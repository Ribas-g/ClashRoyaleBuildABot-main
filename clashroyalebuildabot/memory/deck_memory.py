"""
Sistema de memória de deck para rastrear cartas próprias e inimigas
"""
import json
import time
from typing import Dict, List, Optional
from loguru import logger


class DeckMemory:
    def __init__(self):
        # Nosso deck (conhecido)
        self.our_deck = [
            'archers', 'knight', 'minipekka', 'musketeer', 
            'minions', 'fireball', 'spear_goblins', 'giant'
        ]
        
        # Ciclo do nosso deck
        self.our_cycle_position = 0
        self.our_cards_played = []
        
        # Deck inimigo (descoberto durante o jogo)
        self.enemy_deck = []
        self.enemy_cards_seen = set()
        self.enemy_cards_played = []
        self.enemy_cycle_position = 0
        
        # Histórico de jogadas
        self.game_history = []
        
        # Timestamp do último reset
        self.last_reset = time.time()
        
    def reset_for_new_game(self):
        """Reseta a memória para um novo jogo"""
        self.our_cycle_position = 0
        self.our_cards_played = []
        self.enemy_deck = []
        self.enemy_cards_seen = set()
        self.enemy_cards_played = []
        self.enemy_cycle_position = 0
        self.game_history = []
        self.last_reset = time.time()
        logger.info("Deck memory reset for new game")
    
    def record_our_card_played(self, card_name: str):
        """Registra que jogamos uma carta"""
        if card_name in self.our_deck:
            self.our_cards_played.append({
                'card': card_name,
                'timestamp': time.time(),
                'cycle_position': self.our_cycle_position
            })
            
            self.our_cycle_position = (self.our_cycle_position + 1) % 8
            logger.debug(f"Our card played: {card_name}, cycle position: {self.our_cycle_position}")
    
    def record_enemy_card_seen(self, card_name: str):
        """Registra que vimos uma carta inimiga"""
        if card_name and card_name != 'unknown' and card_name != 'blank':
            self.enemy_cards_seen.add(card_name)
            
            # Adiciona ao deck inimigo se ainda não está lá
            if card_name not in self.enemy_deck and len(self.enemy_deck) < 8:
                self.enemy_deck.append(card_name)
                logger.info(f"Enemy card discovered: {card_name} ({len(self.enemy_deck)}/8)")
            
            # Registra a jogada
            self.enemy_cards_played.append({
                'card': card_name,
                'timestamp': time.time(),
                'cycle_position': self.enemy_cycle_position
            })
            
            if len(self.enemy_deck) == 8:
                self.enemy_cycle_position = (self.enemy_cycle_position + 1) % 8
    
    def predict_our_next_cards(self, count: int = 4) -> List[str]:
        """Prediz nossas próximas cartas baseado no ciclo"""
        if not self.our_cards_played:
            return self.our_deck[:count]
        
        next_cards = []
        current_pos = self.our_cycle_position
        
        for i in range(count):
            card_index = (current_pos + i) % 8
            next_cards.append(self.our_deck[card_index])
        
        return next_cards
    
    def predict_enemy_next_cards(self, count: int = 4) -> List[Dict]:
        """Prediz próximas cartas inimigas baseado no ciclo conhecido"""
        if len(self.enemy_deck) < 8:
            # Se não conhecemos o deck completo, usa probabilidades
            return self._predict_unknown_enemy_cards(count)
        
        next_cards = []
        current_pos = self.enemy_cycle_position
        
        for i in range(count):
            card_index = (current_pos + i) % 8
            card = self.enemy_deck[card_index]
            next_cards.append({
                'card': card,
                'probability': 0.9,  # Alta probabilidade se conhecemos o ciclo
                'position_in_cycle': card_index
            })
        
        return next_cards
    
    def _predict_unknown_enemy_cards(self, count: int) -> List[Dict]:
        """Prediz cartas quando não conhecemos o deck completo"""
        predictions = []
        
        # Cartas comuns no meta
        common_cards = [
            'giant', 'musketeer', 'fireball', 'zap', 'knight', 'archers',
            'minions', 'skeleton_army', 'wizard', 'baby_dragon'
        ]
        
        # Remove cartas já vistas
        unseen_common = [card for card in common_cards if card not in self.enemy_cards_seen]
        
        for i, card in enumerate(unseen_common[:count]):
            predictions.append({
                'card': card,
                'probability': max(0.3 - i * 0.05, 0.1),  # Probabilidade decrescente
                'position_in_cycle': 'unknown'
            })
        
        return predictions
    
    def get_deck_analysis(self) -> Dict:
        """Análise completa dos decks"""
        return {
            'our_deck': {
                'cards': self.our_deck,
                'current_cycle_position': self.our_cycle_position,
                'next_cards': self.predict_our_next_cards(4),
                'cards_played_count': len(self.our_cards_played)
            },
            'enemy_deck': {
                'known_cards': list(self.enemy_cards_seen),
                'full_deck': self.enemy_deck if len(self.enemy_deck) == 8 else None,
                'cards_discovered': f"{len(self.enemy_deck)}/8",
                'predicted_next': self.predict_enemy_next_cards(4),
                'cycle_position': self.enemy_cycle_position if len(self.enemy_deck) == 8 else 'unknown'
            },
            'strategic_insights': self._generate_strategic_insights()
        }
    
    def _generate_strategic_insights(self) -> Dict:
        """Gera insights estratégicos baseados na memória"""
        insights = {
            'our_advantages': [],
            'enemy_threats': [],
            'recommended_actions': []
        }
        
        # Analisa vantagens do nosso deck
        our_next = self.predict_our_next_cards(2)
        if 'fireball' in our_next:
            insights['our_advantages'].append('Fireball available for area damage')
        if 'giant' in our_next:
            insights['our_advantages'].append('Giant ready for big push')
        if 'spear_goblins' in our_next:
            insights['our_advantages'].append('Cycle card available')
        
        # Analisa ameaças inimigas
        enemy_next = self.predict_enemy_next_cards(3)
        for prediction in enemy_next:
            card = prediction['card']
            prob = prediction['probability']
            
            if prob > 0.7:  # Alta probabilidade
                if card in ['giant', 'pekka', 'golem']:
                    insights['enemy_threats'].append(f'Enemy {card} likely next - prepare defense')
                elif card in ['fireball', 'rocket']:
                    insights['enemy_threats'].append(f'Enemy {card} expected - avoid grouping')
        
        # Recomendações
        if len(self.enemy_deck) < 8:
            insights['recommended_actions'].append('Continue scouting enemy deck')
        else:
            insights['recommended_actions'].append('Full enemy deck known - exploit cycle')
        
        return insights
    
    def should_expect_card(self, card_name: str, within_cards: int = 2) -> float:
        """Calcula probabilidade de uma carta específica aparecer em breve"""
        if card_name in self.our_deck:
            our_next = self.predict_our_next_cards(within_cards)
            return 1.0 if card_name in our_next else 0.0
        
        # Para cartas inimigas
        enemy_predictions = self.predict_enemy_next_cards(within_cards)
        for pred in enemy_predictions:
            if pred['card'] == card_name:
                return pred['probability']
        
        return 0.0

"""
Sistema de análise de deck do oponente com memória e previsão
"""

import json
import os
from datetime import datetime
from collections import defaultdict, Counter
from loguru import logger
import numpy as np


class DeckAnalyzer:
    def __init__(self, save_path="deck_memory.json"):
        self.save_path = save_path
        self.current_game = None
        try:
            self.deck_memory = self.load_memory()
            logger.debug("Deck memory loaded successfully")
        except Exception as e:
            logger.error(f"Error loading deck memory: {e}")
            # Usar memória vazia como fallback
            self.deck_memory = {
                'games': [],
                'deck_patterns': {},
                'card_frequencies': {},
                'cycle_analysis': {}
            }
        
        # Cartas conhecidas do Clash Royale
        self.all_cards = {
            # Tropas
            'archers', 'baby_dragon', 'bats', 'giant', 'goblin_barrel', 
            'knight', 'minions', 'minipekka', 'musketeer', 'witch',
            # Feitiços
            'arrows', 'fireball', 'zap',
            # Construções
            'cannon'
        }
        
        # Decks populares conhecidos
        self.known_decks = {
            'giant_beatdown': ['giant', 'musketeer', 'witch', 'baby_dragon', 'knight', 'archers', 'fireball', 'zap'],
            'control': ['archers', 'musketeer', 'giant', 'witch', 'baby_dragon', 'knight', 'fireball', 'zap'],
            'cycle': ['archers', 'knight', 'musketeer', 'minipekka', 'bats', 'goblin_barrel', 'zap', 'arrows'],
            'defensive': ['knight', 'archers', 'musketeer', 'cannon', 'fireball', 'zap', 'minions', 'witch']
        }
    
    def load_memory(self):
        """Carrega memória de decks anteriores"""
        try:
            if os.path.exists(self.save_path):
                with open(self.save_path, 'r') as f:
                    memory = json.load(f)
                logger.info(f"Loaded deck memory with {len(memory.get('games', []))} games")
                return memory
        except Exception as e:
            logger.warning(f"Could not load deck memory: {e}")
        
        return {
            'games': [],
            'deck_patterns': {},
            'card_frequencies': {},
            'cycle_analysis': {}
        }
    
    def save_memory(self):
        """Salva memória de decks"""
        try:
            with open(self.save_path, 'w') as f:
                json.dump(self.deck_memory, f, indent=2)
            logger.debug("Deck memory saved")
        except Exception as e:
            logger.error(f"Failed to save deck memory: {e}")
    
    def start_new_game(self):
        """Inicia análise de um novo jogo"""
        self.current_game = {
            'timestamp': datetime.now().isoformat(),
            'enemy_cards_played': [],
            'card_order': [],
            'cycle_positions': {},
            'deck_prediction': None,
            'weaknesses_identified': [],
            'strategy_suggestions': []
        }
        logger.info("Started new deck analysis")
    
    def record_enemy_card(self, card_name, game_state):
        """Registra uma carta jogada pelo inimigo"""
        if not self.current_game:
            return
        
        # Adiciona à lista de cartas jogadas
        self.current_game['enemy_cards_played'].append({
            'card': card_name,
            'timestamp': datetime.now().isoformat(),
            'elixir': game_state.numbers.elixir.number,
            'position': len(self.current_game['enemy_cards_played']) + 1
        })
        
        # Atualiza ordem das cartas
        if card_name not in self.current_game['card_order']:
            self.current_game['card_order'].append(card_name)
        
        # Analisa o deck atual
        self.analyze_current_deck()
        
        logger.debug(f"Recorded enemy card: {card_name}")
    
    def analyze_current_deck(self):
        """Analisa o deck atual do oponente"""
        if not self.current_game or len(self.current_game['enemy_cards_played']) < 2:
            return
        
        played_cards = set(self.current_game['card_order'])
        
        # 1. Prediz deck baseado nas cartas jogadas
        deck_prediction = self.predict_deck(played_cards)
        self.current_game['deck_prediction'] = deck_prediction
        
        # 2. Analisa ciclo das cartas
        cycle_analysis = self.analyze_card_cycle()
        self.current_game['cycle_positions'] = cycle_analysis
        
        # 3. Identifica fraquezas
        weaknesses = self.identify_deck_weaknesses(played_cards, deck_prediction)
        self.current_game['weaknesses_identified'] = weaknesses
        
        # 4. Sugere estratégias
        strategies = self.suggest_strategies(played_cards, deck_prediction, weaknesses)
        self.current_game['strategy_suggestions'] = strategies
        
        logger.info(f"Deck analysis: {len(played_cards)} cards, predicted: {deck_prediction['name']}")
    
    def predict_deck(self, played_cards):
        """Prediz o deck do oponente baseado nas cartas jogadas"""
        best_match = None
        best_score = 0
        
        for deck_name, deck_cards in self.known_decks.items():
            # Calcula similaridade com deck conhecido
            deck_set = set(deck_cards)
            intersection = played_cards.intersection(deck_set)
            
            if len(intersection) > 0:
                # Score baseado na porcentagem de cartas conhecidas
                score = len(intersection) / len(deck_cards)
                
                # Bônus para cartas únicas do deck
                unique_cards = deck_set - played_cards
                if len(unique_cards) <= 3:  # Poucas cartas restantes
                    score += 0.2
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        'name': deck_name,
                        'cards': deck_cards,
                        'confidence': score,
                        'missing_cards': list(deck_set - played_cards),
                        'played_cards': list(played_cards)
                    }
        
        # Se não encontrou match bom, cria predição baseada em padrões
        if not best_match or best_match['confidence'] < 0.3:
            best_match = self.create_pattern_based_prediction(played_cards)
        
        return best_match
    
    def create_pattern_based_prediction(self, played_cards):
        """Cria predição baseada em padrões de cartas"""
        # Analisa frequência de tipos de cartas
        card_types = {
            'troops': ['archers', 'knight', 'musketeer', 'giant', 'witch', 'baby_dragon', 'minipekka', 'minions', 'bats'],
            'spells': ['fireball', 'zap', 'arrows'],
            'buildings': ['cannon']
        }
        
        type_counts = {}
        for card_type, cards in card_types.items():
            type_counts[card_type] = len(played_cards.intersection(set(cards)))
        
        # Prediz cartas restantes baseado no padrão
        predicted_deck = list(played_cards)
        
        # Adiciona cartas prováveis baseado no padrão
        if type_counts['troops'] < 6:
            # Precisa de mais tropas
            common_troops = ['knight', 'archers', 'musketeer']
            for troop in common_troops:
                if troop not in played_cards and len(predicted_deck) < 8:
                    predicted_deck.append(troop)
        
        if type_counts['spells'] < 2:
            # Precisa de mais feitiços
            common_spells = ['zap', 'fireball']
            for spell in common_spells:
                if spell not in played_cards and len(predicted_deck) < 8:
                    predicted_deck.append(spell)
        
        return {
            'name': 'pattern_based',
            'cards': predicted_deck[:8],
            'confidence': 0.2,
            'missing_cards': predicted_deck[len(played_cards):8],
            'played_cards': list(played_cards)
        }
    
    def analyze_card_cycle(self):
        """Analisa o ciclo das cartas do oponente"""
        if len(self.current_game['enemy_cards_played']) < 4:
            return {}
        
        cycle_analysis = {}
        card_positions = defaultdict(list)
        
        # Mapeia posições de cada carta
        for i, card_data in enumerate(self.current_game['enemy_cards_played']):
            card_positions[card_data['card']].append(i)
        
        # Analisa padrões de ciclo
        for card, positions in card_positions.items():
            if len(positions) > 1:
                # Calcula intervalo médio entre jogadas da carta
                intervals = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
                avg_interval = np.mean(intervals) if intervals else 0
                
                cycle_analysis[card] = {
                    'positions': positions,
                    'avg_interval': avg_interval,
                    'last_played': positions[-1],
                    'next_expected': positions[-1] + avg_interval if avg_interval > 0 else None
                }
        
        return cycle_analysis
    
    def identify_deck_weaknesses(self, played_cards, deck_prediction):
        """Identifica fraquezas do deck do oponente"""
        weaknesses = []
        
        # Analisa tipos de cartas
        card_types = {
            'air_troops': ['baby_dragon', 'minions', 'bats'],
            'ground_troops': ['knight', 'giant', 'minipekka'],
            'ranged_troops': ['archers', 'musketeer', 'witch'],
            'spells': ['fireball', 'zap', 'arrows'],
            'buildings': ['cannon']
        }
        
        # Verifica fraquezas por tipo
        for weakness_type, cards in card_types.items():
            if not played_cards.intersection(set(cards)):
                weaknesses.append(f"no_{weakness_type}")
        
        # Fraquezas específicas
        if 'giant' in played_cards and not any(card in played_cards for card in ['fireball', 'zap']):
            weaknesses.append("giant_no_spells")
        
        if len([card for card in played_cards if card in card_types['spells']]) < 1:
            weaknesses.append("few_spells")
        
        if len([card for card in played_cards if card in card_types['air_troops']]) < 1:
            weaknesses.append("weak_air_defense")
        
        return weaknesses
    
    def suggest_strategies(self, played_cards, deck_prediction, weaknesses):
        """Sugere estratégias baseadas na análise do deck"""
        strategies = []
        
        # Estratégias baseadas em fraquezas
        if "no_air_troops" in weaknesses:
            strategies.append("use_air_units")
        
        if "giant_no_spells" in weaknesses:
            strategies.append("counter_giant_with_swarm")
        
        if "few_spells" in weaknesses:
            strategies.append("use_swarm_units")
        
        if "weak_air_defense" in weaknesses:
            strategies.append("focus_air_attack")
        
        # Estratégias baseadas no tipo de deck
        if deck_prediction and deck_prediction['name'] == 'giant_beatdown':
            strategies.extend(["defend_early", "counter_push"])
        
        if deck_prediction and deck_prediction['name'] == 'cycle':
            strategies.extend(["control_elixir", "defend_efficiently"])
        
        # Estratégias baseadas no ciclo
        cycle_analysis = self.current_game.get('cycle_positions', {})
        if cycle_analysis:
            # Identifica cartas que podem estar próximas de voltar
            for card, data in cycle_analysis.items():
                if data.get('next_expected') and data['next_expected'] <= len(self.current_game['enemy_cards_played']) + 2:
                    strategies.append(f"prepare_for_{card}")
        
        return strategies
    
    def get_next_expected_cards(self):
        """Retorna cartas esperadas do oponente baseado no ciclo"""
        if not self.current_game or not self.current_game.get('cycle_positions'):
            return []
        
        expected_cards = []
        current_position = len(self.current_game['enemy_cards_played'])
        
        for card, data in self.current_game['cycle_positions'].items():
            if data.get('next_expected') and data['next_expected'] <= current_position + 2:
                expected_cards.append({
                    'card': card,
                    'probability': 0.8 if data['next_expected'] <= current_position + 1 else 0.6
                })
        
        return expected_cards
    
    def get_counter_suggestions(self, enemy_card):
        """Sugere contras para uma carta específica"""
        counters = {
            'giant': ['minipekka', 'knight', 'archers'],
            'musketeer': ['fireball', 'knight'],
            'witch': ['fireball', 'knight'],
            'baby_dragon': ['musketeer', 'archers'],
            'knight': ['archers', 'minipekka'],
            'archers': ['fireball', 'zap'],
            'minipekka': ['knight', 'archers'],
            'minions': ['zap', 'archers'],
            'bats': ['zap', 'archers'],
            'goblin_barrel': ['zap', 'fireball'],
            'cannon': ['giant', 'knight'],
            'fireball': ['avoid_swarm'],
            'zap': ['avoid_swarm'],
            'arrows': ['avoid_swarm']
        }
        
        return counters.get(enemy_card, [])
    
    def end_game(self, result):
        """Finaliza análise do jogo e salva na memória"""
        if self.current_game:
            self.current_game['result'] = result
            self.current_game['final_analysis'] = {
                'total_cards_played': len(self.current_game['enemy_cards_played']),
                'deck_accuracy': self.current_game['deck_prediction']['confidence'] if self.current_game['deck_prediction'] else 0,
                'weaknesses_found': len(self.current_game['weaknesses_identified']),
                'strategies_suggested': len(self.current_game['strategy_suggestions'])
            }
            
            # Adiciona à memória
            self.deck_memory['games'].append(self.current_game)
            
            # Atualiza estatísticas
            self.update_statistics()
            
            # Salva memória
            self.save_memory()
            
            logger.info(f"Deck analysis completed. Cards played: {len(self.current_game['enemy_cards_played'])}")
            
            self.current_game = None
    
    def update_statistics(self):
        """Atualiza estatísticas baseadas nos jogos analisados"""
        # Atualiza frequência de cartas
        card_freq = Counter()
        for game in self.deck_memory['games']:
            for card_data in game['enemy_cards_played']:
                card_freq[card_data['card']] += 1
        
        self.deck_memory['card_frequencies'] = dict(card_freq)
        
        # Atualiza padrões de deck
        deck_patterns = defaultdict(int)
        for game in self.deck_memory['games']:
            if game.get('deck_prediction'):
                deck_patterns[game['deck_prediction']['name']] += 1
        
        self.deck_memory['deck_patterns'] = dict(deck_patterns)
    
    def get_analysis_summary(self):
        """Retorna resumo da análise atual"""
        if not self.current_game:
            return None
        
        return {
            'cards_played': len(self.current_game['enemy_cards_played']),
            'deck_prediction': self.current_game['deck_prediction'],
            'weaknesses': self.current_game['weaknesses_identified'],
            'strategies': self.current_game['strategy_suggestions'],
            'next_expected': self.get_next_expected_cards()
        }

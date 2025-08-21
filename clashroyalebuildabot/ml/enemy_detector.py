"""
Sistema para detectar cartas jogadas pelo inimigo
"""

import time
from loguru import logger
from clashroyalebuildabot.ml.deck_analyzer import DeckAnalyzer


class EnemyDetector:
    def __init__(self, deck_analyzer):
        self.deck_analyzer = deck_analyzer
        self.last_enemy_cards = set()
        self.last_detection_time = 0
        self.detection_cooldown = 2.0  # Segundos entre detecções
        
        # Mapeamento de unidades para cartas
        self.unit_to_card = {
            'archers': 'archers',
            'baby_dragon': 'baby_dragon',
            'bats': 'bats',
            'giant': 'giant',
            'knight': 'knight',
            'minions': 'minions',
            'minipekka': 'minipekka',
            'musketeer': 'musketeer',
            'witch': 'witch'
        }
    
    def detect_enemy_cards(self, game_state):
        """Detecta cartas jogadas pelo inimigo"""
        current_time = time.time()
        
        # Evita detecções muito frequentes
        if current_time - self.last_detection_time < self.detection_cooldown:
            return
        
        self.last_detection_time = current_time
        
        # Obtém unidades inimigas atuais
        current_enemy_units = set()
        for enemy in game_state.enemies:
            unit_name = enemy.unit.name
            if unit_name in self.unit_to_card:
                current_enemy_units.add(self.unit_to_card[unit_name])
        
        # Detecta novas cartas jogadas
        new_cards = current_enemy_units - self.last_enemy_cards
        
        # Registra novas cartas no analisador
        for card in new_cards:
            self.deck_analyzer.record_enemy_card(card, game_state)
            logger.info(f"Enemy played: {card}")
        
        # Atualiza estado anterior
        self.last_enemy_cards = current_enemy_units.copy()
    
    def get_enemy_analysis(self):
        """Retorna análise atual do inimigo"""
        return self.deck_analyzer.get_analysis_summary()
    
    def get_counter_suggestions(self, enemy_card):
        """Retorna sugestões de contra para uma carta inimiga"""
        return self.deck_analyzer.get_counter_suggestions(enemy_card)
    
    def get_next_expected_cards(self):
        """Retorna cartas esperadas do inimigo"""
        return self.deck_analyzer.get_next_expected_cards()

"""
Sistema de Análise de Padrões e Adaptação
Analisa padrões do oponente e adapta estratégias
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from loguru import logger
import json
import time
from collections import defaultdict, deque


class PatternAnalyzer:
    """Sistema de análise de padrões do oponente"""
    
    def __init__(self):
        # Armazenamento de padrões
        self.opponent_patterns = {}
        self.game_history = deque(maxlen=100)  # Últimas 100 partidas
        self.current_game_actions = []
        
        # Configurações de análise
        self.pattern_window = 10  # Janela para análise de padrões
        self.confidence_threshold = 0.7  # Limiar de confiança
        self.adaptation_threshold = 0.8  # Limiar para adaptação
        
        # Tipos de padrões
        self.pattern_types = {
            'opening': 'Primeiras jogadas do oponente',
            'defensive': 'Padrões defensivos',
            'aggressive': 'Padrões agressivos',
            'cycling': 'Padrões de cycling',
            'spell_usage': 'Uso de magias',
            'counter_play': 'Contra-jogadas',
            'elixir_management': 'Gerenciamento de elixir'
        }
    
    def record_opponent_action(self, action: Dict, game_state: Dict):
        """Registra uma ação do oponente"""
        try:
            action_record = {
                'timestamp': time.time(),
                'action': action,
                'game_state': game_state,
                'game_phase': self._determine_game_phase(game_state),
                'elixir_cost': action.get('elixir_cost', 0),
                'card_name': action.get('card_name', 'unknown'),
                'position': (action.get('tile_x', 0), action.get('tile_y', 0))
            }
            
            self.current_game_actions.append(action_record)
            
            # Analisar padrões em tempo real
            self._analyze_realtime_patterns()
            
        except Exception as e:
            logger.error(f"Error recording opponent action: {e}")
    
    def _determine_game_phase(self, game_state: Dict) -> str:
        """Determina a fase atual do jogo"""
        try:
            game_time = game_state.get('game_time', 0)
            ally_towers = game_state.get('ally_tower_health', [1.0, 1.0])
            enemy_towers = game_state.get('enemy_tower_health', [1.0, 1.0])
            
            # Calcular dano total
            total_damage = (1.0 - ally_towers[0]) + (1.0 - ally_towers[1]) + \
                          (1.0 - enemy_towers[0]) + (1.0 - enemy_towers[1])
            
            if game_time < 30:
                return 'opening'
            elif total_damage < 0.3:
                return 'early_game'
            elif total_damage < 0.7:
                return 'mid_game'
            else:
                return 'late_game'
                
        except Exception as e:
            logger.error(f"Error determining game phase: {e}")
            return 'mid_game'
    
    def _analyze_realtime_patterns(self):
        """Analisa padrões em tempo real"""
        try:
            if len(self.current_game_actions) < 3:
                return
            
            # Analisar padrões de opening
            opening_pattern = self._analyze_opening_pattern()
            if opening_pattern:
                self._update_pattern('opening', opening_pattern)
            
            # Analisar padrões defensivos
            defensive_pattern = self._analyze_defensive_pattern()
            if defensive_pattern:
                self._update_pattern('defensive', defensive_pattern)
            
            # Analisar padrões agressivos
            aggressive_pattern = self._analyze_aggressive_pattern()
            if aggressive_pattern:
                self._update_pattern('aggressive', aggressive_pattern)
            
            # Analisar uso de magias
            spell_pattern = self._analyze_spell_usage()
            if spell_pattern:
                self._update_pattern('spell_usage', spell_pattern)
            
        except Exception as e:
            logger.error(f"Error in realtime pattern analysis: {e}")
    
    def _analyze_opening_pattern(self) -> Optional[Dict]:
        """Analisa padrão de opening do oponente"""
        try:
            opening_actions = [a for a in self.current_game_actions 
                             if a['game_phase'] == 'opening']
            
            if len(opening_actions) < 2:
                return None
            
            # Analisar primeiras jogadas
            first_cards = [a['card_name'] for a in opening_actions[:3]]
            first_positions = [a['position'] for a in opening_actions[:3]]
            
            # Determinar tipo de opening
            opening_type = self._classify_opening(first_cards, first_positions)
            
            return {
                'type': opening_type,
                'first_cards': first_cards,
                'first_positions': first_positions,
                'confidence': self._calculate_pattern_confidence(opening_actions),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing opening pattern: {e}")
            return None
    
    def _classify_opening(self, cards: List[str], positions: List[Tuple]) -> str:
        """Classifica o tipo de opening"""
        try:
            # Verificar se é opening agressivo
            aggressive_cards = ['giant', 'golem', 'pekka', 'hog_rider']
            if any(card in aggressive_cards for card in cards):
                return 'aggressive'
            
            # Verificar se é opening defensivo
            defensive_cards = ['cannon', 'tesla', 'bomb_tower', 'inferno_tower']
            if any(card in defensive_cards for card in cards):
                return 'defensive'
            
            # Verificar se é opening de cycling
            cycling_cards = ['skeletons', 'goblins', 'spear_goblins', 'ice_spirit']
            if any(card in cycling_cards for card in cards):
                return 'cycling'
            
            # Verificar posições
            bridge_positions = [(9, 7), (9, 8), (8, 7), (8, 8)]
            if any(pos in bridge_positions for pos in positions):
                return 'bridge_rush'
            
            return 'standard'
            
        except Exception as e:
            logger.error(f"Error classifying opening: {e}")
            return 'unknown'
    
    def _analyze_defensive_pattern(self) -> Optional[Dict]:
        """Analisa padrões defensivos"""
        try:
            recent_actions = self.current_game_actions[-self.pattern_window:]
            
            # Identificar ações defensivas
            defensive_actions = []
            for action in recent_actions:
                if self._is_defensive_action(action):
                    defensive_actions.append(action)
            
            if len(defensive_actions) < 2:
                return None
            
            # Analisar padrões defensivos
            defensive_cards = [a['card_name'] for a in defensive_actions]
            defensive_positions = [a['position'] for a in defensive_actions]
            
            # Determinar estratégia defensiva
            defensive_strategy = self._classify_defensive_strategy(defensive_cards, defensive_positions)
            
            return {
                'strategy': defensive_strategy,
                'cards_used': defensive_cards,
                'positions': defensive_positions,
                'frequency': len(defensive_actions) / len(recent_actions),
                'confidence': self._calculate_pattern_confidence(defensive_actions),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing defensive pattern: {e}")
            return None
    
    def _is_defensive_action(self, action: Dict) -> bool:
        """Verifica se uma ação é defensiva"""
        try:
            card_name = action['card_name']
            position = action['position']
            
            # Cartas defensivas
            defensive_cards = ['cannon', 'tesla', 'bomb_tower', 'inferno_tower', 
                             'knight', 'valkyrie', 'mini_pekka']
            
            # Posições defensivas (lado aliado)
            defensive_positions = position[1] < 7  # Lado aliado do campo
            
            return card_name in defensive_cards or defensive_positions
            
        except Exception as e:
            logger.error(f"Error checking defensive action: {e}")
            return False
    
    def _classify_defensive_strategy(self, cards: List[str], positions: List[Tuple]) -> str:
        """Classifica estratégia defensiva"""
        try:
            # Verificar se usa construções
            building_cards = ['cannon', 'tesla', 'bomb_tower', 'inferno_tower']
            if any(card in building_cards for card in cards):
                return 'building_defense'
            
            # Verificar se usa tropas
            troop_cards = ['knight', 'valkyrie', 'mini_pekka', 'musketeer']
            if any(card in troop_cards for card in cards):
                return 'troop_defense'
            
            # Verificar se usa magias
            spell_cards = ['fireball', 'zap', 'arrows', 'poison']
            if any(card in spell_cards for card in cards):
                return 'spell_defense'
            
            return 'mixed_defense'
            
        except Exception as e:
            logger.error(f"Error classifying defensive strategy: {e}")
            return 'unknown'
    
    def _analyze_aggressive_pattern(self) -> Optional[Dict]:
        """Analisa padrões agressivos"""
        try:
            recent_actions = self.current_game_actions[-self.pattern_window:]
            
            # Identificar ações agressivas
            aggressive_actions = []
            for action in recent_actions:
                if self._is_aggressive_action(action):
                    aggressive_actions.append(action)
            
            if len(aggressive_actions) < 2:
                return None
            
            # Analisar padrões agressivos
            aggressive_cards = [a['card_name'] for a in aggressive_actions]
            aggressive_positions = [a['position'] for a in aggressive_actions]
            
            # Determinar estratégia agressiva
            aggressive_strategy = self._classify_aggressive_strategy(aggressive_cards, aggressive_positions)
            
            return {
                'strategy': aggressive_strategy,
                'cards_used': aggressive_cards,
                'positions': aggressive_positions,
                'frequency': len(aggressive_actions) / len(recent_actions),
                'confidence': self._calculate_pattern_confidence(aggressive_actions),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing aggressive pattern: {e}")
            return None
    
    def _is_aggressive_action(self, action: Dict) -> bool:
        """Verifica se uma ação é agressiva"""
        try:
            card_name = action['card_name']
            position = action['position']
            
            # Cartas agressivas
            aggressive_cards = ['giant', 'golem', 'pekka', 'hog_rider', 'balloon']
            
            # Posições agressivas (lado inimigo)
            aggressive_positions = position[1] > 7  # Lado inimigo do campo
            
            return card_name in aggressive_cards or aggressive_positions
            
        except Exception as e:
            logger.error(f"Error checking aggressive action: {e}")
            return False
    
    def _classify_aggressive_strategy(self, cards: List[str], positions: List[Tuple]) -> str:
        """Classifica estratégia agressiva"""
        try:
            # Verificar se usa tanks
            tank_cards = ['giant', 'golem', 'pekka']
            if any(card in tank_cards for card in cards):
                return 'tank_push'
            
            # Verificar se usa bridge rush
            bridge_rush_cards = ['hog_rider', 'balloon', 'battle_ram']
            if any(card in bridge_rush_cards for card in cards):
                return 'bridge_rush'
            
            # Verificar se usa swarm
            swarm_cards = ['minions', 'skeletons', 'goblins']
            if any(card in swarm_cards for card in cards):
                return 'swarm_attack'
            
            return 'mixed_aggressive'
            
        except Exception as e:
            logger.error(f"Error classifying aggressive strategy: {e}")
            return 'unknown'
    
    def _analyze_spell_usage(self) -> Optional[Dict]:
        """Analisa padrões de uso de magias"""
        try:
            recent_actions = self.current_game_actions[-self.pattern_window:]
            
            # Identificar uso de magias
            spell_actions = [a for a in recent_actions 
                           if a['card_name'] in ['fireball', 'zap', 'arrows', 'poison']]
            
            if len(spell_actions) < 1:
                return None
            
            # Analisar padrões de magias
            spell_types = [a['card_name'] for a in spell_actions]
            spell_positions = [a['position'] for a in spell_actions]
            
            # Determinar estratégia de magias
            spell_strategy = self._classify_spell_strategy(spell_types, spell_positions)
            
            return {
                'strategy': spell_strategy,
                'spells_used': spell_types,
                'positions': spell_positions,
                'frequency': len(spell_actions) / len(recent_actions),
                'confidence': self._calculate_pattern_confidence(spell_actions),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing spell usage: {e}")
            return None
    
    def _classify_spell_strategy(self, spells: List[str], positions: List[Tuple]) -> str:
        """Classifica estratégia de magias"""
        try:
            # Verificar se usa magias de dano
            damage_spells = ['fireball', 'poison']
            if any(spell in damage_spells for spell in spells):
                return 'damage_spells'
            
            # Verificar se usa magias de controle
            control_spells = ['zap', 'arrows']
            if any(spell in control_spells for spell in spells):
                return 'control_spells'
            
            # Verificar se usa magias defensivas
            defensive_positions = [pos for pos in positions if pos[1] < 7]
            if len(defensive_positions) > len(positions) / 2:
                return 'defensive_spells'
            
            return 'mixed_spells'
            
        except Exception as e:
            logger.error(f"Error classifying spell strategy: {e}")
            return 'unknown'
    
    def _calculate_pattern_confidence(self, actions: List[Dict]) -> float:
        """Calcula confiança de um padrão"""
        try:
            if len(actions) < 2:
                return 0.0
            
            # Calcular consistência do padrão
            card_names = [a['card_name'] for a in actions]
            unique_cards = len(set(card_names))
            total_actions = len(actions)
            
            # Confiança baseada na consistência
            consistency = 1.0 - (unique_cards / total_actions)
            
            # Confiança baseada no número de ações
            frequency_confidence = min(1.0, total_actions / self.pattern_window)
            
            # Confiança combinada
            confidence = (consistency + frequency_confidence) / 2.0
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating pattern confidence: {e}")
            return 0.0
    
    def _update_pattern(self, pattern_type: str, pattern_data: Dict):
        """Atualiza padrão identificado"""
        try:
            if pattern_type not in self.opponent_patterns:
                self.opponent_patterns[pattern_type] = []
            
            # Adicionar novo padrão
            self.opponent_patterns[pattern_type].append(pattern_data)
            
            # Manter apenas os padrões mais recentes
            if len(self.opponent_patterns[pattern_type]) > 10:
                self.opponent_patterns[pattern_type] = self.opponent_patterns[pattern_type][-10:]
            
            logger.debug(f"Updated {pattern_type} pattern: {pattern_data}")
            
        except Exception as e:
            logger.error(f"Error updating pattern: {e}")
    
    def get_opponent_profile(self) -> Dict:
        """Retorna perfil do oponente baseado nos padrões"""
        try:
            profile = {
                'playstyle': self._determine_playstyle(),
                'preferred_strategies': self._get_preferred_strategies(),
                'weaknesses': self._identify_weaknesses(),
                'adaptation_recommendations': self._get_adaptation_recommendations(),
                'confidence': self._calculate_profile_confidence(),
                'patterns_identified': len(self.opponent_patterns)
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting opponent profile: {e}")
            return {'playstyle': 'unknown', 'confidence': 0.0}
    
    def _determine_playstyle(self) -> str:
        """Determina o estilo de jogo do oponente"""
        try:
            if not self.opponent_patterns:
                return 'unknown'
            
            # Analisar padrões para determinar estilo
            aggressive_score = 0
            defensive_score = 0
            cycling_score = 0
            
            if 'aggressive' in self.opponent_patterns:
                aggressive_score = len(self.opponent_patterns['aggressive'])
            
            if 'defensive' in self.opponent_patterns:
                defensive_score = len(self.opponent_patterns['defensive'])
            
            if 'opening' in self.opponent_patterns:
                opening_patterns = self.opponent_patterns['opening']
                cycling_openings = [p for p in opening_patterns if p.get('type') == 'cycling']
                cycling_score = len(cycling_openings)
            
            # Determinar estilo dominante
            max_score = max(aggressive_score, defensive_score, cycling_score)
            
            if max_score == aggressive_score:
                return 'aggressive'
            elif max_score == defensive_score:
                return 'defensive'
            elif max_score == cycling_score:
                return 'cycling'
            else:
                return 'balanced'
                
        except Exception as e:
            logger.error(f"Error determining playstyle: {e}")
            return 'unknown'
    
    def _get_preferred_strategies(self) -> List[str]:
        """Retorna estratégias preferidas do oponente"""
        try:
            strategies = []
            
            for pattern_type, patterns in self.opponent_patterns.items():
                if patterns:
                    # Pegar estratégia mais recente
                    latest_pattern = patterns[-1]
                    strategy = latest_pattern.get('strategy', latest_pattern.get('type', 'unknown'))
                    confidence = latest_pattern.get('confidence', 0.0)
                    
                    if confidence > self.confidence_threshold:
                        strategies.append(f"{pattern_type}: {strategy}")
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error getting preferred strategies: {e}")
            return []
    
    def _identify_weaknesses(self) -> List[str]:
        """Identifica fraquezas do oponente"""
        try:
            weaknesses = []
            
            # Analisar padrões para identificar fraquezas
            if 'defensive' in self.opponent_patterns:
                defensive_patterns = self.opponent_patterns['defensive']
                if defensive_patterns:
                    latest_defensive = defensive_patterns[-1]
                    strategy = latest_defensive.get('strategy', 'unknown')
                    
                    if strategy == 'building_defense':
                        weaknesses.append('Vulnerável a magias anti-construção')
                    elif strategy == 'troop_defense':
                        weaknesses.append('Vulnerável a pushes pesados')
            
            if 'aggressive' in self.opponent_patterns:
                aggressive_patterns = self.opponent_patterns['aggressive']
                if aggressive_patterns:
                    latest_aggressive = aggressive_patterns[-1]
                    strategy = latest_aggressive.get('strategy', 'unknown')
                    
                    if strategy == 'tank_push':
                        weaknesses.append('Vulnerável a contra-ataques rápidos')
                    elif strategy == 'bridge_rush':
                        weaknesses.append('Vulnerável a defesas sólidas')
            
            return weaknesses
            
        except Exception as e:
            logger.error(f"Error identifying weaknesses: {e}")
            return []
    
    def _get_adaptation_recommendations(self) -> List[str]:
        """Retorna recomendações de adaptação"""
        try:
            recommendations = []
            playstyle = self._determine_playstyle()
            
            if playstyle == 'aggressive':
                recommendations.extend([
                    'Focar em defesas sólidas',
                    'Usar contra-ataques eficientes',
                    'Manter vantagem de elixir'
                ])
            elif playstyle == 'defensive':
                recommendations.extend([
                    'Aplicar pressão constante',
                    'Usar pushes coordenados',
                    'Explorar fraquezas defensivas'
                ])
            elif playstyle == 'cycling':
                recommendations.extend([
                    'Interromper ciclo do oponente',
                    'Usar magias estrategicamente',
                    'Manter pressão no campo'
                ])
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting adaptation recommendations: {e}")
            return []
    
    def _calculate_profile_confidence(self) -> float:
        """Calcula confiança do perfil do oponente"""
        try:
            if not self.opponent_patterns:
                return 0.0
            
            total_confidence = 0.0
            total_patterns = 0
            
            for patterns in self.opponent_patterns.values():
                for pattern in patterns:
                    confidence = pattern.get('confidence', 0.0)
                    total_confidence += confidence
                    total_patterns += 1
            
            if total_patterns > 0:
                return total_confidence / total_patterns
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating profile confidence: {e}")
            return 0.0
    
    def end_game(self, result: str):
        """Finaliza análise da partida"""
        try:
            # Salvar histórico da partida
            game_record = {
                'timestamp': time.time(),
                'result': result,
                'actions': self.current_game_actions.copy(),
                'patterns': self.opponent_patterns.copy()
            }
            
            self.game_history.append(game_record)
            
            # Limpar dados da partida atual
            self.current_game_actions.clear()
            
            logger.info(f"Game analysis completed. Result: {result}")
            
        except Exception as e:
            logger.error(f"Error ending game analysis: {e}")
    
    def get_analysis_summary(self) -> Dict:
        """Retorna resumo da análise"""
        try:
            return {
                'current_patterns': len(self.opponent_patterns),
                'games_analyzed': len(self.game_history),
                'opponent_profile': self.get_opponent_profile(),
                'pattern_types': list(self.opponent_patterns.keys()),
                'analysis_confidence': self._calculate_profile_confidence()
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis summary: {e}")
            return {'analysis_confidence': 0.0}

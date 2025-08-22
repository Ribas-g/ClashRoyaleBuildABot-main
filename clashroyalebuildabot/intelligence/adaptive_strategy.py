"""
Sistema de Adaptação Dinâmica
Ajusta estratégias baseado no perfil do oponente
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from loguru import logger
import time
from collections import defaultdict


class AdaptiveStrategy:
    """Sistema de adaptação dinâmica de estratégias"""
    
    def __init__(self):
        # Configurações de adaptação
        self.adaptation_threshold = 0.7  # Limiar para adaptação
        self.strategy_memory = defaultdict(list)  # Memória de estratégias
        self.current_strategy = 'balanced'
        self.strategy_confidence = 0.0
        
        # Estratégias disponíveis
        self.strategies = {
            'aggressive': {
                'description': 'Estratégia agressiva - foco em ataques',
                'elixir_threshold': 6.0,
                'push_frequency': 0.8,
                'defense_priority': 0.3,
                'spell_usage': 0.4
            },
            'defensive': {
                'description': 'Estratégia defensiva - foco em defesas',
                'elixir_threshold': 8.0,
                'push_frequency': 0.3,
                'defense_priority': 0.8,
                'spell_usage': 0.6
            },
            'cycling': {
                'description': 'Estratégia de cycling - foco em velocidade',
                'elixir_threshold': 4.0,
                'push_frequency': 0.5,
                'defense_priority': 0.5,
                'spell_usage': 0.7
            },
            'balanced': {
                'description': 'Estratégia equilibrada - adaptável',
                'elixir_threshold': 7.0,
                'push_frequency': 0.6,
                'defense_priority': 0.6,
                'spell_usage': 0.5
            },
            'counter_aggressive': {
                'description': 'Contra-estratégia agressiva',
                'elixir_threshold': 5.0,
                'push_frequency': 0.9,
                'defense_priority': 0.2,
                'spell_usage': 0.3
            },
            'counter_defensive': {
                'description': 'Contra-estratégia defensiva',
                'elixir_threshold': 9.0,
                'push_frequency': 0.2,
                'defense_priority': 0.9,
                'spell_usage': 0.8
            }
        }
        
        # Histórico de adaptações
        self.adaptation_history = []
        
    def analyze_opponent_and_adapt(self, opponent_profile: Dict, game_state: Dict) -> Dict:
        """Analisa o oponente e adapta a estratégia"""
        try:
            # Analisar perfil do oponente
            opponent_playstyle = opponent_profile.get('playstyle', 'unknown')
            opponent_confidence = opponent_profile.get('confidence', 0.0)
            
            # Determinar estratégia de adaptação
            if opponent_confidence > self.adaptation_threshold:
                adapted_strategy = self._determine_counter_strategy(opponent_playstyle)
                adaptation_reason = f"Counter to {opponent_playstyle} playstyle"
            else:
                adapted_strategy = self._determine_situational_strategy(game_state)
                adaptation_reason = "Situational adaptation"
            
            # Aplicar adaptação
            strategy_config = self._apply_strategy_adaptation(adapted_strategy, opponent_profile)
            
            # Registrar adaptação
            self._record_adaptation(adapted_strategy, opponent_playstyle, adaptation_reason)
            
            return {
                'strategy': adapted_strategy,
                'config': strategy_config,
                'reason': adaptation_reason,
                'confidence': opponent_confidence,
                'opponent_playstyle': opponent_playstyle
            }
            
        except Exception as e:
            logger.error(f"Error in opponent analysis and adaptation: {e}")
            return self._get_default_strategy()
    
    def _determine_counter_strategy(self, opponent_playstyle: str) -> str:
        """Determina estratégia de contra-ataque baseada no estilo do oponente"""
        try:
            counter_strategies = {
                'aggressive': 'counter_defensive',
                'defensive': 'counter_aggressive', 
                'cycling': 'aggressive',
                'balanced': 'balanced',
                'unknown': 'balanced'
            }
            
            return counter_strategies.get(opponent_playstyle, 'balanced')
            
        except Exception as e:
            logger.error(f"Error determining counter strategy: {e}")
            return 'balanced'
    
    def _determine_situational_strategy(self, game_state: Dict) -> str:
        """Determina estratégia baseada na situação do jogo"""
        try:
            # Analisar situação atual
            elixir = game_state.get('elixir', 5.0)
            ally_towers = game_state.get('ally_tower_health', [1.0, 1.0])
            enemy_towers = game_state.get('enemy_tower_health', [1.0, 1.0])
            
            # Calcular vantagem/desvantagem
            ally_damage = (1.0 - ally_towers[0]) + (1.0 - ally_towers[1])
            enemy_damage = (1.0 - enemy_towers[0]) + (1.0 - enemy_towers[1])
            
            # Determinar estratégia baseada na situação
            if ally_damage > enemy_damage + 0.3:  # Estamos perdendo
                if elixir > 8.0:
                    return 'aggressive'  # Tentar virar o jogo
                else:
                    return 'defensive'  # Defender e recuperar
            elif enemy_damage > ally_damage + 0.3:  # Estamos ganhando
                if elixir > 6.0:
                    return 'aggressive'  # Manter pressão
                else:
                    return 'defensive'  # Defender vantagem
            else:  # Jogo equilibrado
                if elixir > 7.0:
                    return 'balanced'
                else:
                    return 'cycling'
                    
        except Exception as e:
            logger.error(f"Error determining situational strategy: {e}")
            return 'balanced'
    
    def _apply_strategy_adaptation(self, strategy: str, opponent_profile: Dict) -> Dict:
        """Aplica adaptação da estratégia"""
        try:
            base_config = self.strategies.get(strategy, self.strategies['balanced']).copy()
            
            # Ajustar baseado no perfil do oponente
            weaknesses = opponent_profile.get('weaknesses', [])
            
            # Ajustes específicos baseados em fraquezas
            if 'Vulnerável a magias anti-construção' in weaknesses:
                base_config['spell_usage'] = min(1.0, base_config['spell_usage'] + 0.2)
            
            if 'Vulnerável a pushes pesados' in weaknesses:
                base_config['push_frequency'] = min(1.0, base_config['push_frequency'] + 0.2)
            
            if 'Vulnerável a contra-ataques rápidos' in weaknesses:
                base_config['defense_priority'] = min(1.0, base_config['defense_priority'] + 0.2)
            
            # Ajustes baseados em estratégias preferidas
            preferred_strategies = opponent_profile.get('preferred_strategies', [])
            
            if any('defensive' in strategy for strategy in preferred_strategies):
                base_config['push_frequency'] = min(1.0, base_config['push_frequency'] + 0.1)
            
            if any('aggressive' in strategy for strategy in preferred_strategies):
                base_config['defense_priority'] = min(1.0, base_config['defense_priority'] + 0.1)
            
            return base_config
            
        except Exception as e:
            logger.error(f"Error applying strategy adaptation: {e}")
            return self.strategies['balanced']
    
    def _record_adaptation(self, strategy: str, opponent_playstyle: str, reason: str):
        """Registra adaptação realizada"""
        try:
            adaptation_record = {
                'timestamp': time.time(),
                'strategy': strategy,
                'opponent_playstyle': opponent_playstyle,
                'reason': reason,
                'previous_strategy': self.current_strategy
            }
            
            self.adaptation_history.append(adaptation_record)
            self.current_strategy = strategy
            
            # Manter apenas histórico recente
            if len(self.adaptation_history) > 50:
                self.adaptation_history = self.adaptation_history[-50:]
            
            logger.debug(f"Strategy adapted: {strategy} (reason: {reason})")
            
        except Exception as e:
            logger.error(f"Error recording adaptation: {e}")
    
    def get_strategy_recommendations(self, game_state: Dict, available_cards: List[str]) -> Dict:
        """Retorna recomendações de estratégia para o estado atual"""
        try:
            strategy_config = self.strategies.get(self.current_strategy, self.strategies['balanced'])
            
            recommendations = {
                'strategy': self.current_strategy,
                'elixir_threshold': strategy_config['elixir_threshold'],
                'should_push': self._should_push_now(game_state, strategy_config),
                'should_defend': self._should_defend_now(game_state, strategy_config),
                'spell_priority': self._get_spell_priority(game_state, strategy_config),
                'card_recommendations': self._get_card_recommendations(available_cards, strategy_config),
                'positioning_advice': self._get_positioning_advice(strategy_config)
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting strategy recommendations: {e}")
            return self._get_default_recommendations()
    
    def _should_push_now(self, game_state: Dict, strategy_config: Dict) -> bool:
        """Determina se deve fazer push agora"""
        try:
            elixir = game_state.get('elixir', 5.0)
            push_frequency = strategy_config.get('push_frequency', 0.5)
            
            # Verificar se tem elixir suficiente
            if elixir < strategy_config.get('elixir_threshold', 7.0):
                return False
            
            # Verificar se há inimigos no campo
            enemy_units = game_state.get('enemy_units', [])
            if len(enemy_units) > 3:  # Muitos inimigos, melhor defender
                return False
            
            # Decisão baseada na frequência da estratégia
            return np.random.random() < push_frequency
            
        except Exception as e:
            logger.error(f"Error determining push decision: {e}")
            return False
    
    def _should_defend_now(self, game_state: Dict, strategy_config: Dict) -> bool:
        """Determina se deve defender agora"""
        try:
            defense_priority = strategy_config.get('defense_priority', 0.5)
            enemy_units = game_state.get('enemy_units', [])
            
            # Sempre defender se há inimigos próximos
            if len(enemy_units) > 0:
                return True
            
            # Decisão baseada na prioridade defensiva da estratégia
            return np.random.random() < defense_priority
            
        except Exception as e:
            logger.error(f"Error determining defense decision: {e}")
            return True
    
    def _get_spell_priority(self, game_state: Dict, strategy_config: Dict) -> float:
        """Retorna prioridade para uso de magias"""
        try:
            base_priority = strategy_config.get('spell_usage', 0.5)
            
            # Ajustar baseado na situação
            enemy_units = game_state.get('enemy_units', [])
            if len(enemy_units) > 2:
                base_priority += 0.2  # Mais inimigos = mais prioridade para magias
            
            return min(1.0, base_priority)
            
        except Exception as e:
            logger.error(f"Error getting spell priority: {e}")
            return 0.5
    
    def _get_card_recommendations(self, available_cards: List[str], strategy_config: Dict) -> List[str]:
        """Retorna recomendações de cartas baseadas na estratégia"""
        try:
            recommendations = []
            strategy = self.current_strategy
            
            # Recomendações baseadas na estratégia
            if strategy in ['aggressive', 'counter_aggressive']:
                # Priorizar cartas agressivas
                aggressive_cards = ['giant', 'golem', 'pekka', 'hog_rider']
                recommendations.extend([card for card in available_cards if card in aggressive_cards])
            
            elif strategy in ['defensive', 'counter_defensive']:
                # Priorizar cartas defensivas
                defensive_cards = ['cannon', 'tesla', 'knight', 'mini_pekka']
                recommendations.extend([card for card in available_cards if card in defensive_cards])
            
            elif strategy == 'cycling':
                # Priorizar cartas baratas
                cheap_cards = ['skeletons', 'goblins', 'spear_goblins', 'ice_spirit']
                recommendations.extend([card for card in available_cards if card in cheap_cards])
            
            # Adicionar outras cartas disponíveis
            other_cards = [card for card in available_cards if card not in recommendations]
            recommendations.extend(other_cards)
            
            return recommendations[:4]  # Retornar até 4 cartas
            
        except Exception as e:
            logger.error(f"Error getting card recommendations: {e}")
            return available_cards[:4]
    
    def _get_positioning_advice(self, strategy_config: Dict) -> Dict:
        """Retorna conselhos de posicionamento baseados na estratégia"""
        try:
            strategy = self.current_strategy
            
            if strategy in ['aggressive', 'counter_aggressive']:
                return {
                    'tank_position': 'frontline',
                    'support_position': 'close_to_tank',
                    'spell_targeting': 'enemy_groups',
                    'defense_position': 'bridge'
                }
            elif strategy in ['defensive', 'counter_defensive']:
                return {
                    'tank_position': 'backline',
                    'support_position': 'spread_out',
                    'spell_targeting': 'defensive',
                    'defense_position': 'tower_area'
                }
            elif strategy == 'cycling':
                return {
                    'tank_position': 'midline',
                    'support_position': 'flexible',
                    'spell_targeting': 'opportunistic',
                    'defense_position': 'reactive'
                }
            else:  # balanced
                return {
                    'tank_position': 'adaptive',
                    'support_position': 'situational',
                    'spell_targeting': 'value_based',
                    'defense_position': 'optimal'
                }
                
        except Exception as e:
            logger.error(f"Error getting positioning advice: {e}")
            return {
                'tank_position': 'adaptive',
                'support_position': 'situational',
                'spell_targeting': 'value_based',
                'defense_position': 'optimal'
            }
    
    def _get_default_strategy(self) -> Dict:
        """Retorna estratégia padrão"""
        return {
            'strategy': 'balanced',
            'config': self.strategies['balanced'],
            'reason': 'Default strategy',
            'confidence': 0.0,
            'opponent_playstyle': 'unknown'
        }
    
    def _get_default_recommendations(self) -> Dict:
        """Retorna recomendações padrão"""
        return {
            'strategy': 'balanced',
            'elixir_threshold': 7.0,
            'should_push': False,
            'should_defend': True,
            'spell_priority': 0.5,
            'card_recommendations': [],
            'positioning_advice': {
                'tank_position': 'adaptive',
                'support_position': 'situational',
                'spell_targeting': 'value_based',
                'defense_position': 'optimal'
            }
        }
    
    def get_adaptation_summary(self) -> Dict:
        """Retorna resumo das adaptações"""
        try:
            return {
                'current_strategy': self.current_strategy,
                'adaptation_count': len(self.adaptation_history),
                'recent_adaptations': self.adaptation_history[-5:],
                'strategy_effectiveness': self._calculate_strategy_effectiveness(),
                'adaptation_frequency': self._calculate_adaptation_frequency()
            }
            
        except Exception as e:
            logger.error(f"Error getting adaptation summary: {e}")
            return {'current_strategy': 'balanced', 'adaptation_count': 0}
    
    def _calculate_strategy_effectiveness(self) -> Dict:
        """Calcula efetividade das estratégias"""
        try:
            effectiveness = {}
            
            for strategy in self.strategies.keys():
                strategy_adaptations = [a for a in self.adaptation_history if a['strategy'] == strategy]
                if strategy_adaptations:
                    effectiveness[strategy] = len(strategy_adaptations)
                else:
                    effectiveness[strategy] = 0
            
            return effectiveness
            
        except Exception as e:
            logger.error(f"Error calculating strategy effectiveness: {e}")
            return {}
    
    def _calculate_adaptation_frequency(self) -> float:
        """Calcula frequência de adaptações"""
        try:
            if len(self.adaptation_history) < 2:
                return 0.0
            
            # Calcular tempo médio entre adaptações
            timestamps = [a['timestamp'] for a in self.adaptation_history]
            time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            
            if time_diffs:
                avg_time_between_adaptations = np.mean(time_diffs)
                # Converter para frequência (adaptações por minuto)
                frequency = 60.0 / avg_time_between_adaptations if avg_time_between_adaptations > 0 else 0.0
                return min(10.0, frequency)  # Limitar a 10 adaptações por minuto
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating adaptation frequency: {e}")
            return 0.0
    
    def reset_strategy(self):
        """Reseta para estratégia padrão"""
        try:
            self.current_strategy = 'balanced'
            self.strategy_confidence = 0.0
            logger.info("Strategy reset to balanced")
            
        except Exception as e:
            logger.error(f"Error resetting strategy: {e}")

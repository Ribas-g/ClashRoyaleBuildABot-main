"""
Sistema de Análise Tática Profunda
Analisa situações complexas do jogo e toma decisões estratégicas
"""
from typing import Dict, List, Tuple, Optional
from loguru import logger
import time


class TacticalAnalyzer:
    def __init__(self):
        # Definições de ameaças críticas
        self.critical_threats = {
            'giant_behind_king': {
                'threat_level': 9,
                'description': 'Giant atrás da torre do rei - BIG PUSH incoming!',
                'response_options': ['quick_opposite_attack', 'prepare_defense', 'elixir_advantage_wait'],
                'combo_predictions': ['musketeer', 'archers', 'wizard', 'witch', 'baby_dragon']
            },
            'hog_bridge': {
                'threat_level': 8,
                'description': 'Hog Rider na ponte - dano imediato na torre',
                'response_options': ['building_defense', 'knight_intercept', 'cannon_distract']
            },
            'balloon_push': {
                'threat_level': 10,
                'description': 'Balloon push - ameaça aérea crítica',
                'response_options': ['immediate_air_defense', 'musketeer_archers']
            }
        }
        
        # Combos inimigos comuns
        self.enemy_combo_patterns = {
            'giant_support': {
                'primary': 'giant',
                'likely_support': ['musketeer', 'archers', 'wizard', 'witch', 'baby_dragon'],
                'timing': 'when_giant_crosses_bridge',
                'counter_strategy': 'eliminate_support_first'
            },
            'hog_spell': {
                'primary': 'hog_rider', 
                'likely_support': ['fireball', 'zap', 'lightning'],
                'timing': 'simultaneous_or_after',
                'counter_strategy': 'building_distract_then_counter'
            },
            'balloon_freeze': {
                'primary': 'balloon',
                'likely_support': ['freeze', 'rage'],
                'timing': 'when_balloon_reaches_tower',
                'counter_strategy': 'immediate_air_defense'
            }
        }
        
        # Táticas de luring (corrigidas para serem realistas)
        self.luring_tactics = {
            'building_luring': {
                'cards': ['cannon', 'tesla', 'tombstone'],
                'targets': ['giant', 'pekka', 'golem', 'hog_rider', 'royal_giant'],
                'purpose': 'Atrair tanks para longe da torre',
                'positioning': 'center_field_defensive',
                'follow_up': 'dps_units_behind_building'
            },
            'cheap_distraction': {
                'cards': ['spear_goblins', 'skeletons', 'ice_spirit'],
                'targets': ['musketeer', 'wizard', 'witch', 'archers'],
                'purpose': 'Fazer tropas de longo alcance perderem tempo',
                'positioning': 'slightly_off_path',
                'follow_up': 'real_threat_from_different_angle'
            },
            'split_pressure_luring': {
                'cards': ['knight', 'archers'],
                'targets': ['any_ground_troop'],
                'purpose': 'Dividir atenção inimiga',
                'positioning': 'opposite_lane',
                'follow_up': 'main_attack_other_side'
            }
        }
    
    def analyze_threat_situation(self, enemy_units: List[Dict], our_elixir: int, 
                               enemy_elixir_estimate: int) -> Dict:
        """Analisa situação de ameaça específica"""
        analysis = {
            'threat_type': 'none',
            'threat_level': 0,
            'recommended_response': 'neutral',
            'response_options': [],
            'predicted_combo': None,
            'time_to_react': 0,
            'should_panic': False
        }
        
        try:
            if not enemy_units:
                return analysis
            
            # Detectar ameaças específicas
            for unit in enemy_units:
                unit_name = unit.get('name', '')
                unit_pos = unit.get('position', (0, 0))
                
                if len(unit_pos) < 2:
                    continue
                    
                unit_x, unit_y = unit_pos
                
                # GIANT ATRÁS DA TORRE DO REI - PERIGO MÁXIMO!
                if unit_name == 'giant' and unit_y <= 4:
                    analysis['threat_type'] = 'giant_behind_king'
                    analysis['threat_level'] = 9
                    analysis['should_panic'] = False  # Não panic, mas ação decisiva
                    
                    # Análise de opções
                    response_options = self._analyze_giant_threat_options(
                        unit_pos, our_elixir, enemy_elixir_estimate
                    )
                    analysis['response_options'] = response_options
                    analysis['recommended_response'] = response_options[0] if response_options else 'prepare_defense'
                    
                    # Predizer combo
                    analysis['predicted_combo'] = self._predict_giant_combo(unit_pos, enemy_elixir_estimate)
                    
                    # Tempo para reagir (Giant leva ~8 segundos para chegar na ponte)
                    analysis['time_to_react'] = 8
                    
                    logger.warning(f"🚨 GIANT BEHIND KING DETECTED! Position: {unit_pos}")
                    logger.info(f"Response options: {response_options}")
                    
                    break  # Giant é prioridade máxima
                
                # Outras ameaças críticas
                elif unit_name in ['hog_rider', 'ram_rider'] and unit_y >= 5:
                    analysis['threat_type'] = 'fast_attack'
                    analysis['threat_level'] = 8
                    analysis['time_to_react'] = 3
                    
                elif unit_name == 'balloon' and unit_y >= 6:
                    analysis['threat_type'] = 'air_threat'
                    analysis['threat_level'] = 10
                    analysis['time_to_react'] = 4
        
        except Exception as e:
            logger.debug(f"Error analyzing threat situation: {e}")
        
        return analysis
    
    def _analyze_giant_threat_options(self, giant_pos: Tuple[int, int], 
                                    our_elixir: int, enemy_elixir: int) -> List[str]:
        """Analisa opções de resposta ao Giant atrás da torre"""
        options = []
        giant_x, giant_y = giant_pos
        
        # Opção 1: Ataque rápido no lado oposto
        if our_elixir >= 6:
            opposite_side = 'right' if giant_x < 9 else 'left'
            options.append(f'quick_attack_{opposite_side}_side')
            logger.info(f"💡 Option: Quick attack on {opposite_side} side while enemy commits to Giant")
        
        # Opção 2: Preparar defesa sólida
        if our_elixir >= 4:
            options.append('prepare_solid_defense')
            logger.info("💡 Option: Prepare solid defense with counter units")
        
        # Opção 3: Aguardar e punir overcommit
        if enemy_elixir <= 6:
            options.append('wait_and_punish_overcommit')
            logger.info("💡 Option: Wait for enemy overcommit then counter-attack")
        
        # Opção 4: Elixir advantage play
        if our_elixir > enemy_elixir + 2:
            options.append('elixir_advantage_play')
            logger.info("💡 Option: Use elixir advantage for aggressive response")
        
        return options if options else ['emergency_defense']
    
    def _predict_giant_combo(self, giant_pos: Tuple[int, int], enemy_elixir: int) -> Dict:
        """Prediz que combo o inimigo pode fazer com Giant"""
        combo_prediction = {
            'likely_support': [],
            'support_positions': [],
            'timing_estimate': 0,
            'total_threat_level': 5  # Giant base threat
        }
        
        giant_x, giant_y = giant_pos
        
        # Predições baseadas no elixir inimigo
        if enemy_elixir >= 4:
            # Pode adicionar suporte de 4 elixir
            combo_prediction['likely_support'].extend(['musketeer', 'wizard', 'baby_dragon'])
            combo_prediction['support_positions'].append((giant_x - 1, giant_y + 1))
            combo_prediction['total_threat_level'] += 4
        
        if enemy_elixir >= 3:
            # Pode adicionar suporte de 3 elixir
            combo_prediction['likely_support'].extend(['archers', 'knight'])
            combo_prediction['support_positions'].append((giant_x, giant_y + 1))
            combo_prediction['total_threat_level'] += 3
        
        # Timing: suporte vem quando Giant cruza a ponte
        combo_prediction['timing_estimate'] = 6  # segundos
        
        logger.info(f"🔮 Predicted Giant combo: {combo_prediction['likely_support'][:2]}")
        
        return combo_prediction
    
    def analyze_counter_push_opportunity(self, our_units: List[Dict], 
                                       enemy_units: List[Dict]) -> Dict:
        """Analisa oportunidade de counter-push"""
        opportunity = {
            'has_opportunity': False,
            'push_type': 'none',
            'recommended_cards': [],
            'positioning_strategy': {},
            'timing': 'none'
        }
        
        try:
            # Verificar se temos unidades que podem fazer counter-push
            our_attackers = [u for u in our_units if u.get('name') in ['knight', 'minipekka', 'giant']]
            
            if not our_attackers:
                return opportunity
            
            # Analisar tipo de counter-push
            for unit in our_attackers:
                unit_name = unit.get('name')
                unit_pos = unit.get('position', (0, 0))
                
                if len(unit_pos) < 2:
                    continue
                
                unit_x, unit_y = unit_pos
                
                # Se unidade está avançando (no lado inimigo)
                if unit_y < 8:
                    opportunity['has_opportunity'] = True
                    
                    if unit_name == 'knight':
                        opportunity['push_type'] = 'knight_counter_push'
                        opportunity['recommended_cards'] = ['musketeer', 'archers']
                        
                        # Musketeer deve acompanhar Knight
                        opportunity['positioning_strategy'] = {
                            'musketeer': {
                                'position': (unit_x - 1, unit_y + 1),
                                'reasoning': 'Support Knight counter-push from safe distance'
                            },
                            'archers': {
                                'position': (unit_x, unit_y + 2),
                                'reasoning': 'Additional support behind Knight'
                            }
                        }
                        
                        logger.info(f"🗡️ Knight counter-push opportunity! Support at {unit_pos}")
                    
                    elif unit_name == 'minipekka':
                        opportunity['push_type'] = 'minipekka_counter_push'
                        opportunity['recommended_cards'] = ['spear_goblins', 'minions']
                        
                        opportunity['positioning_strategy'] = {
                            'spear_goblins': {
                                'position': (unit_x + 1, unit_y + 1),
                                'reasoning': 'Cheap support for Mini Pekka push'
                            }
                        }
                        
                        logger.info(f"⚔️ Mini Pekka counter-push opportunity!")
                    
                    opportunity['timing'] = 'immediate'
                    break
        
        except Exception as e:
            logger.debug(f"Error analyzing counter-push opportunity: {e}")
        
        return opportunity
    
    def calculate_luring_strategy(self, enemy_threat: Dict, our_available_cards: List[str],
                                our_elixir: int) -> Dict:
        """Calcula estratégia de luring realista (atrair atenção)"""
        luring_strategy = {
            'should_lure': False,
            'lure_card': None,
            'lure_position': None,
            'follow_up_card': None,
            'follow_up_position': None,
            'expected_outcome': 'none',
            'luring_type': 'none'
        }
        
        try:
            threat_name = enemy_threat.get('name', '')
            threat_pos = enemy_threat.get('position', (0, 0))
            
            if len(threat_pos) < 2:
                return luring_strategy
            
            threat_x, threat_y = threat_pos
            
            # LURING CORRETO: Apenas para tropas que podem ser "luradas"
            
            # 1. Building Luring - Giant só é atraído por construções
            if threat_name in ['giant', 'pekka', 'golem', 'hog_rider'] and our_elixir >= 4:
                # Infelizmente não temos construções no nosso deck
                # Mas podemos usar distração com tropas baratas
                if 'spear_goblins' in our_available_cards:
                    luring_strategy['should_lure'] = True
                    luring_strategy['lure_card'] = 'spear_goblins'
                    luring_strategy['luring_type'] = 'cheap_distraction'
                    # Posição: ligeiramente fora do caminho para fazer Giant desviar
                    luring_strategy['lure_position'] = (threat_x + 2, threat_y + 3)
                    luring_strategy['expected_outcome'] = 'distract_and_delay'
                    
                    logger.info(f"🎣 Cheap distraction: Spear Goblins to delay {threat_name}")
            
            # 2. Luring de tropas de longo alcance (mais efetivo)
            elif threat_name in ['musketeer', 'wizard', 'witch', 'archers'] and our_elixir >= 3:
                if 'knight' in our_available_cards:
                    luring_strategy['should_lure'] = True
                    luring_strategy['lure_card'] = 'knight'
                    luring_strategy['luring_type'] = 'tank_distraction'
                    # Knight vai na frente para tankar, força tropa a focar nele
                    luring_strategy['lure_position'] = (threat_x, threat_y + 2)
                    luring_strategy['expected_outcome'] = 'tank_absorbs_damage'
                    
                    logger.info(f"🎣 Tank luring: Knight tanks {threat_name} damage")
            
            # 3. Split pressure luring (mais avançado)
            elif our_elixir >= 6 and len(our_available_cards) >= 2:
                # Usar carta no lado oposto para dividir atenção
                if 'knight' in our_available_cards or 'archers' in our_available_cards:
                    lure_card = 'knight' if 'knight' in our_available_cards else 'archers'
                    luring_strategy['should_lure'] = True
                    luring_strategy['lure_card'] = lure_card
                    luring_strategy['luring_type'] = 'split_pressure'
                    # Lado oposto para dividir atenção
                    opposite_x = 3 if threat_x > 9 else 14
                    luring_strategy['lure_position'] = (opposite_x, 8)
                    luring_strategy['expected_outcome'] = 'split_enemy_attention'
                    
                    logger.info(f"🎣 Split pressure: {lure_card} on opposite side to divide attention")
        
        except Exception as e:
            logger.debug(f"Error calculating luring strategy: {e}")
        
        return luring_strategy
    
    def analyze_push_coordination(self, our_units: List[Dict], target_card: str) -> Dict:
        """Analisa coordenação de push - onde colocar suporte"""
        coordination = {
            'should_coordinate': False,
            'primary_unit': None,
            'support_positioning': {},
            'coordination_type': 'none'
        }
        
        try:
            # Encontrar unidade principal que precisa de suporte
            primary_unit = None
            for unit in our_units:
                unit_name = unit.get('name', '')
                unit_pos = unit.get('position', (0, 0))
                
                if len(unit_pos) < 2:
                    continue
                
                unit_x, unit_y = unit_pos
                
                # Se Knight está fazendo counter-push
                if unit_name == 'knight' and unit_y < 8:
                    primary_unit = unit
                    coordination['coordination_type'] = 'knight_support'
                    
                    # Musketeer deve acompanhar Knight
                    if target_card == 'musketeer':
                        coordination['should_coordinate'] = True
                        coordination['support_positioning'] = {
                            'position': (unit_x - 1, unit_y + 1),
                            'reasoning': 'Musketeer supports Knight counter-push from safe distance',
                            'distance_from_primary': 1.4  # tiles
                        }
                        
                        logger.info(f"🤝 Coordinating Musketeer support for Knight counter-push")
                
                # Se Giant está fazendo push
                elif unit_name == 'giant' and unit_y < 10:
                    primary_unit = unit
                    coordination['coordination_type'] = 'giant_support'
                    
                    # Suporte atrás do Giant
                    if target_card in ['musketeer', 'archers', 'minions']:
                        coordination['should_coordinate'] = True
                        coordination['support_positioning'] = {
                            'position': (unit_x, unit_y + 2),
                            'reasoning': f'{target_card} supports Giant push from behind',
                            'distance_from_primary': 2.0
                        }
                        
                        logger.info(f"🤝 Coordinating {target_card} support for Giant push")
                
                if coordination['should_coordinate']:
                    coordination['primary_unit'] = primary_unit
                    break
        
        except Exception as e:
            logger.debug(f"Error analyzing push coordination: {e}")
        
        return coordination
    
    def evaluate_tactical_decision(self, situation: str, our_elixir: int, 
                                 enemy_elixir: int, available_cards: List[str]) -> Dict:
        """Avalia decisão tática complexa"""
        decision = {
            'recommended_action': 'wait',
            'reasoning': 'Insufficient information',
            'confidence': 0.5,
            'alternative_options': [],
            'risk_assessment': 'medium'
        }
        
        try:
            if situation == 'giant_behind_king':
                # Análise profunda da situação Giant
                elixir_advantage = our_elixir - enemy_elixir
                
                if elixir_advantage >= 3 and our_elixir >= 6:
                    # Temos vantagem, podemos atacar o lado oposto
                    decision['recommended_action'] = 'quick_opposite_attack'
                    decision['reasoning'] = 'Elixir advantage allows quick opposite lane pressure'
                    decision['confidence'] = 0.8
                    decision['risk_assessment'] = 'medium'
                    
                elif our_elixir >= 7 and 'minipekka' in available_cards:
                    # Podemos defender bem e contra-atacar
                    decision['recommended_action'] = 'prepare_defense_counter'
                    decision['reasoning'] = 'Strong defense available, can counter-attack after'
                    decision['confidence'] = 0.9
                    decision['risk_assessment'] = 'low'
                    
                elif our_elixir <= 4:
                    # Pouco elixir, precisa ser conservador
                    decision['recommended_action'] = 'cycle_and_defend'
                    decision['reasoning'] = 'Low elixir, need to cycle and prepare minimal defense'
                    decision['confidence'] = 0.7
                    decision['risk_assessment'] = 'high'
                
                else:
                    # Situação padrão
                    decision['recommended_action'] = 'standard_defense'
                    decision['reasoning'] = 'Standard defensive response to Giant threat'
                    decision['confidence'] = 0.6
                    decision['risk_assessment'] = 'medium'
                
                logger.info(f"🧠 Tactical decision vs Giant: {decision['recommended_action']} ({decision['confidence']:.1%} confidence)")
        
        except Exception as e:
            logger.debug(f"Error evaluating tactical decision: {e}")
        
        return decision

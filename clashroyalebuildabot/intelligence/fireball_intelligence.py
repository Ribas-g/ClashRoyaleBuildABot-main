"""
Sistema de Inteligência da Bola de Fogo
Configura targeting específico para construções e unidades de alto valor
"""
from typing import Dict, List, Tuple, Optional
from loguru import logger
import time
import math


class FireballIntelligence:
    def __init__(self):
        # Configurações de targeting específico
        self.target_priorities = {
            'high_value_units': {
                'musketeer': {
                    'priority': 10,
                    'elixir_value': 4,
                    'reason': 'High damage ranged unit',
                    'min_distance': 2.0,
                    'max_distance': 4.0
                },
                'wizard': {
                    'priority': 9,
                    'elixir_value': 5,
                    'reason': 'Area damage dealer',
                    'min_distance': 2.0,
                    'max_distance': 4.0
                },
                'witch': {
                    'priority': 8,
                    'elixir_value': 5,
                    'reason': 'Skeleton spawner',
                    'min_distance': 2.0,
                    'max_distance': 4.0
                },
                'archers': {
                    'priority': 7,
                    'elixir_value': 3,
                    'reason': 'Ranged support unit',
                    'min_distance': 1.5,
                    'max_distance': 3.5
                },
                'three_musketeers': {
                    'priority': 11,
                    'elixir_value': 9,
                    'reason': 'Extremely high value target',
                    'min_distance': 2.5,
                    'max_distance': 4.5
                },
                'barbarians': {
                    'priority': 6,
                    'elixir_value': 5,
                    'reason': 'High HP melee unit',
                    'min_distance': 1.0,
                    'max_distance': 3.0
                }
            },
            'buildings': {
                'inferno_tower': {
                    'priority': 9,
                    'elixir_value': 5,
                    'reason': 'Tank killer building',
                    'min_distance': 2.0,
                    'max_distance': 4.0,
                    'targeting_strategy': 'center_of_building'
                },
                'tesla': {
                    'priority': 8,
                    'elixir_value': 4,
                    'reason': 'Hidden building',
                    'min_distance': 2.0,
                    'max_distance': 4.0,
                    'targeting_strategy': 'center_of_building'
                },
                'bomb_tower': {
                    'priority': 7,
                    'elixir_value': 4,
                    'reason': 'Splash damage building',
                    'min_distance': 2.0,
                    'max_distance': 4.0,
                    'targeting_strategy': 'center_of_building'
                },
                'cannon': {
                    'priority': 6,
                    'elixir_value': 3,
                    'reason': 'Cheap building',
                    'min_distance': 1.5,
                    'max_distance': 3.5,
                    'targeting_strategy': 'center_of_building'
                }
            },
            'grouped_units': {
                'minion_horde': {
                    'priority': 8,
                    'elixir_value': 5,
                    'reason': 'Grouped air units',
                    'min_units': 3,
                    'max_distance': 3.0
                },
                'skeleton_army': {
                    'priority': 7,
                    'elixir_value': 3,
                    'reason': 'Grouped ground units',
                    'min_units': 4,
                    'max_distance': 2.5
                },
                'goblin_gang': {
                    'priority': 6,
                    'elixir_value': 3,
                    'reason': 'Mixed ground units',
                    'min_units': 3,
                    'max_distance': 2.5
                }
            }
        }
        
        # Configurações de timing e pathing
        self.casting_config = {
            'fireball_travel_time': 1.0,  # Tempo de viagem da bola de fogo
            'unit_movement_speed': {
                'fast': 2.5,      # Unidades rápidas (goblins, etc.)
                'medium': 1.8,    # Unidades médias (knight, etc.)
                'slow': 1.2       # Unidades lentas (giant, etc.)
            },
            'prediction_factors': {
                'bridge_crossing': 1.5,    # Multiplicador para travessia de ponte
                'tower_approach': 1.2,     # Multiplicador para aproximação da torre
                'unit_clustering': 0.8     # Reduz velocidade quando agrupadas
            }
        }
        
        # Histórico de usos da bola de fogo
        self.fireball_history = []
        
    def analyze_fireball_targets(self, enemy_units: List[Dict], enemy_buildings: List[Dict]) -> Dict:
        """Analisa alvos potenciais para bola de fogo"""
        analysis = {
            'best_target': None,
            'target_position': None,
            'expected_value': 0,
            'reasoning': [],
            'should_cast': False,
            'timing_instructions': {}
        }
        
        try:
            # Analisar unidades individuais de alto valor
            high_value_targets = self._find_high_value_units(enemy_units)
            
            # Analisar construções
            building_targets = self._find_building_targets(enemy_buildings)
            
            # Analisar grupos de unidades
            grouped_targets = self._find_grouped_units(enemy_units)
            
            # Combinar todos os alvos e encontrar o melhor
            all_targets = high_value_targets + building_targets + grouped_targets
            
            if not all_targets:
                analysis['reasoning'].append("No viable Fireball targets found")
                return analysis
            
            # Ordenar por valor esperado
            all_targets.sort(key=lambda x: x['expected_value'], reverse=True)
            best_target = all_targets[0]
            
            if best_target['expected_value'] >= 4:  # Mínimo de 4 elixir de valor
                analysis['best_target'] = best_target
                analysis['target_position'] = best_target['position']
                analysis['expected_value'] = best_target['expected_value']
                analysis['should_cast'] = True
                analysis['reasoning'].append(f"Targeting {best_target['name']} - Expected value: {best_target['expected_value']}")
                analysis['reasoning'].append(f"Reason: {best_target['reason']}")
                
                # Calcular timing de casting
                analysis['timing_instructions'] = self._calculate_casting_timing(best_target)
            else:
                analysis['reasoning'].append(f"Best target value ({best_target['expected_value']}) below minimum (4)")
            
        except Exception as e:
            logger.debug(f"Error analyzing Fireball targets: {e}")
            analysis['reasoning'].append(f"Error in analysis: {e}")
        
        return analysis
    
    def _find_high_value_units(self, enemy_units: List[Dict]) -> List[Dict]:
        """Encontra unidades de alto valor para bola de fogo"""
        targets = []
        
        for unit in enemy_units:
            unit_name = unit.get('name', '')
            unit_pos = unit.get('position', (0, 0))
            
            if unit_name in self.target_priorities['high_value_units']:
                target_config = self.target_priorities['high_value_units'][unit_name]
                
                # Verificar se está em posição válida
                if self._is_valid_target_position(unit_pos, target_config):
                    targets.append({
                        'name': unit_name,
                        'position': unit_pos,
                        'type': 'high_value_unit',
                        'expected_value': target_config['elixir_value'],
                        'reason': target_config['reason'],
                        'priority': target_config['priority']
                    })
        
        return targets
    
    def _find_building_targets(self, enemy_buildings: List[Dict]) -> List[Dict]:
        """Encontra construções para bola de fogo"""
        targets = []
        
        for building in enemy_buildings:
            building_name = building.get('name', '')
            building_pos = building.get('position', (0, 0))
            
            if building_name in self.target_priorities['buildings']:
                target_config = self.target_priorities['buildings'][building_name]
                
                # Verificar se está em posição válida
                if self._is_valid_target_position(building_pos, target_config):
                    targets.append({
                        'name': building_name,
                        'position': building_pos,
                        'type': 'building',
                        'expected_value': target_config['elixir_value'],
                        'reason': target_config['reason'],
                        'priority': target_config['priority'],
                        'targeting_strategy': target_config['targeting_strategy']
                    })
        
        return targets
    
    def _find_grouped_units(self, enemy_units: List[Dict]) -> List[Dict]:
        """Encontra grupos de unidades para bola de fogo"""
        targets = []
        
        # Agrupar unidades por proximidade
        unit_groups = self._group_units_by_proximity(enemy_units)
        
        for group in unit_groups:
            if len(group) >= 3:  # Mínimo de 3 unidades para valer a pena
                # Calcular posição central do grupo
                center_pos = self._calculate_group_center(group)
                
                # Calcular valor total do grupo
                total_value = sum(self._get_unit_elixir_value(unit.get('name', '')) for unit in group)
                
                if total_value >= 4:  # Mínimo de 4 elixir de valor
                    targets.append({
                        'name': f"group_{len(group)}_units",
                        'position': center_pos,
                        'type': 'grouped_units',
                        'expected_value': total_value,
                        'reason': f"Group of {len(group)} units worth {total_value} elixir",
                        'priority': 7,
                        'units': group
                    })
        
        return targets
    
    def _group_units_by_proximity(self, units: List[Dict], max_distance: float = 3.0) -> List[List[Dict]]:
        """Agrupa unidades por proximidade"""
        groups = []
        used_units = set()
        
        for i, unit in enumerate(units):
            if i in used_units:
                continue
            
            group = [unit]
            used_units.add(i)
            
            for j, other_unit in enumerate(units):
                if j in used_units:
                    continue
                
                distance = self._calculate_distance(unit['position'], other_unit['position'])
                if distance <= max_distance:
                    group.append(other_unit)
                    used_units.add(j)
            
            if len(group) >= 2:  # Pelo menos 2 unidades para formar grupo
                groups.append(group)
        
        return groups
    
    def _calculate_group_center(self, units: List[Dict]) -> Tuple[float, float]:
        """Calcula o centro de um grupo de unidades"""
        if not units:
            return (0, 0)
        
        total_x = sum(unit['position'][0] for unit in units)
        total_y = sum(unit['position'][1] for unit in units)
        
        return (total_x / len(units), total_y / len(units))
    
    def _is_valid_target_position(self, position: Tuple[float, float], target_config: Dict) -> bool:
        """Verifica se a posição é válida para o alvo"""
        x, y = position
        
        # Verificar distância mínima e máxima
        min_dist = target_config.get('min_distance', 1.0)
        max_dist = target_config.get('max_distance', 4.0)
        
        # Calcular distância do centro do campo (aproximação)
        center_distance = math.sqrt(x**2 + y**2)
        
        return min_dist <= center_distance <= max_dist
    
    def _calculate_casting_timing(self, target: Dict) -> Dict:
        """Calcula timing de casting baseado no movimento do alvo"""
        timing = {
            'cast_delay': 0.0,
            'lead_distance': 0.0,
            'prediction_factor': 1.0,
            'instructions': []
        }
        
        try:
            target_pos = target['position']
            target_type = target.get('type', 'unit')
            
            # Para construções, não precisa de lead
            if target_type == 'building':
                timing['instructions'].append("Cast immediately - building is stationary")
                return timing
            
            # Para unidades, calcular lead baseado na velocidade
            unit_speed = self._estimate_unit_speed(target.get('name', ''))
            
            # Calcular direção de movimento (simplificado)
            movement_direction = self._estimate_movement_direction(target_pos)
            
            # Calcular lead baseado no tempo de viagem da bola de fogo
            fireball_travel_time = self.casting_config['fireball_travel_time']
            lead_distance = unit_speed * fireball_travel_time
            
            # Aplicar fatores de predição
            prediction_factor = self._calculate_prediction_factor(target_pos, movement_direction)
            lead_distance *= prediction_factor
            
            timing['cast_delay'] = 0.0  # Cast imediatamente
            timing['lead_distance'] = lead_distance
            timing['prediction_factor'] = prediction_factor
            
            timing['instructions'].extend([
                f"Cast immediately with {lead_distance:.1f} tile lead",
                f"Unit speed: {unit_speed:.1f} tiles/sec",
                f"Prediction factor: {prediction_factor:.2f}"
            ])
            
        except Exception as e:
            logger.debug(f"Error calculating casting timing: {e}")
            timing['instructions'].append("Error in timing calculation")
        
        return timing
    
    def _estimate_unit_speed(self, unit_name: str) -> float:
        """Estima a velocidade de uma unidade"""
        # Mapeamento de velocidades baseado em conhecimento do jogo
        speed_mapping = {
            'musketeer': 'medium',
            'wizard': 'medium',
            'witch': 'slow',
            'archers': 'medium',
            'knight': 'medium',
            'giant': 'slow',
            'minipekka': 'fast',
            'pekka': 'slow',
            'goblins': 'fast',
            'spear_goblins': 'fast',
            'minions': 'fast',
            'barbarians': 'medium'
        }
        
        speed_category = speed_mapping.get(unit_name, 'medium')
        return self.casting_config['unit_movement_speed'][speed_category]
    
    def _estimate_movement_direction(self, position: Tuple[float, float]) -> str:
        """Estima a direção de movimento baseado na posição"""
        x, y = position
        
        # Simplificado: se está no lado inimigo, provavelmente vai para nossa torre
        if y < 8:  # Lado inimigo
            return 'towards_our_tower'
        else:  # Nosso lado
            return 'towards_enemy_tower'
    
    def _calculate_prediction_factor(self, position: Tuple[float, float], direction: str) -> float:
        """Calcula fator de predição baseado na situação"""
        factor = 1.0
        
        x, y = position
        
        # Fator para travessia de ponte
        if 7 <= x <= 9 and 8 <= y <= 10:  # Área da ponte
            factor *= self.casting_config['prediction_factors']['bridge_crossing']
        
        # Fator para aproximação da torre
        if y > 12:  # Próximo da nossa torre
            factor *= self.casting_config['prediction_factors']['tower_approach']
        
        # Fator para agrupamento (reduz velocidade)
        # Isso seria calculado baseado em outras unidades próximas
        
        return factor
    
    def _get_unit_elixir_value(self, unit_name: str) -> int:
        """Obtém o valor em elixir de uma unidade"""
        # Mapeamento de custos de elixir
        elixir_costs = {
            'musketeer': 4, 'wizard': 5, 'witch': 5, 'archers': 3,
            'knight': 3, 'giant': 5, 'minipekka': 4, 'pekka': 7,
            'goblins': 2, 'spear_goblins': 2, 'minions': 3, 'barbarians': 5
        }
        
        return elixir_costs.get(unit_name, 3)
    
    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calcula distância entre duas posições"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def record_fireball_usage(self, target: Dict, success: bool, damage_dealt: int):
        """Registra uso da bola de fogo para aprendizado"""
        record = {
            'timestamp': time.time(),
            'target': target,
            'success': success,
            'damage_dealt': damage_dealt,
            'expected_value': target.get('expected_value', 0)
        }
        
        self.fireball_history.append(record)
        
        # Manter apenas os últimos 20 usos
        if len(self.fireball_history) > 20:
            self.fireball_history.pop(0)
    
    def get_fireball_statistics(self) -> Dict:
        """Retorna estatísticas de uso da bola de fogo"""
        if not self.fireball_history:
            return {'total_uses': 0, 'success_rate': 0.0, 'avg_damage': 0.0}
        
        total_uses = len(self.fireball_history)
        successful_uses = sum(1 for record in self.fireball_history if record['success'])
        total_damage = sum(record['damage_dealt'] for record in self.fireball_history)
        
        return {
            'total_uses': total_uses,
            'success_rate': successful_uses / total_uses,
            'avg_damage': total_damage / total_uses,
            'recent_performance': self._analyze_recent_performance()
        }
    
    def _analyze_recent_performance(self) -> Dict:
        """Analisa performance recente da bola de fogo"""
        recent_records = self.fireball_history[-5:]  # Últimos 5 usos
        
        if not recent_records:
            return {'trend': 'no_data'}
        
        recent_success_rate = sum(1 for record in recent_records if record['success']) / len(recent_records)
        
        if recent_success_rate >= 0.8:
            trend = 'improving'
        elif recent_success_rate >= 0.6:
            trend = 'stable'
        else:
            trend = 'declining'
        
        return {
            'trend': trend,
            'recent_success_rate': recent_success_rate,
            'recommendation': self._get_performance_recommendation(recent_success_rate)
        }
    
    def _get_performance_recommendation(self, success_rate: float) -> str:
        """Gera recomendação baseada na performance"""
        if success_rate >= 0.8:
            return "Continue current targeting strategy"
        elif success_rate >= 0.6:
            return "Consider more conservative targeting"
        else:
            return "Review targeting priorities and timing"

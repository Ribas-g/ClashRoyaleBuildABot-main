"""
Sistema de Mecânicas Avançadas de Jogo
Implementa mecânicas profissionais de Clash Royale
"""
import math
import random
from typing import List, Dict, Tuple, Optional
from loguru import logger


class AdvancedGameMechanics:
    """Sistema de mecânicas avançadas de jogo"""
    
    def __init__(self):
        # Configurações de mecânicas avançadas
        self.unit_mechanics = {
            'giant': {
                'aggro_range': 5.0,
                'retarget_conditions': ['tower_damage', 'building_priority'],
                'kiting_susceptible': True,
                'splash_damage': False,
                'air_target': False
            },
            'musketeer': {
                'aggro_range': 6.0,
                'retarget_conditions': ['closest_target', 'air_priority'],
                'kiting_susceptible': False,
                'splash_damage': False,
                'air_target': True
            },
            'knight': {
                'aggro_range': 1.5,
                'retarget_conditions': ['closest_target'],
                'kiting_susceptible': True,
                'splash_damage': False,
                'air_target': False
            },
            'minipekka': {
                'aggro_range': 1.5,
                'retarget_conditions': ['closest_target', 'high_hp_priority'],
                'kiting_susceptible': True,
                'splash_damage': False,
                'air_target': False
            },
            'minions': {
                'aggro_range': 1.5,
                'retarget_conditions': ['closest_target'],
                'kiting_susceptible': False,
                'splash_damage': False,
                'air_target': True
            }
        }
        
        # Configurações de timing
        self.timing_config = {
            'spawn_delay': 1.0,  # Segundos para spawn
            'aggro_delay': 0.5,  # Segundos para aggro
            'retarget_delay': 0.3,  # Segundos para retarget
            'kiting_delay': 0.2  # Segundos para kiting
        }
    
    def calculate_advanced_positioning(self, unit_name: str, target: Dict, 
                                     allies: List[Dict], enemies: List[Dict],
                                     game_phase: str) -> Tuple[float, float]:
        """Calcula posicionamento avançado considerando mecânicas do jogo"""
        try:
            base_x, base_y = target.get('x', 9), target.get('y', 7)
            
            # Obter mecânicas da unidade
            unit_mech = self.unit_mechanics.get(unit_name, {})
            aggro_range = unit_mech.get('aggro_range', 1.5)
            kiting_susceptible = unit_mech.get('kiting_susceptible', False)
            
            # Ajustar baseado na fase do jogo
            if game_phase == 'early_game':
                # Posicionamento mais conservador
                base_x += random.uniform(-0.5, 0.5)
                base_y += random.uniform(-0.5, 0.5)
            elif game_phase == 'mid_game':
                # Posicionamento balanceado
                base_x += random.uniform(-1.0, 1.0)
                base_y += random.uniform(-1.0, 1.0)
            elif game_phase == 'late_game':
                # Posicionamento agressivo
                base_x += random.uniform(-1.5, 1.5)
                base_y += random.uniform(-1.5, 1.5)
            
            # Considerar kiting
            if kiting_susceptible and enemies:
                # Posicionar para evitar kiting
                closest_enemy = min(enemies, key=lambda e: 
                    math.sqrt((e.get('x', 0) - base_x)**2 + (e.get('y', 0) - base_y)**2))
                
                enemy_x, enemy_y = closest_enemy.get('x', 0), closest_enemy.get('y', 0)
                
                # Calcular direção oposta ao inimigo
                dx = base_x - enemy_x
                dy = base_y - enemy_y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance > 0:
                    # Normalizar e aplicar offset
                    dx = dx / distance * aggro_range
                    dy = dy / distance * aggro_range
                    base_x += dx
                    base_y += dy
            
            # Evitar sobreposição com aliados
            for ally in allies:
                ally_x, ally_y = ally.get('x', 0), ally.get('y', 0)
                distance = math.sqrt((base_x - ally_x)**2 + (base_y - ally_y)**2)
                
                if distance < 2.0:
                    # Ajustar posição
                    angle = math.atan2(base_y - ally_y, base_x - ally_x)
                    base_x = ally_x + 2.0 * math.cos(angle)
                    base_y = ally_y + 2.0 * math.sin(angle)
            
            # Manter dentro dos limites
            base_x = max(1.0, min(17.0, base_x))
            base_y = max(1.0, min(14.0, base_y))
            
            return base_x, base_y
            
        except Exception as e:
            logger.error(f"Error in advanced positioning: {e}")
            return target.get('x', 9), target.get('y', 7)
    
    def calculate_kiting_strategy(self, unit: Dict, enemies: List[Dict]) -> Dict:
        """Calcula estratégia de kiting para uma unidade"""
        try:
            unit_name = unit.get('name', 'unknown')
            unit_x, unit_y = unit.get('x', 0), unit.get('y', 0)
            
            # Verificar se a unidade é suscetível a kiting
            unit_mech = self.unit_mechanics.get(unit_name, {})
            if not unit_mech.get('kiting_susceptible', False):
                return {'should_kite': False, 'reason': 'Unit not susceptible to kiting'}
            
            # Encontrar inimigos próximos
            nearby_enemies = []
            for enemy in enemies:
                distance = math.sqrt((enemy.get('x', 0) - unit_x)**2 + (enemy.get('y', 0) - unit_y)**2)
                if distance < 3.0:  # Inimigos próximos
                    nearby_enemies.append({
                        'enemy': enemy,
                        'distance': distance
                    })
            
            if not nearby_enemies:
                return {'should_kite': False, 'reason': 'No nearby enemies'}
            
            # Ordenar por distância
            nearby_enemies.sort(key=lambda x: x['distance'])
            closest_enemy = nearby_enemies[0]['enemy']
            
            # Calcular direção de kiting
            enemy_x, enemy_y = closest_enemy.get('x', 0), closest_enemy.get('y', 0)
            
            # Direção oposta ao inimigo
            dx = unit_x - enemy_x
            dy = unit_y - enemy_y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                # Normalizar
                dx = dx / distance
                dy = dy / distance
                
                # Calcular posição de kiting
                kite_distance = 2.0  # Distância de kiting
                kite_x = unit_x + dx * kite_distance
                kite_y = unit_y + dy * kite_distance
                
                # Manter dentro dos limites
                kite_x = max(1.0, min(17.0, kite_x))
                kite_y = max(1.0, min(14.0, kite_y))
                
                return {
                    'should_kite': True,
                    'kite_position': (kite_x, kite_y),
                    'target_enemy': closest_enemy,
                    'kite_distance': kite_distance,
                    'reason': f'Kiting {unit_name} away from {closest_enemy.get("name", "enemy")}'
                }
            
            return {'should_kite': False, 'reason': 'Cannot calculate kiting direction'}
            
        except Exception as e:
            logger.error(f"Error calculating kiting strategy: {e}")
            return {'should_kite': False, 'reason': f'Error: {e}'}
    
    def calculate_aggro_management(self, unit: Dict, enemies: List[Dict], 
                                 allies: List[Dict]) -> Dict:
        """Calcula gerenciamento de aggro para uma unidade"""
        try:
            unit_name = unit.get('name', 'unknown')
            unit_x, unit_y = unit.get('x', 0), unit.get('y', 0)
            
            # Obter configurações de aggro
            unit_mech = self.unit_mechanics.get(unit_name, {})
            aggro_range = unit_mech.get('aggro_range', 1.5)
            retarget_conditions = unit_mech.get('retarget_conditions', [])
            
            # Encontrar alvos no alcance
            targets_in_range = []
            for enemy in enemies:
                distance = math.sqrt((enemy.get('x', 0) - unit_x)**2 + (enemy.get('y', 0) - unit_y)**2)
                if distance <= aggro_range:
                    targets_in_range.append({
                        'enemy': enemy,
                        'distance': distance,
                        'priority': self._calculate_target_priority(enemy, retarget_conditions)
                    })
            
            if not targets_in_range:
                return {'has_target': False, 'reason': 'No targets in range'}
            
            # Ordenar por prioridade
            targets_in_range.sort(key=lambda x: x['priority'], reverse=True)
            best_target = targets_in_range[0]
            
            return {
                'has_target': True,
                'target': best_target['enemy'],
                'target_priority': best_target['priority'],
                'targets_in_range': len(targets_in_range),
                'aggro_range': aggro_range,
                'reason': f'Targeting {best_target["enemy"].get("name", "enemy")} with priority {best_target["priority"]:.2f}'
            }
            
        except Exception as e:
            logger.error(f"Error calculating aggro management: {e}")
            return {'has_target': False, 'reason': f'Error: {e}'}
    
    def _calculate_target_priority(self, enemy: Dict, conditions: List[str]) -> float:
        """Calcula prioridade de um alvo baseado nas condições"""
        try:
            priority = 0.0
            enemy_name = enemy.get('name', 'unknown')
            
            for condition in conditions:
                if condition == 'closest_target':
                    priority += 1.0
                elif condition == 'air_priority' and enemy.get('is_air', False):
                    priority += 2.0
                elif condition == 'high_hp_priority':
                    hp = enemy.get('hp', 100)
                    priority += hp / 1000.0  # Normalizar HP
                elif condition == 'tower_damage':
                    if enemy.get('can_damage_tower', False):
                        priority += 3.0
                elif condition == 'building_priority':
                    if enemy_name in ['giant', 'golem', 'pekka']:
                        priority += 2.0
            
            return priority
            
        except Exception as e:
            logger.error(f"Error calculating target priority: {e}")
            return 0.0
    
    def calculate_spawn_timing(self, unit_name: str, game_state: Dict) -> Dict:
        """Calcula timing ótimo para spawn de uma unidade"""
        try:
            # Obter informações do estado do jogo
            elixir = game_state.get('elixir', 0)
            enemy_elixir = game_state.get('enemy_elixir', 0)
            game_phase = game_state.get('phase', 'mid_game')
            
            # Configurações de timing baseadas na unidade
            timing_config = {
                'giant': {'min_elixir': 5, 'preferred_elixir': 8, 'spawn_delay': 1.5},
                'musketeer': {'min_elixir': 4, 'preferred_elixir': 6, 'spawn_delay': 1.0},
                'knight': {'min_elixir': 3, 'preferred_elixir': 5, 'spawn_delay': 0.8},
                'minipekka': {'min_elixir': 4, 'preferred_elixir': 6, 'spawn_delay': 1.0},
                'minions': {'min_elixir': 3, 'preferred_elixir': 5, 'spawn_delay': 0.8}
            }
            
            unit_timing = timing_config.get(unit_name, {
                'min_elixir': 3, 'preferred_elixir': 5, 'spawn_delay': 1.0
            })
            
            # Verificar se pode spawnar
            can_spawn = elixir >= unit_timing['min_elixir']
            
            # Calcular urgência do spawn
            urgency = 0.0
            if can_spawn:
                if elixir >= unit_timing['preferred_elixir']:
                    urgency = 1.0  # Spawn imediato
                else:
                    urgency = (elixir - unit_timing['min_elixir']) / (unit_timing['preferred_elixir'] - unit_timing['min_elixir'])
            
            # Considerar vantagem de elixir
            elixir_advantage = elixir - enemy_elixir
            if elixir_advantage > 2:
                urgency *= 1.2  # Mais urgente com vantagem
            elif elixir_advantage < -2:
                urgency *= 0.8  # Menos urgente em desvantagem
            
            # Considerar fase do jogo
            if game_phase == 'early_game':
                urgency *= 0.7  # Mais conservador no início
            elif game_phase == 'late_game':
                urgency *= 1.3  # Mais agressivo no final
            
            return {
                'can_spawn': can_spawn,
                'urgency': max(0.0, min(1.0, urgency)),
                'spawn_delay': unit_timing['spawn_delay'],
                'min_elixir': unit_timing['min_elixir'],
                'preferred_elixir': unit_timing['preferred_elixir'],
                'elixir_advantage': elixir_advantage,
                'reason': f'Can spawn: {can_spawn}, Urgency: {urgency:.2f}'
            }
            
        except Exception as e:
            logger.error(f"Error calculating spawn timing: {e}")
            return {'can_spawn': False, 'urgency': 0.0, 'reason': f'Error: {e}'}
    
    def calculate_retarget_strategy(self, unit: Dict, current_target: Dict, 
                                  available_targets: List[Dict]) -> Dict:
        """Calcula estratégia de retarget para uma unidade"""
        try:
            unit_name = unit.get('name', 'unknown')
            unit_mech = self.unit_mechanics.get(unit_name, {})
            retarget_conditions = unit_mech.get('retarget_conditions', [])
            
            # Calcular prioridade do alvo atual
            current_priority = self._calculate_target_priority(current_target, retarget_conditions)
            
            # Encontrar melhor alvo disponível
            best_target = None
            best_priority = current_priority
            
            for target in available_targets:
                priority = self._calculate_target_priority(target, retarget_conditions)
                if priority > best_priority:
                    best_target = target
                    best_priority = priority
            
            if best_target and best_priority > current_priority:
                return {
                    'should_retarget': True,
                    'new_target': best_target,
                    'priority_improvement': best_priority - current_priority,
                    'reason': f'Retargeting to {best_target.get("name", "enemy")} with priority {best_priority:.2f}'
                }
            else:
                return {
                    'should_retarget': False,
                    'reason': f'Current target optimal with priority {current_priority:.2f}'
                }
                
        except Exception as e:
            logger.error(f"Error calculating retarget strategy: {e}")
            return {'should_retarget': False, 'reason': f'Error: {e}'}
    
    def calculate_formation_strategy(self, units: List[Dict], target: Dict) -> Dict:
        """Calcula estratégia de formação para múltiplas unidades"""
        try:
            if len(units) < 2:
                return {'formation_type': 'single', 'positions': []}
            
            target_x, target_y = target.get('x', 9), target.get('y', 7)
            
            # Classificar unidades por tipo
            tanks = [u for u in units if u.get('name') in ['giant', 'golem', 'pekka']]
            supports = [u for u in units if u.get('name') in ['musketeer', 'archers', 'wizard']]
            melee = [u for u in units if u.get('name') in ['knight', 'minipekka']]
            
            formation_positions = []
            
            if tanks and supports:
                # Formação tank + suporte
                tank = tanks[0]
                support = supports[0]
                
                # Tank na frente
                tank_x = target_x
                tank_y = target_y
                
                # Suporte atrás
                support_x = target_x + 2.0
                support_y = target_y + 1.0
                
                formation_positions = [
                    {'unit': tank, 'position': (tank_x, tank_y)},
                    {'unit': support, 'position': (support_x, support_y)}
                ]
                
                formation_type = 'tank_support'
                
            elif len(units) >= 3:
                # Formação triangular
                center_x, center_y = target_x, target_y
                
                for i, unit in enumerate(units[:3]):
                    angle = (i * 120) * (math.pi / 180)  # 120 graus cada
                    distance = 1.5
                    
                    pos_x = center_x + distance * math.cos(angle)
                    pos_y = center_y + distance * math.sin(angle)
                    
                    formation_positions.append({
                        'unit': unit,
                        'position': (pos_x, pos_y)
                    })
                
                formation_type = 'triangular'
                
            else:
                # Formação linear
                for i, unit in enumerate(units):
                    pos_x = target_x + i * 1.0
                    pos_y = target_y
                    
                    formation_positions.append({
                        'unit': unit,
                        'position': (pos_x, pos_y)
                    })
                
                formation_type = 'linear'
            
            return {
                'formation_type': formation_type,
                'positions': formation_positions,
                'target': target,
                'unit_count': len(units)
            }
            
        except Exception as e:
            logger.error(f"Error calculating formation strategy: {e}")
            return {'formation_type': 'error', 'positions': [], 'reason': f'Error: {e}'}

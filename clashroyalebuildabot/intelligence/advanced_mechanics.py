"""
Sistema de Mecânicas Avançadas
Baseado em técnicas do bot_Clash_Royale para jogabilidade profissional
"""
import math
from typing import List, Dict, Tuple, Optional
from loguru import logger


class AdvancedMechanics:
    def __init__(self):
        # Configurações de mecânicas
        self.unit_speeds = {
            'giant': 0.8,      # Lento
            'knight': 1.2,     # Médio
            'musketeer': 1.0,  # Médio
            'archers': 1.1,    # Médio-rápido
            'minipekka': 1.4,  # Rápido
            'minions': 1.6,    # Muito rápido
            'spear_goblins': 1.5,  # Muito rápido
            'fireball': 2.0,   # Instantâneo
            'zap': 2.0,        # Instantâneo
            'arrows': 1.8      # Muito rápido
        }
        
        # Configurações de alcance
        self.unit_ranges = {
            'giant': 1.0,      # Melee
            'knight': 1.0,     # Melee
            'musketeer': 6.0,  # Ranged
            'archers': 5.0,    # Ranged
            'minipekka': 1.0,  # Melee
            'minions': 1.0,    # Melee (voadores)
            'spear_goblins': 5.5,  # Ranged
            'fireball': 8.0,   # Spell
            'zap': 3.0,        # Spell
            'arrows': 7.0      # Spell
        }
        
        # Configurações de dano por segundo
        self.unit_dps = {
            'giant': 126,      # Alto
            'knight': 139,     # Médio-alto
            'musketeer': 160,  # Alto
            'archers': 86,     # Médio
            'minipekka': 325,  # Muito alto
            'minions': 84,     # Médio
            'spear_goblins': 67,   # Baixo
            'fireball': 572,   # Muito alto
            'zap': 159,        # Médio
            'arrows': 243      # Alto
        }
        
        # Configurações de vida
        self.unit_hp = {
            'giant': 2544,     # Muito alto
            'knight': 1399,    # Alto
            'musketeer': 598,  # Baixo
            'archers': 253,    # Muito baixo
            'minipekka': 598,  # Baixo
            'minions': 190,    # Muito baixo
            'spear_goblins': 110,  # Muito baixo
            'fireball': 0,     # Spell
            'zap': 0,          # Spell
            'arrows': 0        # Spell
        }
    
    def calculate_unit_interaction(self, unit1: Dict, unit2: Dict) -> Dict:
        """Calcula interação entre duas unidades"""
        try:
            unit1_name = unit1.get('name', 'unknown')
            unit2_name = unit2.get('name', 'unknown')
            
            # Distância entre unidades
            distance = self._calculate_distance(unit1, unit2)
            
            # Verificar se estão no alcance
            unit1_range = self.unit_ranges.get(unit1_name, 1.0)
            unit2_range = self.unit_ranges.get(unit2_name, 1.0)
            
            unit1_can_attack = distance <= unit1_range
            unit2_can_attack = distance <= unit2_range
            
            # Calcular tempo para matar
            unit1_dps = self.unit_dps.get(unit1_name, 100)
            unit2_dps = self.unit_dps.get(unit2_name, 100)
            unit1_hp = self.unit_hp.get(unit1_name, 500)
            unit2_hp = self.unit_hp.get(unit2_name, 500)
            
            if unit1_can_attack and unit2_hp > 0:
                unit1_ttk = unit2_hp / unit1_dps  # Time to kill
            else:
                unit1_ttk = float('inf')
            
            if unit2_can_attack and unit1_hp > 0:
                unit2_ttk = unit1_hp / unit2_dps
            else:
                unit2_ttk = float('inf')
            
            # Determinar vencedor
            if unit1_ttk < unit2_ttk:
                winner = unit1_name
                advantage = unit2_ttk - unit1_ttk
            elif unit2_ttk < unit1_ttk:
                winner = unit2_name
                advantage = unit1_ttk - unit2_ttk
            else:
                winner = 'tie'
                advantage = 0
            
            return {
                'distance': distance,
                'unit1_can_attack': unit1_can_attack,
                'unit2_can_attack': unit2_can_attack,
                'unit1_ttk': unit1_ttk,
                'unit2_ttk': unit2_ttk,
                'winner': winner,
                'advantage': advantage,
                'interaction_type': self._get_interaction_type(unit1_name, unit2_name)
            }
            
        except Exception as e:
            logger.error(f"Error calculating unit interaction: {e}")
            return {}
    
    def _calculate_distance(self, unit1: Dict, unit2: Dict) -> float:
        """Calcula distância entre duas unidades"""
        try:
            x1, y1 = unit1.get('x', 0), unit1.get('y', 0)
            x2, y2 = unit2.get('x', 0), unit2.get('y', 0)
            
            return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return float('inf')
    
    def _get_interaction_type(self, unit1_name: str, unit2_name: str) -> str:
        """Determina o tipo de interação entre unidades"""
        # Tank vs Support
        if unit1_name in ['giant', 'golem', 'pekka'] and unit2_name in ['musketeer', 'archers', 'wizard']:
            return 'tank_vs_support'
        
        # Ranged vs Melee
        if unit1_name in ['musketeer', 'archers', 'wizard'] and unit2_name in ['knight', 'minipekka', 'giant']:
            return 'ranged_vs_melee'
        
        # Swarm vs Single
        if unit1_name in ['minions', 'spear_goblins', 'skeletons'] and unit2_name in ['knight', 'minipekka']:
            return 'swarm_vs_single'
        
        # Spell vs Troop
        if unit1_name in ['fireball', 'zap', 'arrows'] and unit2_name not in ['fireball', 'zap', 'arrows']:
            return 'spell_vs_troop'
        
        return 'standard'
    
    def calculate_optimal_positioning(self, unit_name: str, target: Dict, allies: List[Dict], enemies: List[Dict]) -> Tuple[float, float]:
        """Calcula posicionamento ótimo para uma unidade"""
        try:
            target_x, target_y = target.get('x', 0), target.get('y', 0)
            unit_range = self.unit_ranges.get(unit_name, 1.0)
            
            # Posição base (próxima ao alvo)
            base_x = target_x
            base_y = target_y
            
            # Ajustar baseado no tipo de unidade
            if unit_name in ['musketeer', 'archers', 'wizard']:
                # Unidades ranged: manter distância
                if target_x < 9:  # Lado esquerdo
                    base_x = target_x + unit_range
                else:  # Lado direito
                    base_x = target_x - unit_range
                base_y = target_y + 1  # Ligeiramente atrás
            
            elif unit_name in ['giant', 'golem', 'pekka']:
                # Tanks: ir direto ao alvo
                base_x = target_x
                base_y = target_y
            
            elif unit_name in ['knight', 'minipekka']:
                # Melee: posicionar para interceptar
                if target_x < 9:
                    base_x = target_x + 1
                else:
                    base_x = target_x - 1
                base_y = target_y
            
            # Evitar sobreposição com aliados
            for ally in allies:
                ally_x, ally_y = ally.get('x', 0), ally.get('y', 0)
                distance = math.sqrt((base_x - ally_x)**2 + (base_y - ally_y)**2)
                
                if distance < 2.0:  # Muito próximo
                    # Ajustar posição
                    angle = math.atan2(base_y - ally_y, base_x - ally_x)
                    base_x = ally_x + 2.0 * math.cos(angle)
                    base_y = ally_y + 2.0 * math.sin(angle)
            
            # Manter dentro dos limites do campo
            base_x = max(1.0, min(17.0, base_x))
            base_y = max(1.0, min(14.0, base_y))
            
            return base_x, base_y
            
        except Exception as e:
            logger.error(f"Error calculating optimal positioning: {e}")
            return target.get('x', 9), target.get('y', 7)
    
    def calculate_spell_value(self, spell_name: str, target_area: Tuple[float, float], enemies: List[Dict]) -> float:
        """Calcula o valor de usar um spell em uma área"""
        try:
            target_x, target_y = target_area
            total_value = 0
            
            for enemy in enemies:
                enemy_x, enemy_y = enemy.get('x', 0), enemy.get('y', 0)
                distance = math.sqrt((target_x - enemy_x)**2 + (target_y - enemy_y)**2)
                
                # Verificar se está no alcance do spell
                spell_range = self.unit_ranges.get(spell_name, 3.0)
                
                if distance <= spell_range:
                    enemy_name = enemy.get('name', 'unknown')
                    enemy_elixir = self._get_unit_elixir_cost(enemy_name)
                    
                    # Valor baseado no custo de elixir
                    total_value += enemy_elixir
                    
                    # Bônus para unidades de alto valor
                    if enemy_name in ['musketeer', 'wizard', 'three_musketeers']:
                        total_value += 2
                    
                    # Bônus para grupos
                    if enemy_name in ['minions', 'spear_goblins', 'skeletons']:
                        total_value += 0.5
            
            return total_value
            
        except Exception as e:
            logger.error(f"Error calculating spell value: {e}")
            return 0.0
    
    def _get_unit_elixir_cost(self, unit_name: str) -> int:
        """Retorna o custo de elixir de uma unidade"""
        elixir_costs = {
            'giant': 5,
            'knight': 3,
            'musketeer': 4,
            'archers': 3,
            'minipekka': 4,
            'minions': 3,
            'spear_goblins': 2,
            'fireball': 4,
            'zap': 2,
            'arrows': 3,
            'wizard': 5,
            'three_musketeers': 9,
            'skeletons': 1,
            'goblins': 2
        }
        
        return elixir_costs.get(unit_name, 3)
    
    def calculate_push_timing(self, tank_unit: Dict, support_units: List[Dict]) -> Dict:
        """Calcula timing para push coordenado"""
        try:
            tank_name = tank_unit.get('name', 'giant')
            tank_speed = self.unit_speeds.get(tank_name, 1.0)
            
            # Calcular tempo para tank chegar na ponte
            tank_x, tank_y = tank_unit.get('x', 0), tank_unit.get('y', 0)
            bridge_distance = abs(9 - tank_x) + abs(7 - tank_y)  # Distância até a ponte
            tank_time_to_bridge = bridge_distance / tank_speed
            
            # Calcular delays para unidades de suporte
            support_delays = {}
            
            for support in support_units:
                support_name = support.get('name', 'unknown')
                support_speed = self.unit_speeds.get(support_name, 1.0)
                
                # Unidades mais rápidas devem esperar
                if support_speed > tank_speed:
                    delay = (bridge_distance / support_speed) - tank_time_to_bridge
                    support_delays[support_name] = max(0, delay)
                else:
                    support_delays[support_name] = 0
            
            return {
                'tank_time_to_bridge': tank_time_to_bridge,
                'support_delays': support_delays,
                'total_push_time': tank_time_to_bridge + max(support_delays.values())
            }
            
        except Exception as e:
            logger.error(f"Error calculating push timing: {e}")
            return {}
    
    def calculate_counter_push_opportunity(self, enemies: List[Dict], allies: List[Dict], elixir: float) -> Dict:
        """Calcula oportunidade de contra-ataque"""
        try:
            # Analisar força inimiga
            enemy_strength = 0
            for enemy in enemies:
                enemy_name = enemy.get('name', 'unknown')
                enemy_elixir = self._get_unit_elixir_cost(enemy_name)
                enemy_strength += enemy_elixir
            
            # Analisar força aliada
            ally_strength = 0
            for ally in allies:
                ally_name = ally.get('name', 'unknown')
                ally_elixir = self._get_unit_elixir_cost(ally_name)
                ally_strength += ally_elixir
            
            # Calcular vantagem
            total_strength = ally_strength + elixir
            advantage = total_strength - enemy_strength
            
            # Determinar tipo de contra-ataque
            if advantage > 3:
                counter_type = 'aggressive'
                recommended_elixir = min(10, elixir)
            elif advantage > 0:
                counter_type = 'balanced'
                recommended_elixir = min(8, elixir)
            else:
                counter_type = 'defensive'
                recommended_elixir = min(5, elixir)
            
            return {
                'enemy_strength': enemy_strength,
                'ally_strength': ally_strength,
                'advantage': advantage,
                'counter_type': counter_type,
                'recommended_elixir': recommended_elixir,
                'should_counter': advantage > -2
            }
            
        except Exception as e:
            logger.error(f"Error calculating counter push: {e}")
            return {}
    
    def calculate_elixir_efficiency(self, action_cost: int, expected_value: float) -> float:
        """Calcula eficiência de elixir de uma ação"""
        try:
            if action_cost <= 0:
                return 0.0
            
            # Valor esperado por elixir
            efficiency = expected_value / action_cost
            
            # Bônus para ações de baixo custo
            if action_cost <= 2:
                efficiency *= 1.2
            
            # Penalidade para ações muito caras
            if action_cost >= 6:
                efficiency *= 0.8
            
            return efficiency
            
        except Exception as e:
            logger.error(f"Error calculating elixir efficiency: {e}")
            return 0.0
    
    def get_unit_priorities(self, unit_name: str) -> Dict:
        """Retorna prioridades de uma unidade"""
        priorities = {
            'giant': {
                'primary_target': 'towers',
                'secondary_target': 'buildings',
                'avoid': ['swarms', 'ranged'],
                'positioning': 'frontline'
            },
            'musketeer': {
                'primary_target': 'air_units',
                'secondary_target': 'ranged_units',
                'avoid': ['tanks', 'swarms'],
                'positioning': 'backline'
            },
            'knight': {
                'primary_target': 'ranged_units',
                'secondary_target': 'medium_units',
                'avoid': ['tanks', 'air_units'],
                'positioning': 'midline'
            },
            'minipekka': {
                'primary_target': 'tanks',
                'secondary_target': 'medium_units',
                'avoid': ['swarms', 'air_units'],
                'positioning': 'midline'
            },
            'fireball': {
                'primary_target': 'grouped_units',
                'secondary_target': 'high_value_units',
                'avoid': ['single_units', 'low_value'],
                'positioning': 'spell'
            }
        }
        
        return priorities.get(unit_name, {
            'primary_target': 'general',
            'secondary_target': 'general',
            'avoid': [],
            'positioning': 'general'
        })

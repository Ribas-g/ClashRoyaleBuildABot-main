"""
Sistema de Timing de Combos
Garante que tanks chegam primeiro e suporte vem depois
"""
import time
from typing import Dict, List, Tuple, Optional
from loguru import logger


class ComboTiming:
    def __init__(self):
        # Velocidades das tropas (tiles por segundo aproximadamente)
        self.unit_speeds = {
            # Tanks (lentos)
            'giant': 1.0,
            'pekka': 1.0,
            'golem': 0.8,
            'royal_giant': 1.2,
            
            # Tropas médias
            'knight': 1.5,
            'musketeer': 1.3,
            'archers': 1.3,
            'wizard': 1.4,
            
            # Tropas rápidas
            'minions': 2.0,
            'bats': 2.5,
            'spear_goblins': 1.8,
            'minipekka': 1.6,
            
            # Tropas muito rápidas
            'hog_rider': 2.5,
            'ram_rider': 2.3
        }
        
        # Distâncias típicas do campo
        self.field_distances = {
            'behind_king_to_bridge': 8,    # Da torre do rei até a ponte
            'bridge_to_tower': 6,          # Da ponte até a torre inimiga
            'defensive_to_bridge': 5       # Posição defensiva até ponte
        }
    
    def calculate_arrival_time(self, unit_name: str, start_pos: Tuple[int, int], 
                             target_pos: Tuple[int, int]) -> float:
        """Calcula tempo para unidade chegar ao destino"""
        try:
            speed = self.unit_speeds.get(unit_name, 1.5)
            
            # Calcula distância
            distance = ((target_pos[0] - start_pos[0])**2 + (target_pos[1] - start_pos[1])**2)**0.5
            
            # Tempo = distância / velocidade
            arrival_time = distance / speed
            
            return arrival_time
        except Exception as e:
            logger.debug(f"Error calculating arrival time: {e}")
            return 5.0  # Valor padrão
    
    def calculate_combo_timing(self, tank_card: str, support_cards: List[str],
                             tank_position: Tuple[int, int]) -> Dict:
        """Calcula timing correto para combo tank + suporte"""
        timing_plan = {
            'tank_placement': 'immediate',
            'support_delays': {},
            'total_combo_time': 0,
            'success_probability': 0.0
        }
        
        try:
            tank_x, tank_y = tank_position
            bridge_position = (tank_x, 8)  # Ponte
            tower_position = (tank_x, 15)  # Torre inimiga
            
            # Calcular quando tank chega na ponte
            tank_to_bridge_time = self.calculate_arrival_time(tank_card, tank_position, bridge_position)
            
            # Calcular delays para suporte
            for support_card in support_cards:
                support_speed = self.unit_speeds.get(support_card, 1.5)
                tank_speed = self.unit_speeds.get(tank_card, 1.0)
                
                # Se suporte é mais rápido que tank, precisa de delay
                if support_speed > tank_speed:
                    # Calcular delay necessário
                    speed_ratio = support_speed / tank_speed
                    delay_needed = tank_to_bridge_time * (speed_ratio - 1.0) / speed_ratio
                    
                    timing_plan['support_delays'][support_card] = max(0.5, delay_needed)
                    
                    logger.info(f"⏰ {support_card} needs {delay_needed:.1f}s delay to sync with {tank_card}")
                else:
                    # Suporte mais lento, pode jogar imediatamente
                    timing_plan['support_delays'][support_card] = 0.0
            
            # Calcular probabilidade de sucesso
            timing_plan['success_probability'] = self._calculate_combo_success_probability(
                tank_card, support_cards, timing_plan['support_delays']
            )
            
            timing_plan['total_combo_time'] = tank_to_bridge_time + max(timing_plan['support_delays'].values())
            
        except Exception as e:
            logger.debug(f"Error calculating combo timing: {e}")
        
        return timing_plan
    
    def _calculate_combo_success_probability(self, tank_card: str, support_cards: List[str],
                                           delays: Dict[str, float]) -> float:
        """Calcula probabilidade de sucesso do combo"""
        base_probability = 0.7  # Base para combos bem timados
        
        # Bônus por tank forte
        if tank_card in ['giant', 'pekka', 'golem']:
            base_probability += 0.1
        
        # Bônus por suporte adequado
        good_support = ['musketeer', 'archers', 'wizard']
        support_bonus = sum(0.05 for card in support_cards if card in good_support)
        
        # Penalidade por delays muito longos
        delay_penalty = sum(max(0, delay - 3.0) * 0.05 for delay in delays.values())
        
        final_probability = min(0.95, max(0.3, base_probability + support_bonus - delay_penalty))
        
        return final_probability
    
    def should_wait_for_tank(self, tank_card: str, support_card: str, 
                           tank_position: Tuple[int, int]) -> Dict:
        """Determina se deve aguardar tank chegar antes de colocar suporte"""
        decision = {
            'should_wait': False,
            'wait_time': 0.0,
            'reasoning': 'No timing needed'
        }
        
        try:
            tank_speed = self.unit_speeds.get(tank_card, 1.0)
            support_speed = self.unit_speeds.get(support_card, 1.5)
            
            # Se suporte é mais rápido, deve aguardar
            if support_speed > tank_speed * 1.2:  # 20% mais rápido
                tank_x, tank_y = tank_position
                bridge_distance = 8 - tank_y  # Distância até a ponte
                
                # Tempo para tank chegar na ponte
                tank_bridge_time = bridge_distance / tank_speed
                
                # Suporte deve aguardar tank estar quase na ponte
                wait_time = tank_bridge_time * 0.7  # 70% do caminho
                
                decision['should_wait'] = True
                decision['wait_time'] = wait_time
                decision['reasoning'] = f'{support_card} faster than {tank_card}, waiting for tank to lead'
                
                logger.info(f"⏰ {support_card} should wait {wait_time:.1f}s for {tank_card} to lead")
        
        except Exception as e:
            logger.debug(f"Error calculating wait timing: {e}")
        
        return decision

"""
Sistema de Range de Atenção das Cartas
Determina se uma carta vai chamar atenção de tropas inimigas baseado na distância
"""
import math
from typing import List, Dict, Tuple, Optional
from loguru import logger


class AttentionSystem:
    def __init__(self):
        # Range de atenção para cada tipo de carta (em tiles)
        self.attention_ranges = {
            # Tropas terrestres
            'giant': 5.5,
            'knight': 5.0,
            'minipekka': 5.5,
            'pekka': 6.0,
            'barbarians': 5.0,
            'skeleton_army': 4.0,
            'spear_goblins': 4.5,
            
            # Tropas aéreas
            'minions': 5.5,
            'baby_dragon': 6.0,
            'balloon': 6.5,
            'bats': 4.0,
            
            # Tropas de longo alcance
            'musketeer': 6.0,
            'archers': 5.5,
            'wizard': 5.5,
            'witch': 5.5,
            
            # Construções
            'cannon': 5.5,
            'tesla': 5.5,
            'inferno_tower': 6.0,
            'bomb_tower': 6.0,
            
            # Tropas especiais
            'hog_rider': 6.0,
            'prince': 6.5,
            'dark_prince': 6.0
        }
        
        # Prioridade de atenção (qual tropa atrai mais atenção)
        self.attention_priority = {
            'giant': 10,       # Tanks atraem muita atenção
            'pekka': 10,
            'golem': 10,
            'knight': 7,       # Mini-tanks médio
            'musketeer': 8,    # Tropas de alto valor
            'wizard': 8,
            'witch': 8,
            'archers': 6,      # Tropas de médio valor
            'minions': 5,
            'spear_goblins': 3, # Tropas baratas
            'skeleton_army': 4
        }
    
    def calculate_attention_from_position(self, card_position: Tuple[int, int], 
                                        enemy_units: List[Dict], 
                                        card_name: str) -> Dict:
        """
        Calcula se uma carta vai chamar atenção de tropas inimigas
        """
        card_x, card_y = card_position
        card_range = self.attention_ranges.get(card_name, 5.0)
        card_priority = self.attention_priority.get(card_name, 5)
        
        attention_analysis = {
            'will_attract_attention': False,
            'attracting_units': [],
            'safe_placement': True,
            'attention_score': 0,
            'recommendations': []
        }
        
        for enemy_unit in enemy_units:
            enemy_x, enemy_y = enemy_unit['position']
            enemy_name = enemy_unit['name']
            enemy_range = self.attention_ranges.get(enemy_name, 5.0)
            
            # Calcula distância
            distance = math.sqrt((card_x - enemy_x)**2 + (card_y - enemy_y)**2)
            
            # Verifica se está no range de atenção
            if distance <= enemy_range:
                attention_analysis['will_attract_attention'] = True
                attention_analysis['attracting_units'].append({
                    'unit': enemy_name,
                    'distance': distance,
                    'threat_level': self._calculate_threat_level(enemy_name, distance)
                })
                
                # Calcula score de atenção
                threat_score = self._calculate_threat_level(enemy_name, distance)
                attention_analysis['attention_score'] += threat_score
        
        # Determina se posicionamento é seguro
        if attention_analysis['attention_score'] > card_priority:
            attention_analysis['safe_placement'] = False
            attention_analysis['recommendations'].append('find_safer_position')
        
        # Gera recomendações específicas
        attention_analysis['recommendations'].extend(
            self._generate_positioning_recommendations(card_name, attention_analysis['attracting_units'])
        )
        
        return attention_analysis
    
    def find_safe_position(self, card_name: str, enemy_units: List[Dict], 
                          target_area: str = 'defensive') -> Optional[Tuple[int, int]]:
        """
        Encontra uma posição segura para uma carta
        """
        # Áreas de posicionamento baseadas no objetivo
        position_areas = {
            'defensive': [(x, y) for x in range(3, 14) for y in range(8, 15)],
            'offensive': [(x, y) for x in range(5, 12) for y in range(3, 8)],
            'support': [(x, y) for x in range(4, 13) for y in range(5, 10)]
        }
        
        candidate_positions = position_areas.get(target_area, position_areas['defensive'])
        
        best_position = None
        lowest_attention = float('inf')
        
        for pos in candidate_positions:
            attention_analysis = self.calculate_attention_from_position(pos, enemy_units, card_name)
            
            if attention_analysis['safe_placement'] and attention_analysis['attention_score'] < lowest_attention:
                lowest_attention = attention_analysis['attention_score']
                best_position = pos
        
        return best_position
    
    def _calculate_threat_level(self, enemy_name: str, distance: float) -> float:
        """
        Calcula nível de ameaça baseado no tipo de tropa e distância
        """
        base_threat = {
            'giant': 3.0,
            'pekka': 8.0,
            'knight': 5.0,
            'musketeer': 7.0,
            'archers': 5.0,
            'wizard': 7.0,
            'minions': 4.0,
            'baby_dragon': 6.0
        }.get(enemy_name, 4.0)
        
        # Quanto mais próximo, maior a ameaça
        distance_factor = max(0.1, 1.0 - (distance / 10.0))
        
        return base_threat * distance_factor
    
    def _generate_positioning_recommendations(self, card_name: str, 
                                            attracting_units: List[Dict]) -> List[str]:
        """
        Gera recomendações de posicionamento baseado nas tropas que vão reagir
        """
        recommendations = []
        
        if not attracting_units:
            return recommendations
        
        # Analisa tipos de tropas que vão reagir
        ground_threats = [u for u in attracting_units if u['unit'] in ['giant', 'knight', 'pekka']]
        air_threats = [u for u in attracting_units if u['unit'] in ['baby_dragon', 'minions']]
        ranged_threats = [u for u in attracting_units if u['unit'] in ['musketeer', 'archers', 'wizard']]
        
        # Recomendações específicas
        if ground_threats and card_name in ['archers', 'musketeer']:
            recommendations.append('place_behind_tank_protection')
        
        if ranged_threats and card_name in ['knight', 'giant']:
            recommendations.append('place_to_tank_ranged_damage')
        
        if air_threats and card_name in ['archers', 'musketeer']:
            recommendations.append('position_for_air_defense')
        
        return recommendations
    
    def analyze_unit_formation(self, units: List[Dict]) -> Dict:
        """
        Analisa formação de tropas para entender quem está na frente/atrás
        """
        if not units:
            return {'formation': 'empty', 'front_line': [], 'back_line': [], 'formation_strength': 0}
        
        # Ordena por posição Y (quem está mais à frente)
        sorted_units = sorted(units, key=lambda u: u['position'][1])
        
        formation_analysis = {
            'formation': 'unknown',
            'front_line': [],
            'back_line': [],
            'formation_strength': 0,
            'has_tank': False,
            'has_support': False,
            'formation_type': 'scattered'
        }
        
        # Identifica linha de frente (primeiros 30% das tropas)
        front_count = max(1, len(sorted_units) // 3)
        formation_analysis['front_line'] = sorted_units[:front_count]
        formation_analysis['back_line'] = sorted_units[front_count:]
        
        # Analisa tipo de formação
        front_units = [u['name'] for u in formation_analysis['front_line']]
        back_units = [u['name'] for u in formation_analysis['back_line']]
        
        # Detecta tanks na frente
        tank_units = ['giant', 'pekka', 'golem', 'knight']
        if any(unit in tank_units for unit in front_units):
            formation_analysis['has_tank'] = True
        
        # Detecta suporte atrás
        support_units = ['musketeer', 'archers', 'wizard', 'witch']
        if any(unit in support_units for unit in back_units):
            formation_analysis['has_support'] = True
        
        # Determina tipo de formação
        if formation_analysis['has_tank'] and formation_analysis['has_support']:
            formation_analysis['formation_type'] = 'tank_push'
            formation_analysis['formation_strength'] = 8
        elif formation_analysis['has_tank']:
            formation_analysis['formation_type'] = 'tank_only'
            formation_analysis['formation_strength'] = 6
        elif formation_analysis['has_support']:
            formation_analysis['formation_type'] = 'support_only'
            formation_analysis['formation_strength'] = 4
        else:
            formation_analysis['formation_type'] = 'scattered'
            formation_analysis['formation_strength'] = 2
        
        return formation_analysis

"""
Sistema de Validação de Matchups
Baseado em conhecimento profissional de Clash Royale
"""
from typing import Dict, List, Tuple, Optional
from loguru import logger


class MatchupValidator:
    def __init__(self):
        # Interações fundamentais baseadas em conhecimento profissional
        self.card_types = {
            'melee_high_damage': ['minipekka', 'pekka', 'prince'],
            'melee_tank': ['knight', 'giant', 'golem'],
            'ranged_single': ['musketeer', 'wizard', 'witch'],
            'ranged_multi': ['archers', 'dart_goblin'],
            'air_units': ['minions', 'baby_dragon', 'balloon'],
            'swarm_ground': ['skeleton_army', 'barbarians', 'goblin_gang'],
            'swarm_air': ['minion_horde', 'bats'],
            'buildings': ['cannon', 'tesla', 'inferno_tower'],
            'spells_damage': ['fireball', 'lightning', 'rocket'],
            'spells_utility': ['zap', 'arrows', 'freeze']
        }
        
        # Regras fundamentais de interação
        self.interaction_rules = {
            'melee_vs_ranged': {
                'rule': 'Melee wins if gets close, Ranged wins if maintains distance',
                'critical_distance': 3,  # tiles
                'positioning_rule': 'Ranged must stay 3+ tiles away from melee'
            },
            'air_vs_ground': {
                'rule': 'Air bypasses ground-only units',
                'advantage': 'air',
                'counter_requirement': 'air_targeting_unit'
            },
            'swarm_vs_single': {
                'rule': 'Swarm overwhelms single target, single target needs splash',
                'advantage': 'swarm',
                'counter_requirement': 'splash_damage'
            }
        }
        
        # Matchups críticos que NUNCA devem acontecer
        self.forbidden_matchups = {
            'musketeer_on_minipekka': {
                'reason': 'Mini Pekka one-shots Musketeer in melee',
                'correct_counter': 'musketeer_at_distance',
                'min_distance': 4
            },
            'archers_on_knight': {
                'reason': 'Knight has splash and more HP',
                'correct_counter': 'archers_at_distance',
                'min_distance': 3
            },
            'any_ranged_on_melee': {
                'reason': 'Melee units destroy ranged in close combat',
                'correct_counter': 'maintain_distance',
                'min_distance': 3
            }
        }
    
    def validate_card_placement(self, our_card: str, target_position: Tuple[int, int], 
                              enemy_units: List[Dict]) -> Dict:
        """Valida se posicionamento de carta é tático correto"""
        validation = {
            'is_valid': True,
            'confidence': 1.0,
            'warnings': [],
            'corrections': [],
            'reasoning': 'Standard placement'
        }
        
        try:
            target_x, target_y = target_position
            our_card_type = self._get_card_type(our_card)
            
            for enemy in enemy_units:
                enemy_name = enemy.get('name', '')
                enemy_pos = enemy.get('position', (0, 0))
                
                if len(enemy_pos) < 2:
                    continue
                
                enemy_x, enemy_y = enemy_pos
                distance = ((target_x - enemy_x)**2 + (target_y - enemy_y)**2)**0.5
                enemy_type = self._get_card_type(enemy_name)
                
                # VALIDAÇÃO CRÍTICA: Ranged vs Melee
                if our_card_type == 'ranged' and enemy_type == 'melee_damage':
                    if distance < 3:
                        validation['is_valid'] = False
                        validation['confidence'] = 0.1
                        validation['warnings'].append(f"🚫 CRITICAL: {our_card} too close to {enemy_name}")
                        validation['corrections'].append(f"Place {our_card} 4+ tiles away from {enemy_name}")
                        validation['reasoning'] = f"{enemy_name} will one-shot {our_card} in melee range"
                        
                        # Sugerir posição corrigida
                        safe_x = enemy_x + (4 if enemy_x < 9 else -4)
                        safe_y = enemy_y + 2
                        validation['suggested_position'] = (safe_x, safe_y)
                        
                        logger.error(f"🚫 INVALID PLACEMENT: {our_card} at {target_position} vs {enemy_name} at {enemy_pos}")
                        break
                
                # VALIDAÇÃO: Air units positioning
                elif our_card_type == 'air' and enemy_type in ['ranged', 'air_targeting']:
                    if distance < 2:
                        validation['warnings'].append(f"⚠️ {our_card} in range of {enemy_name}")
                        validation['confidence'] *= 0.7
                
                # VALIDAÇÃO: Tank positioning
                elif our_card_type == 'tank' and enemy_type == 'tank_killer':
                    if distance < 2:
                        validation['warnings'].append(f"⚠️ {our_card} will be focused by {enemy_name}")
                        validation['confidence'] *= 0.8
        
        except Exception as e:
            logger.debug(f"Error validating card placement: {e}")
        
        return validation
    
    def _get_card_type(self, card_name: str) -> str:
        """Determina tipo da carta para análise de matchup"""
        for card_type, cards in self.card_types.items():
            if card_name in cards:
                return card_type
        
        # Classificação baseada no nome se não estiver na lista
        if 'pekka' in card_name or card_name in ['prince', 'mega_knight']:
            return 'melee_damage'
        elif card_name in ['musketeer', 'wizard', 'witch', 'electro_wizard']:
            return 'ranged'
        elif card_name in ['giant', 'golem', 'royal_giant']:
            return 'tank'
        elif 'minion' in card_name or card_name in ['baby_dragon', 'balloon']:
            return 'air'
        
        return 'unknown'
    
    def suggest_counter_positioning(self, our_card: str, enemy_card: str, 
                                  enemy_position: Tuple[int, int]) -> Dict:
        """Sugere posicionamento correto para counter"""
        suggestion = {
            'position': enemy_position,
            'reasoning': 'Direct engagement',
            'success_probability': 0.5
        }
        
        try:
            enemy_x, enemy_y = enemy_position
            our_type = self._get_card_type(our_card)
            enemy_type = self._get_card_type(enemy_card)
            
            # Ranged vs Melee - manter distância
            if our_type == 'ranged' and enemy_type in ['melee_damage', 'melee_tank']:
                safe_x = enemy_x + (4 if enemy_x < 9 else -4)
                safe_y = enemy_y + 2
                suggestion['position'] = (safe_x, safe_y)
                suggestion['reasoning'] = f'{our_card} maintains safe distance from {enemy_card}'
                suggestion['success_probability'] = 0.8
                
            # Melee vs Ranged - ir direto
            elif our_type in ['melee_damage', 'melee_tank'] and enemy_type == 'ranged':
                suggestion['position'] = (enemy_x, enemy_y + 1)
                suggestion['reasoning'] = f'{our_card} engages {enemy_card} in melee'
                suggestion['success_probability'] = 0.9
                
            # Air vs Ground - posição acima
            elif our_type == 'air' and enemy_type not in ['air', 'air_targeting']:
                suggestion['position'] = (enemy_x, enemy_y - 1)
                suggestion['reasoning'] = f'{our_card} attacks from above'
                suggestion['success_probability'] = 0.85
                
        except Exception as e:
            logger.debug(f"Error suggesting counter positioning: {e}")
        
        return suggestion

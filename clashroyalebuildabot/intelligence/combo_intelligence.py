"""
Sistema de Inteligência de Combos
Analisa combos viáveis, calcula compensação e decide quando segurar elixir
"""
from typing import Dict, List, Tuple, Optional
from loguru import logger
import time


class ComboIntelligence:
    def __init__(self):
        # Definição de combos viáveis para nosso deck
        self.viable_combos = {
            'giant_push': {
                'cards': ['giant', 'musketeer'],
                'total_cost': 9,
                'min_elixir': 8,
                'effectiveness': 0.9,
                'description': 'Giant tank + Musketeer support',
                'timing': 'giant_first',
                'positioning': 'giant_bridge_musketeer_behind'
            },
            'giant_air_support': {
                'cards': ['giant', 'minions'],
                'total_cost': 8,
                'min_elixir': 7,
                'effectiveness': 0.85,
                'description': 'Giant tank + Minions air support',
                'timing': 'giant_first',
                'positioning': 'giant_bridge_minions_above'
            },
            'knight_counter_push': {
                'cards': ['knight', 'musketeer'],
                'total_cost': 7,
                'min_elixir': 6,
                'effectiveness': 0.8,
                'description': 'Knight tank + Musketeer support for counter-push',
                'timing': 'knight_first',
                'positioning': 'knight_front_musketeer_behind'
            },
            'minipekka_defense_counter': {
                'cards': ['minipekka', 'spear_goblins'],
                'total_cost': 6,
                'min_elixir': 5,
                'effectiveness': 0.75,
                'description': 'Mini Pekka defense + Spear Goblins counter',
                'timing': 'minipekka_first',
                'positioning': 'minipekka_defense_spears_bridge'
            },
            'fireball_cleanup': {
                'cards': ['fireball', 'knight'],
                'total_cost': 7,
                'min_elixir': 6,
                'effectiveness': 0.8,
                'description': 'Fireball clear + Knight counter-push',
                'timing': 'fireball_first',
                'positioning': 'fireball_clear_knight_bridge'
            },
            'cycle_pressure': {
                'cards': ['spear_goblins', 'archers'],
                'total_cost': 5,
                'min_elixir': 4,
                'effectiveness': 0.6,
                'description': 'Fast cycle pressure',
                'timing': 'simultaneous',
                'positioning': 'spears_bridge_archers_support'
            },
            'heavy_defense': {
                'cards': ['minipekka', 'knight'],
                'total_cost': 7,
                'min_elixir': 6,
                'effectiveness': 0.85,
                'description': 'Heavy defensive combo',
                'timing': 'minipekka_first',
                'positioning': 'minipekka_defense_knight_support'
            }
        }
        
        # Análise de situações onde combos compensam
        self.combo_scenarios = {
            'enemy_spent_heavy': {
                'condition': 'enemy_elixir < 3',
                'recommended_combos': ['giant_push', 'giant_air_support'],
                'reasoning': 'Enemy low on elixir - perfect for heavy push'
            },
            'enemy_used_spell': {
                'condition': 'enemy_just_used_spell',
                'recommended_combos': ['knight_counter_push', 'minipekka_defense_counter'],
                'reasoning': 'Enemy used spell - counter-push opportunity'
            },
            'enemy_has_heavy_tank': {
                'condition': 'enemy_has_giant_or_pekka',
                'recommended_combos': ['heavy_defense', 'fireball_cleanup'],
                'reasoning': 'Enemy has heavy tank - need strong defense'
            },
            'we_have_elixir_advantage': {
                'condition': 'our_elixir > enemy_elixir + 2',
                'recommended_combos': ['giant_push', 'giant_air_support'],
                'reasoning': 'Elixir advantage - time for heavy push'
            },
            'enemy_cycling_fast': {
                'condition': 'enemy_cycle_speed > 2.5',
                'recommended_combos': ['cycle_pressure', 'knight_counter_push'],
                'reasoning': 'Enemy cycling fast - match their speed'
            }
        }
        
        # Histórico de combos usados
        self.combo_history = []
        self.last_combo_time = 0
        
    def analyze_combo_opportunity(self, game_state: Dict, available_cards: List[str]) -> Dict:
        """Analisa se há oportunidade para um combo viável"""
        analysis = {
            'should_combo': False,
            'recommended_combo': None,
            'reasoning': [],
            'wait_for_elixir': False,
            'immediate_play': None
        }
        
        try:
            our_elixir = game_state.get('our_elixir', 0)
            enemy_elixir = game_state.get('enemy_elixir', 10)
            enemy_just_used = game_state.get('enemy_last_card', '')
            enemy_has_tank = game_state.get('enemy_has_heavy_tank', False)
            
            # Verificar se temos cartas para combos
            available_combos = self._get_available_combos(available_cards, our_elixir)
            
            if not available_combos:
                analysis['reasoning'].append("No viable combos available with current cards/elixir")
                return analysis
            
            # Analisar cenários
            scenario_analysis = self._analyze_scenarios(game_state)
            
            # Encontrar melhor combo para o cenário
            best_combo = self._find_best_combo(available_combos, scenario_analysis, game_state)
            
            if best_combo:
                combo_info = self.viable_combos[best_combo]
                
                # Verificar se compensa esperar
                if our_elixir < combo_info['min_elixir']:
                    analysis['wait_for_elixir'] = True
                    analysis['reasoning'].append(f"Waiting for {combo_info['min_elixir']} elixir to execute {best_combo}")
                    analysis['reasoning'].append(f"Current: {our_elixir}, Need: {combo_info['min_elixir']}")
                else:
                    analysis['should_combo'] = True
                    analysis['recommended_combo'] = best_combo
                    analysis['reasoning'].append(f"Executing {best_combo}: {combo_info['description']}")
                    analysis['reasoning'].append(f"Effectiveness: {combo_info['effectiveness']:.1%}")
                    
                    # Verificar se há carta imediata para jogar
                    first_card = combo_info['cards'][0]
                    if first_card in available_cards:
                        analysis['immediate_play'] = first_card
                        analysis['reasoning'].append(f"Playing {first_card} first as per combo timing")
            
            # Adicionar raciocínio do cenário
            for scenario, info in scenario_analysis.items():
                if info['applies']:
                    analysis['reasoning'].append(f"Scenario: {scenario} - {info['reasoning']}")
            
        except Exception as e:
            logger.debug(f"Error analyzing combo opportunity: {e}")
            analysis['reasoning'].append(f"Error in analysis: {e}")
        
        return analysis
    
    def _get_available_combos(self, available_cards: List[str], our_elixir: int) -> List[str]:
        """Retorna combos disponíveis com as cartas atuais"""
        available_combos = []
        
        for combo_name, combo_info in self.viable_combos.items():
            # Verificar se temos as cartas necessárias
            has_cards = all(card in available_cards for card in combo_info['cards'])
            
            # Verificar se temos elixir suficiente
            has_elixir = our_elixir >= combo_info['min_elixir']
            
            if has_cards and has_elixir:
                available_combos.append(combo_name)
        
        return available_combos
    
    def _analyze_scenarios(self, game_state: Dict) -> Dict:
        """Analisa quais cenários se aplicam à situação atual"""
        scenarios = {}
        
        our_elixir = game_state.get('our_elixir', 10)
        enemy_elixir = game_state.get('enemy_elixir', 10)
        enemy_last_card = game_state.get('enemy_last_card', '')
        enemy_has_tank = game_state.get('enemy_has_heavy_tank', False)
        
        # Cenário: Inimigo gastou muito elixir
        if enemy_elixir < 3:
            scenarios['enemy_spent_heavy'] = {
                'applies': True,
                'reasoning': f'Enemy low on elixir ({enemy_elixir}) - perfect for heavy push'
            }
        else:
            scenarios['enemy_spent_heavy'] = {'applies': False}
        
        # Cenário: Inimigo usou spell
        spell_cards = ['fireball', 'lightning', 'poison', 'rocket', 'arrows']
        if enemy_last_card in spell_cards:
            scenarios['enemy_used_spell'] = {
                'applies': True,
                'reasoning': f'Enemy used {enemy_last_card} - counter-push opportunity'
            }
        else:
            scenarios['enemy_used_spell'] = {'applies': False}
        
        # Cenário: Inimigo tem tank pesado
        if enemy_has_tank:
            scenarios['enemy_has_heavy_tank'] = {
                'applies': True,
                'reasoning': 'Enemy has heavy tank - need strong defense'
            }
        else:
            scenarios['enemy_has_heavy_tank'] = {'applies': False}
        
        # Cenário: Temos vantagem de elixir
        if our_elixir > enemy_elixir + 2:
            scenarios['we_have_elixir_advantage'] = {
                'applies': True,
                'reasoning': f'Elixir advantage ({our_elixir} vs {enemy_elixir}) - time for heavy push'
            }
        else:
            scenarios['we_have_elixir_advantage'] = {'applies': False}
        
        return scenarios
    
    def _find_best_combo(self, available_combos: List[str], scenarios: Dict, game_state: Dict) -> Optional[str]:
        """Encontra o melhor combo baseado nos cenários"""
        best_combo = None
        best_score = 0
        
        for combo_name in available_combos:
            combo_info = self.viable_combos[combo_name]
            score = combo_info['effectiveness']
            
            # Bônus baseado em cenários aplicáveis
            for scenario_name, scenario_info in scenarios.items():
                if scenario_info['applies']:
                    scenario_config = self.combo_scenarios.get(scenario_name, {})
                    if combo_name in scenario_config.get('recommended_combos', []):
                        score += 0.2  # Bônus por ser recomendado para o cenário
            
            # Penalidade por combo recente
            if self._was_combo_used_recently(combo_name):
                score -= 0.3
            
            # Bônus por ser combo pesado em situação favorável
            if combo_info['total_cost'] >= 8 and game_state.get('our_elixir', 0) >= 9:
                score += 0.1
            
            if score > best_score:
                best_score = score
                best_combo = combo_name
        
        return best_combo
    
    def _was_combo_used_recently(self, combo_name: str) -> bool:
        """Verifica se um combo foi usado recentemente"""
        current_time = time.time()
        recent_threshold = 30  # 30 segundos
        
        for combo_record in self.combo_history:
            if (combo_record['combo'] == combo_name and 
                current_time - combo_record['timestamp'] < recent_threshold):
                return True
        
        return False
    
    def record_combo_execution(self, combo_name: str, success: bool):
        """Registra execução de um combo"""
        record = {
            'combo': combo_name,
            'timestamp': time.time(),
            'success': success
        }
        
        self.combo_history.append(record)
        
        # Manter apenas os últimos 10 combos
        if len(self.combo_history) > 10:
            self.combo_history.pop(0)
    
    def should_wait_for_combo(self, game_state: Dict, available_cards: List[str]) -> Dict:
        """Decide se deve esperar para montar um combo"""
        decision = {
            'should_wait': False,
            'reasoning': [],
            'wait_time_estimate': 0,
            'alternative_play': None
        }
        
        try:
            our_elixir = game_state.get('our_elixir', 0)
            
            # Verificar se há combos viáveis
            available_combos = self._get_available_combos(available_cards, our_elixir)
            
            if not available_combos:
                decision['reasoning'].append("No viable combos - don't wait")
                return decision
            
            # Encontrar o melhor combo
            scenario_analysis = self._analyze_scenarios(game_state)
            best_combo = self._find_best_combo(available_combos, scenario_analysis, game_state)
            
            if best_combo:
                combo_info = self.viable_combos[best_combo]
                
                # Se temos elixir suficiente, não esperar
                if our_elixir >= combo_info['min_elixir']:
                    decision['reasoning'].append(f"Have enough elixir ({our_elixir}) for {best_combo}")
                    return decision
                
                # Calcular tempo de espera
                elixir_needed = combo_info['min_elixir'] - our_elixir
                wait_time = elixir_needed * 2.8  # ~2.8 segundos por elixir
                
                # Decidir se vale a pena esperar
                if wait_time <= 8 and combo_info['effectiveness'] >= 0.8:
                    decision['should_wait'] = True
                    decision['wait_time_estimate'] = wait_time
                    decision['reasoning'].append(f"Worth waiting {wait_time:.1f}s for {best_combo}")
                    decision['reasoning'].append(f"Effectiveness: {combo_info['effectiveness']:.1%}")
                else:
                    decision['reasoning'].append(f"Not worth waiting {wait_time:.1f}s for {best_combo}")
                    # Sugerir jogada alternativa
                    decision['alternative_play'] = self._suggest_alternative_play(available_cards, our_elixir)
            
        except Exception as e:
            logger.debug(f"Error in should_wait_for_combo: {e}")
            decision['reasoning'].append(f"Error: {e}")
        
        return decision
    
    def _suggest_alternative_play(self, available_cards: List[str], our_elixir: int) -> Optional[str]:
        """Sugere uma jogada alternativa quando não vale esperar"""
        # Priorizar cartas baratas para cycle
        cheap_cards = ['spear_goblins', 'archers', 'knight']
        
        for card in cheap_cards:
            if card in available_cards and self._estimate_card_cost(card) <= our_elixir:
                return card
        
        # Se não há cartas baratas, sugerir qualquer carta disponível
        for card in available_cards:
            if self._estimate_card_cost(card) <= our_elixir:
                return card
        
        return None
    
    def _estimate_card_cost(self, card_name: str) -> int:
        """Estima o custo de elixir de uma carta"""
        costs = {
            'giant': 5, 'minipekka': 4, 'musketeer': 4, 'knight': 3,
            'archers': 3, 'minions': 3, 'fireball': 4, 'spear_goblins': 2
        }
        return costs.get(card_name, 3)
    
    def get_combo_timing_instructions(self, combo_name: str) -> Dict:
        """Retorna instruções de timing para um combo"""
        if combo_name not in self.viable_combos:
            return {}
        
        combo_info = self.viable_combos[combo_name]
        
        timing_instructions = {
            'combo': combo_name,
            'cards': combo_info['cards'],
            'timing': combo_info['timing'],
            'positioning': combo_info['positioning'],
            'instructions': []
        }
        
        if combo_info['timing'] == 'giant_first':
            timing_instructions['instructions'].extend([
                "1. Play Giant at bridge first",
                "2. Wait 1-2 seconds for Giant to start moving",
                "3. Play support unit behind Giant",
                "4. Ensure support doesn't outrun tank"
            ])
        elif combo_info['timing'] == 'knight_first':
            timing_instructions['instructions'].extend([
                "1. Play Knight in front",
                "2. Immediately play support unit behind",
                "3. Use for counter-push after defense"
            ])
        elif combo_info['timing'] == 'minipekka_first':
            timing_instructions['instructions'].extend([
                "1. Play Mini Pekka for defense",
                "2. After defense, play support for counter-push",
                "3. Time support to arrive after Mini Pekka"
            ])
        elif combo_info['timing'] == 'fireball_first':
            timing_instructions['instructions'].extend([
                "1. Use Fireball to clear enemy units",
                "2. Immediately play counter-push unit",
                "3. Take advantage of cleared field"
            ])
        elif combo_info['timing'] == 'simultaneous':
            timing_instructions['instructions'].extend([
                "1. Play both units quickly",
                "2. Use for fast pressure",
                "3. Don't wait between plays"
            ])
        
        return timing_instructions

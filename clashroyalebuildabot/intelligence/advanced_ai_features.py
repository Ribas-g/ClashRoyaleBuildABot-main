"""
Recursos Avançados de IA para Clash Royale Bot
Implementa funcionalidades de IA de nível profissional
"""
from typing import Dict, List, Tuple, Optional
from loguru import logger
import time
import random


class AdvancedAIFeatures:
    def __init__(self):
        self.game_phase = 'early_game'
        self.opponent_patterns = {}
        self.our_performance_history = []
        self.adaptation_strategies = {
            'aggressive_opponent': 'defensive_counter',
            'defensive_opponent': 'pressure_build',
            'cycle_opponent': 'elixir_advantage',
            'spell_heavy_opponent': 'bait_spells'
        }
        
        # Análise de padrões do oponente
        self.opponent_analysis = {
            'play_style': 'unknown',
            'favorite_cards': [],
            'response_patterns': {},
            'weaknesses': [],
            'strengths': []
        }
        
        # Estratégias adaptativas
        self.adaptive_strategies = {
            'early_game': {
                'conservative': 'wait_for_advantage',
                'aggressive': 'pressure_early',
                'balanced': 'establish_position'
            },
            'mid_game': {
                'winning': 'maintain_pressure',
                'losing': 'defensive_recovery',
                'even': 'find_advantage'
            },
            'late_game': {
                'winning': 'finish_strong',
                'losing': 'desperate_plays',
                'even': 'clutch_plays'
            }
        }
    
    def analyze_opponent_patterns(self, game_history: List[Dict]) -> Dict:
        """Analisa padrões do oponente para adaptação"""
        analysis = {
            'play_style': 'unknown',
            'favorite_cards': [],
            'response_patterns': {},
            'weaknesses': [],
            'strengths': [],
            'adaptation_needed': False
        }
        
        try:
            if len(game_history) < 5:
                return analysis
            
            # Analisar cartas mais usadas
            card_usage = {}
            for turn in game_history:
                opponent_card = turn.get('opponent_card')
                if opponent_card:
                    card_usage[opponent_card] = card_usage.get(opponent_card, 0) + 1
            
            # Identificar cartas favoritas
            favorite_cards = sorted(card_usage.items(), key=lambda x: x[1], reverse=True)[:3]
            analysis['favorite_cards'] = [card[0] for card in favorite_cards]
            
            # Analisar padrões de resposta
            response_patterns = {}
            for i, turn in enumerate(game_history[:-1]):
                our_card = turn.get('our_card')
                next_opponent_card = game_history[i+1].get('opponent_card')
                if our_card and next_opponent_card:
                    if our_card not in response_patterns:
                        response_patterns[our_card] = []
                    response_patterns[our_card].append(next_opponent_card)
            
            analysis['response_patterns'] = response_patterns
            
            # Determinar estilo de jogo
            if len(favorite_cards) > 0:
                if 'giant' in favorite_cards or 'pekka' in favorite_cards:
                    analysis['play_style'] = 'aggressive'
                elif 'fireball' in favorite_cards or 'lightning' in favorite_cards:
                    analysis['play_style'] = 'spell_heavy'
                elif 'spear_goblins' in favorite_cards or 'skeletons' in favorite_cards:
                    analysis['play_style'] = 'cycle'
                else:
                    analysis['play_style'] = 'balanced'
            
            # Identificar fraquezas e forças
            analysis['weaknesses'] = self._identify_opponent_weaknesses(analysis)
            analysis['strengths'] = self._identify_opponent_strengths(analysis)
            
            # Determinar se adaptação é necessária
            analysis['adaptation_needed'] = len(analysis['response_patterns']) > 2
            
        except Exception as e:
            logger.debug(f"Error analyzing opponent patterns: {e}")
        
        return analysis
    
    def _identify_opponent_weaknesses(self, analysis: Dict) -> List[str]:
        """Identifica fraquezas do oponente"""
        weaknesses = []
        
        favorite_cards = analysis.get('favorite_cards', [])
        
        # Se usa muitas cartas caras, vulnerável a cycle
        expensive_cards = ['giant', 'pekka', 'golem', 'lightning']
        if any(card in favorite_cards for card in expensive_cards):
            weaknesses.append('slow_cycle')
        
        # Se usa muitas spells, vulnerável a bait
        spell_cards = ['fireball', 'lightning', 'rocket']
        if any(card in favorite_cards for card in spell_cards):
            weaknesses.append('spell_bait')
        
        # Se não tem defesa aérea
        air_defense = ['archers', 'musketeer', 'baby_dragon']
        if not any(card in favorite_cards for card in air_defense):
            weaknesses.append('weak_air_defense')
        
        return weaknesses
    
    def _identify_opponent_strengths(self, analysis: Dict) -> List[str]:
        """Identifica forças do oponente"""
        strengths = []
        
        favorite_cards = analysis.get('favorite_cards', [])
        
        # Se tem tank forte
        if 'giant' in favorite_cards or 'pekka' in favorite_cards:
            strengths.append('strong_tank')
        
        # Se tem spells poderosos
        if 'fireball' in favorite_cards or 'lightning' in favorite_cards:
            strengths.append('strong_spells')
        
        # Se tem cycle rápido
        if 'spear_goblins' in favorite_cards or 'skeletons' in favorite_cards:
            strengths.append('fast_cycle')
        
        return strengths
    
    def generate_adaptive_strategy(self, opponent_analysis: Dict, game_phase: str, 
                                 our_performance: str) -> Dict:
        """Gera estratégia adaptativa baseada na análise"""
        strategy = {
            'primary_goal': 'standard_play',
            'secondary_goals': [],
            'card_priorities': [],
            'avoid_cards': [],
            'special_tactics': [],
            'reasoning': []
        }
        
        try:
            play_style = opponent_analysis.get('play_style', 'unknown')
            weaknesses = opponent_analysis.get('weaknesses', [])
            strengths = opponent_analysis.get('strengths', [])
            
            # Estratégia baseada no estilo do oponente
            if play_style == 'aggressive':
                strategy['primary_goal'] = 'defensive_counter'
                strategy['secondary_goals'].append('elixir_advantage')
                strategy['card_priorities'].extend(['minipekka', 'knight'])
                strategy['special_tactics'].append('bait_aggressive_plays')
                strategy['reasoning'].append("Opponent is aggressive - focus on defense and counter-attacks")
            
            elif play_style == 'spell_heavy':
                strategy['primary_goal'] = 'spell_bait'
                strategy['secondary_goals'].append('pressure_with_swarms')
                strategy['card_priorities'].extend(['spear_goblins', 'minions'])
                strategy['avoid_cards'].extend(['musketeer', 'archers'])
                strategy['special_tactics'].append('bait_spells_with_cheap_cards')
                strategy['reasoning'].append("Opponent uses many spells - bait them with cheap cards")
            
            elif play_style == 'cycle':
                strategy['primary_goal'] = 'pressure_build'
                strategy['secondary_goals'].append('maintain_advantage')
                strategy['card_priorities'].extend(['giant', 'musketeer'])
                strategy['special_tactics'].append('pressure_with_expensive_cards')
                strategy['reasoning'].append("Opponent cycles fast - pressure with expensive cards")
            
            # Adaptação baseada em fraquezas
            if 'weak_air_defense' in weaknesses:
                strategy['card_priorities'].append('minions')
                strategy['special_tactics'].append('air_pressure')
                strategy['reasoning'].append("Opponent weak to air - use minions")
            
            if 'slow_cycle' in weaknesses:
                strategy['secondary_goals'].append('fast_cycle')
                strategy['card_priorities'].append('spear_goblins')
                strategy['reasoning'].append("Opponent has slow cycle - cycle faster")
            
            # Adaptação baseada em forças
            if 'strong_tank' in strengths:
                strategy['card_priorities'].append('minipekka')
                strategy['reasoning'].append("Opponent has strong tanks - prioritize Mini Pekka")
            
            if 'strong_spells' in strengths:
                strategy['avoid_cards'].extend(['musketeer', 'archers'])
                strategy['reasoning'].append("Opponent has strong spells - avoid expensive ranged units")
            
            # Adaptação baseada na fase do jogo
            if game_phase == 'late_game':
                if our_performance == 'losing':
                    strategy['primary_goal'] = 'desperate_plays'
                    strategy['special_tactics'].append('all_in_attacks')
                    strategy['reasoning'].append("Late game and losing - need desperate plays")
                elif our_performance == 'winning':
                    strategy['primary_goal'] = 'safe_play'
                    strategy['special_tactics'].append('defensive_positioning')
                    strategy['reasoning'].append("Late game and winning - play safe")
            
        except Exception as e:
            logger.debug(f"Error generating adaptive strategy: {e}")
        
        return strategy
    
    def predict_opponent_next_play(self, our_action: Dict, opponent_patterns: Dict) -> List[Dict]:
        """Prediz a próxima jogada do oponente baseada em padrões"""
        predictions = []
        
        try:
            our_card = our_action.get('card', '')
            response_patterns = opponent_patterns.get('response_patterns', {})
            
            # Verificar padrões históricos
            if our_card in response_patterns:
                historical_responses = response_patterns[our_card]
                
                # Contar frequência de cada resposta
                response_counts = {}
                for response in historical_responses:
                    response_counts[response] = response_counts.get(response, 0) + 1
                
                # Ordenar por frequência
                sorted_responses = sorted(response_counts.items(), key=lambda x: x[1], reverse=True)
                
                for response, count in sorted_responses[:3]:  # Top 3 mais prováveis
                    probability = count / len(historical_responses)
                    predictions.append({
                        'card': response,
                        'probability': probability,
                        'reason': f'Historical pattern: {count}/{len(historical_responses)} times'
                    })
            
            # Predições baseadas em conhecimento geral
            general_predictions = self._get_general_predictions(our_card)
            predictions.extend(general_predictions)
            
            # Ordenar por probabilidade
            predictions.sort(key=lambda x: x['probability'], reverse=True)
            
        except Exception as e:
            logger.debug(f"Error predicting opponent next play: {e}")
        
        return predictions
    
    def _get_general_predictions(self, our_card: str) -> List[Dict]:
        """Predições gerais baseadas em conhecimento do jogo"""
        predictions = []
        
        # Predições baseadas em counters conhecidos
        if our_card == 'giant':
            predictions.extend([
                {'card': 'minipekka', 'probability': 0.6, 'reason': 'Standard tank counter'},
                {'card': 'pekka', 'probability': 0.3, 'reason': 'Heavy tank counter'},
                {'card': 'inferno_tower', 'probability': 0.2, 'reason': 'Building counter'}
            ])
        elif our_card == 'musketeer':
            predictions.extend([
                {'card': 'fireball', 'probability': 0.5, 'reason': 'Spell counter'},
                {'card': 'knight', 'probability': 0.4, 'reason': 'Melee counter'}
            ])
        elif our_card == 'minipekka':
            predictions.extend([
                {'card': 'skeleton_army', 'probability': 0.4, 'reason': 'Swarm counter'},
                {'card': 'knight', 'probability': 0.3, 'reason': 'Tank counter'}
            ])
        
        return predictions
    
    def calculate_risk_reward_ratio(self, action: Dict, game_state: Dict) -> float:
        """Calcula a razão risco/recompensa de uma ação"""
        try:
            card_name = action.get('card', '')
            card_cost = self._estimate_card_cost(card_name)
            current_elixir = game_state.get('our_elixir', 10)
            
            # Fatores de risco
            risk_factors = 0
            
            # Risco de elixir baixo
            remaining_elixir = current_elixir - card_cost
            if remaining_elixir < 3:
                risk_factors += 2
            elif remaining_elixir < 5:
                risk_factors += 1
            
            # Risco de carta cara
            if card_cost >= 5:
                risk_factors += 1
            
            # Risco de carta vulnerável
            vulnerable_cards = ['musketeer', 'archers', 'wizard']
            if card_name in vulnerable_cards:
                risk_factors += 1
            
            # Fatores de recompensa
            reward_factors = 0
            
            # Recompensa por carta de counter
            if self._is_counter_card(card_name, game_state.get('enemy_threats', [])):
                reward_factors += 2
            
            # Recompensa por carta de pressão
            if self._is_offensive_card(card_name):
                reward_factors += 1
            
            # Recompensa por carta barata
            if card_cost <= 3:
                reward_factors += 1
            
            # Calcular razão (recompensa / risco)
            if risk_factors == 0:
                risk_factors = 1  # Evitar divisão por zero
            
            ratio = reward_factors / risk_factors
            
            return ratio
            
        except Exception as e:
            logger.debug(f"Error calculating risk/reward ratio: {e}")
            return 1.0  # Valor neutro em caso de erro
    
    def _estimate_card_cost(self, card_name: str) -> int:
        """Estima o custo de elixir de uma carta"""
        costs = {
            'giant': 5, 'minipekka': 4, 'musketeer': 4, 'knight': 3,
            'archers': 3, 'minions': 3, 'fireball': 4, 'spear_goblins': 2
        }
        return costs.get(card_name, 3)
    
    def _is_counter_card(self, card_name: str, enemy_threats: List[str]) -> bool:
        """Verifica se uma carta é counter para as ameaças atuais"""
        counter_matrix = {
            'minipekka': ['giant', 'pekka', 'golem'],
            'knight': ['musketeer', 'archers', 'wizard'],
            'fireball': ['musketeer', 'wizard', 'witch'],
            'musketeer': ['baby_dragon', 'minions', 'balloon']
        }
        
        for threat in enemy_threats:
            if threat in counter_matrix.get(card_name, []):
                return True
        
        return False
    
    def _is_offensive_card(self, card_name: str) -> bool:
        """Verifica se uma carta é ofensiva"""
        offensive_cards = ['giant', 'musketeer', 'archers', 'minions']
        return card_name in offensive_cards

"""
Sistema de Pensamento Estratégico
Implementa lógica de "turnos" e análise de consequências
"""
from typing import Dict, List, Tuple, Optional
from loguru import logger
import time
from clashroyalebuildabot.knowledge_base import knowledge_base


class StrategicThinking:
    def __init__(self):
        self.turn_history = []
        self.opponent_reaction_predictions = {}
        self.strategic_goals = {
            'early_game': 'establish_elixir_advantage',
            'mid_game': 'create_pressure_and_defend',
            'late_game': 'finish_with_advantage'
        }
        
        # Integração com o banco de dados de estratégias
        self.game_phase_strategies = {}
        self.prediction_strategies = {}
        self.advanced_tactics = {}
        self._load_strategies_from_database()
        
        # Análise de consequências de cada ação
        self.action_consequences = {
            'giant_placement': {
                'opponent_likely_responses': ['minipekka', 'pekka', 'inferno_tower'],
                'our_counter_options': ['musketeer', 'archers', 'fireball'],
                'elixir_advantage': -5,  # Giant custa 5
                'pressure_created': 'high',
                'vulnerability': 'air_attack'
            },
            'musketeer_placement': {
                'opponent_likely_responses': ['fireball', 'lightning', 'knight'],
                'our_counter_options': ['knight', 'minipekka'],
                'elixir_advantage': -4,
                'pressure_created': 'medium',
                'vulnerability': 'spells'
            },
            'fireball_usage': {
                'opponent_likely_responses': ['counter_push', 'cycle'],
                'our_counter_options': ['defend_counter_push'],
                'elixir_advantage': -4,
                'pressure_created': 'defensive',
                'vulnerability': 'low_elixir'
            }
        }
    
    def analyze_turn_consequences(self, proposed_action: Dict, game_state: Dict) -> Dict:
        """Analisa as consequências de uma ação proposta"""
        analysis = {
            'action': proposed_action,
            'immediate_impact': {},
            'opponent_reactions': [],
            'our_counters': [],
            'elixir_impact': 0,
            'risk_level': 'low',
            'recommendation': 'proceed',
            'reasoning': []
        }
        
        try:
            action_type = proposed_action.get('type', 'unknown')
            card_name = proposed_action.get('card', 'unknown')
            
            # Análise imediata
            analysis['immediate_impact'] = self._analyze_immediate_impact(action_type, card_name, proposed_action)
            
            # Predição de reações do oponente
            analysis['opponent_reactions'] = self._predict_opponent_reactions(action_type, card_name, game_state)
            
            # Nossas opções de counter
            analysis['our_counters'] = self._identify_our_counters(analysis['opponent_reactions'], game_state)
            
            # Impacto no elixir
            analysis['elixir_impact'] = self._calculate_elixir_impact(card_name, game_state)
            
            # Análise de risco
            analysis['risk_level'] = self._assess_risk_level(analysis)
            
            # Recomendação final
            analysis['recommendation'] = self._make_recommendation(analysis)
            
            # Raciocínio detalhado
            analysis['reasoning'] = self._generate_reasoning(analysis)
            
        except Exception as e:
            logger.debug(f"Error analyzing turn consequences: {e}")
        
        return analysis
    
    def _load_strategies_from_database(self):
        """Carrega estratégias do banco de dados"""
        try:
            self.game_phase_strategies = {
                'opening': knowledge_base.get_strategy_for_game_phase('opening'),
                'mid_game': knowledge_base.get_strategy_for_game_phase('mid_game'),
                'late_game': knowledge_base.get_strategy_for_game_phase('late_game')
            }
            self.prediction_strategies = knowledge_base.get_prediction_strategies()
            self.advanced_tactics = knowledge_base.get_advanced_tactics()
            
            logger.info("Estratégias carregadas do banco de dados")
        except Exception as e:
            logger.warning(f"Erro ao carregar estratégias: {e}")
    
    def get_strategy_for_current_phase(self, game_state: Dict) -> Dict:
        """Retorna estratégia para a fase atual do jogo"""
        game_time = game_state.get('game_time', 0)
        
        if game_time < 60:  # Primeiro minuto
            phase = 'opening'
        elif game_time < 180:  # Primeiros 3 minutos
            phase = 'mid_game'
        else:  # Último minuto
            phase = 'late_game'
        
        return self.game_phase_strategies.get(phase, {})
    
    def get_recommended_moves_for_phase(self, game_state: Dict) -> List[Dict]:
        """Retorna movimentos recomendados para a fase atual"""
        phase_strategy = self.get_strategy_for_current_phase(game_state)
        recommended_moves = []
        
        for strategy_name, strategy_data in phase_strategy.items():
            moves = knowledge_base.get_strategy_moves(strategy_name, game_state)
            recommended_moves.extend(moves)
        
        return recommended_moves
    
    def get_prediction_based_strategy(self, enemy_cards_played: List[str], our_deck: List[str]) -> Dict:
        """Retorna estratégia baseada em predição do deck inimigo"""
        return knowledge_base.get_prediction_strategy(enemy_cards_played, our_deck)
    
    def get_advanced_tactic_moves(self, tactic_name: str, game_state: Dict) -> List[Dict]:
        """Retorna movimentos para uma tática avançada"""
        return knowledge_base.get_strategy_moves(tactic_name, game_state)
    
    def infer_game_state_from_database(self, game_state: Dict) -> str:
        """Inferência de estado usando regras do banco de dados"""
        return knowledge_base.infer_game_state(game_state)
    
    def _analyze_immediate_impact(self, action_type: str, card_name: str, action: Dict) -> Dict:
        """Analisa o impacto imediato da ação"""
        impact = {
            'pressure_created': 'none',
            'defense_provided': 'none',
            'elixir_spent': self._estimate_card_cost(card_name),
            'positioning_quality': 'unknown'
        }
        
        if action_type == 'offensive':
            if card_name == 'giant':
                impact['pressure_created'] = 'high'
                impact['positioning_quality'] = 'tank_leads'
            elif card_name in ['musketeer', 'archers']:
                impact['pressure_created'] = 'medium'
                impact['positioning_quality'] = 'support_behind'
        
        elif action_type == 'defensive':
            if card_name == 'minipekka':
                impact['defense_provided'] = 'high'
                impact['positioning_quality'] = 'direct_counter'
            elif card_name == 'knight':
                impact['defense_provided'] = 'medium'
                impact['positioning_quality'] = 'tank_distraction'
        
        elif action_type == 'spell':
            if card_name == 'fireball':
                impact['defense_provided'] = 'area_clear'
                impact['positioning_quality'] = 'group_targeting'
        
        return impact
    
    def _predict_opponent_reactions(self, action_type: str, card_name: str, game_state: Dict) -> List[Dict]:
        """Prediz as reações mais prováveis do oponente"""
        reactions = []
        
        # Baseado no tipo de ação
        if action_type == 'offensive':
            if card_name == 'giant':
                reactions.extend([
                    {'card': 'minipekka', 'probability': 0.7, 'reason': 'Direct tank counter'},
                    {'card': 'pekka', 'probability': 0.3, 'reason': 'Heavy tank counter'},
                    {'card': 'inferno_tower', 'probability': 0.2, 'reason': 'Building counter'}
                ])
            elif card_name in ['musketeer', 'archers']:
                reactions.extend([
                    {'card': 'fireball', 'probability': 0.6, 'reason': 'Spell counter'},
                    {'card': 'knight', 'probability': 0.4, 'reason': 'Melee counter'}
                ])
        
        elif action_type == 'defensive':
            if card_name == 'minipekka':
                reactions.extend([
                    {'card': 'skeleton_army', 'probability': 0.5, 'reason': 'Swarm counter'},
                    {'card': 'fireball', 'probability': 0.3, 'reason': 'Spell counter'}
                ])
        
        # Filtrar por probabilidade
        high_prob_reactions = [r for r in reactions if r['probability'] > 0.4]
        
        return high_prob_reactions
    
    def _identify_our_counters(self, opponent_reactions: List[Dict], game_state: Dict) -> List[Dict]:
        """Identifica nossas opções de counter para as reações previstas"""
        counters = []
        
        for reaction in opponent_reactions:
            opponent_card = reaction['card']
            
            # Mapear counters baseado em conhecimento profissional
            if opponent_card == 'minipekka':
                counters.append({
                    'our_card': 'knight',
                    'reasoning': 'Knight can tank Mini Pekka damage',
                    'effectiveness': 0.8
                })
            elif opponent_card == 'fireball':
                counters.append({
                    'our_card': 'wait',
                    'reasoning': 'Wait for elixir advantage after Fireball',
                    'effectiveness': 0.9
                })
            elif opponent_card == 'skeleton_army':
                counters.append({
                    'our_card': 'fireball',
                    'reasoning': 'Fireball clears swarm effectively',
                    'effectiveness': 0.9
                })
        
        return counters
    
    def _calculate_elixir_impact(self, card_name: str, game_state: Dict) -> int:
        """Calcula o impacto da ação no elixir"""
        card_cost = self._estimate_card_cost(card_name)
        current_elixir = game_state.get('our_elixir', 10)
        
        # Se vai ficar com pouco elixir, é arriscado
        remaining_elixir = current_elixir - card_cost
        
        if remaining_elixir < 3:
            return -2  # Penalidade por ficar com pouco elixir
        elif remaining_elixir < 5:
            return -1  # Penalidade menor
        
        return 0  # Impacto neutro
    
    def _assess_risk_level(self, analysis: Dict) -> str:
        """Avalia o nível de risco da ação"""
        risk_factors = 0
        
        # Fatores de risco
        if analysis['elixir_impact'] < -1:
            risk_factors += 1
        
        if len(analysis['opponent_reactions']) > 2:
            risk_factors += 1
        
        if not analysis['our_counters']:
            risk_factors += 1
        
        if risk_factors == 0:
            return 'low'
        elif risk_factors == 1:
            return 'medium'
        else:
            return 'high'
    
    def _make_recommendation(self, analysis: Dict) -> str:
        """Faz recomendação final baseada na análise"""
        if analysis['risk_level'] == 'high':
            return 'avoid'
        elif analysis['risk_level'] == 'medium':
            return 'consider'
        else:
            return 'proceed'
    
    def _generate_reasoning(self, analysis: Dict) -> List[str]:
        """Gera raciocínio detalhado para a decisão"""
        reasoning = []
        
        # Raciocínio sobre impacto imediato
        impact = analysis['immediate_impact']
        reasoning.append(f"Immediate impact: {impact['pressure_created']} pressure, {impact['defense_provided']} defense")
        
        # Raciocínio sobre reações do oponente
        if analysis['opponent_reactions']:
            reactions_str = ", ".join([f"{r['card']} ({r['probability']:.1%})" for r in analysis['opponent_reactions']])
            reasoning.append(f"Opponent likely responds with: {reactions_str}")
        
        # Raciocínio sobre nossos counters
        if analysis['our_counters']:
            counters_str = ", ".join([f"{c['our_card']} ({c['effectiveness']:.1%})" for c in analysis['our_counters']])
            reasoning.append(f"We can counter with: {counters_str}")
        
        # Raciocínio sobre elixir
        if analysis['elixir_impact'] < 0:
            reasoning.append(f"Elixir concern: will have {abs(analysis['elixir_impact'])} less elixir")
        
        # Raciocínio final
        reasoning.append(f"Risk level: {analysis['risk_level']} - Recommendation: {analysis['recommendation']}")
        
        return reasoning
    
    def _estimate_card_cost(self, card_name: str) -> int:
        """Estima o custo de elixir de uma carta"""
        costs = {
            'giant': 5, 'minipekka': 4, 'musketeer': 4, 'knight': 3,
            'archers': 3, 'minions': 3, 'fireball': 4, 'spear_goblins': 2
        }
        return costs.get(card_name, 3)
    
    def record_turn(self, action: Dict, opponent_response: Dict = None):
        """Registra um turno para análise histórica"""
        turn_record = {
            'timestamp': time.time(),
            'our_action': action,
            'opponent_response': opponent_response,
            'success': self._evaluate_turn_success(action, opponent_response)
        }
        
        self.turn_history.append(turn_record)
        
        # Manter apenas os últimos 20 turnos
        if len(self.turn_history) > 20:
            self.turn_history.pop(0)
    
    def _evaluate_turn_success(self, our_action: Dict, opponent_response: Dict) -> str:
        """Avalia o sucesso de um turno"""
        if not opponent_response:
            return 'unknown'
        
        # Lógica simples de avaliação
        our_card = our_action.get('card', '')
        opponent_card = opponent_response.get('card', '')
        
        # Se conseguimos counter a resposta do oponente
        if self._can_counter(our_card, opponent_card):
            return 'success'
        else:
            return 'failure'
    
    def _can_counter(self, our_card: str, opponent_card: str) -> bool:
        """Verifica se nossa carta pode counter a do oponente"""
        counter_matrix = {
            'minipekka': ['giant', 'pekka', 'golem'],
            'knight': ['musketeer', 'archers', 'wizard'],
            'fireball': ['musketeer', 'wizard', 'witch'],
            'musketeer': ['baby_dragon', 'minions', 'balloon']
        }
        
        return opponent_card in counter_matrix.get(our_card, [])

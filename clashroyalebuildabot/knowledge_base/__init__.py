"""
Base de Conhecimento para Clash Royale Bot
Sistema completo de estratégias, counters e análise de jogo
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from loguru import logger


class KnowledgeBase:
    def __init__(self, base_path: str = None):
        if base_path is None:
            # Pega o diretório onde está este arquivo
            base_path = os.path.dirname(os.path.abspath(__file__))
        self.base_path = base_path
        self.counters = self.load_counters()
        self.decks = self.load_decks()
        self.strategies = self.load_strategies()
        self.positioning = self.load_positioning()
        self.game_phases = self.load_game_phases()
        self.matchups = self.load_matchups()
        self.chess_strategies = self.load_chess_strategies()
        self.cycling_strategies = self.load_cycling_strategies()
        
        logger.info("Base de conhecimento carregada com sucesso")
    
    def load_json_file(self, filename: str) -> Dict:
        """Carrega arquivo JSON da base de conhecimento"""
        filepath = os.path.join(self.base_path, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Carregado {filename}: {len(data)} entradas")
            return data
        except FileNotFoundError:
            logger.warning(f"Arquivo {filename} não encontrado, usando dados padrão")
            return {}
        except Exception as e:
            logger.error(f"Erro ao carregar {filename}: {e}")
            return {}
    
    def load_counters(self) -> Dict:
        """Carrega sistema de counters"""
        return self.load_json_file("counters.json")
    
    def load_decks(self) -> Dict:
        """Carrega decks conhecidos"""
        return self.load_json_file("decks.json")
    
    def load_strategies(self) -> Dict:
        """Carrega estratégias por situação"""
        return self.load_json_file("strategies.json")
    
    def load_positioning(self) -> Dict:
        """Carrega guias de posicionamento"""
        return self.load_json_file("positioning.json")
    
    def load_game_phases(self) -> Dict:
        """Carrega decisões por fase do jogo"""
        return self.load_json_file("game_phases.json")
    
    def load_matchups(self) -> Dict:
        """Carrega análise de matchups"""
        return self.load_json_file("matchups.json")
    
    def load_chess_strategies(self) -> Dict:
        """Carrega estratégias de xadrez avançadas"""
        return self.load_json_file("chess_strategies.json")
    
    def load_cycling_strategies(self) -> Dict:
        """Carrega estratégias de cycling e cálculo de elixir"""
        return self.load_json_file("cycling_strategies.json")
    
    def get_counter_suggestions(self, enemy_card: str, our_deck: List[str]) -> List[str]:
        """Retorna melhores counters baseado no nosso deck"""
        if enemy_card not in self.counters:
            return []
        
        counter_data = self.counters[enemy_card]
        available_counters = []
        
        # Prioriza hard counters disponíveis no nosso deck
        for counter in counter_data.get("hard_counters", []):
            if counter in our_deck:
                available_counters.append(counter)
        
        # Adiciona soft counters se não há hard counters suficientes
        if len(available_counters) < 2:
            for counter in counter_data.get("soft_counters", []):
                if counter in our_deck and counter not in available_counters:
                    available_counters.append(counter)
        
        # Adiciona spell counters se necessário
        if len(available_counters) < 3:
            for counter in counter_data.get("spell_counters", []):
                if counter in our_deck and counter not in available_counters:
                    available_counters.append(counter)
        
        return available_counters
    
    def get_deck_analysis(self, enemy_cards: List[str]) -> Dict:
        """Analisa deck inimigo baseado nas cartas vistas"""
        best_match = None
        best_score = 0
        
        for deck_name, deck_data in self.decks.items():
            deck_cards = set(deck_data["cards"])
            enemy_cards_set = set(enemy_cards)
            
            # Calcula similaridade
            intersection = enemy_cards_set.intersection(deck_cards)
            if len(intersection) > 0:
                score = len(intersection) / len(deck_cards)
                
                # Bônus para cartas únicas do deck
                unique_cards = deck_cards - enemy_cards_set
                if len(unique_cards) <= 3:  # Poucas cartas restantes
                    score += 0.2
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        "name": deck_name,
                        "confidence": score,
                        "archetype": deck_data.get("archetype", "unknown"),
                        "win_condition": deck_data.get("win_condition", "unknown"),
                        "weaknesses": deck_data.get("weaknesses", []),
                        "strengths": deck_data.get("strengths", []),
                        "missing_cards": list(unique_cards),
                        "avg_elixir": deck_data.get("avg_elixir", 4.0)
                    }
        
        return best_match if best_match and best_match["confidence"] > 0.3 else None
    
    def get_strategy_suggestions(self, game_state: Dict) -> List[str]:
        """Sugere estratégia baseada na situação atual"""
        suggestions = []
        
        # Análise por elixir
        elixir = game_state.get("elixir", 0)
        if elixir <= 3:
            suggestions.extend(self.game_phases.get("low_elixir", {}).get("strategies", []))
        elif elixir <= 6:
            suggestions.extend(self.game_phases.get("medium_elixir", {}).get("strategies", []))
        else:
            suggestions.extend(self.game_phases.get("high_elixir", {}).get("strategies", []))
        
        # Análise por situação defensiva/ofensiva
        if game_state.get("under_pressure", False):
            suggestions.extend(self.strategies.get("defensive_situations", {}).get("general", []))
        elif game_state.get("advantage", False):
            suggestions.extend(self.strategies.get("offensive_situations", {}).get("advantage", []))
        
        return list(set(suggestions))  # Remove duplicatas
    
    def get_positioning_guide(self, card_name: str, situation: str) -> Dict:
        """Retorna guia de posicionamento para uma carta"""
        if card_name not in self.positioning.get("cards", {}):
            return {}
        
        card_positioning = self.positioning["cards"][card_name]
        return card_positioning.get(situation, card_positioning.get("default", {}))
    
    def get_matchup_analysis(self, our_deck: List[str], enemy_deck: List[str]) -> Dict:
        """Analisa matchup entre dois decks"""
        our_deck_name = self.identify_deck(our_deck)
        enemy_deck_name = self.identify_deck(enemy_deck)
        
        if our_deck_name and enemy_deck_name:
            matchup_key = f"{our_deck_name}_vs_{enemy_deck_name}"
            return self.matchups.get(matchup_key, {})
        
        return {}
    
    def identify_deck(self, cards: List[str]) -> Optional[str]:
        """Identifica o nome do deck baseado nas cartas"""
        best_match = None
        best_score = 0
        
        for deck_name, deck_data in self.decks.items():
            deck_cards = set(deck_data["cards"])
            cards_set = set(cards)
            
            intersection = cards_set.intersection(deck_cards)
            if len(intersection) > 0:
                score = len(intersection) / len(deck_cards)
                if score > best_score and score > 0.7:  # 70% de similaridade
                    best_score = score
                    best_match = deck_name
        
        return best_match
    
    def get_card_priority(self, card_name: str) -> int:
        """Retorna prioridade de uma carta (1-10, 10 sendo mais alta)"""
        return self.counters.get(card_name, {}).get("priority", 5)
    
    def get_elixir_efficiency(self, our_card: str, enemy_card: str) -> str:
        """Retorna eficiência de elixir de um trade"""
        if enemy_card not in self.counters:
            return "neutral"
        
        counter_data = self.counters[enemy_card]
        
        if our_card in counter_data.get("hard_counters", []):
            return "positive"
        elif our_card in counter_data.get("soft_counters", []):
            return "neutral"
        else:
            return "negative"
    
    def get_advanced_counter_analysis(self, enemy_card: str, our_card: str) -> Dict:
        """Retorna análise avançada de counter entre duas cartas"""
        if enemy_card not in self.counters:
            return {}
        
        counter_data = self.counters[enemy_card]
        advanced_counters = counter_data.get("advanced_counters", {})
        
        if our_card in advanced_counters:
            return advanced_counters[our_card]
        
        return {}
    
    def get_chess_strategy_moves(self, situation: str, game_state: Dict) -> List[Dict]:
        """Retorna movimentos de estratégia de xadrez para uma situação"""
        strategies = self.chess_strategies.get(situation, {})
        moves = strategies.get("moves", [])
        
        # Filtra movimentos baseado no estado do jogo
        filtered_moves = []
        for move in moves:
            elixir_cost = move.get("elixir_cost", 0)
            current_elixir = game_state.get("elixir", 0)
            
            # Só inclui movimentos que podemos pagar
            if elixir_cost == 0 or elixir_cost == "variable" or elixir_cost <= current_elixir:
                filtered_moves.append(move)
        
        # Ordena por prioridade
        priority_order = {"highest": 0, "high": 1, "medium": 2, "low": 3}
        filtered_moves.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 2))
        
        return filtered_moves
    
    def get_prediction_strategy(self, enemy_cards_played: List[str], our_deck: List[str]) -> Dict:
        """Retorna estratégia de predição baseada nas cartas jogadas"""
        # Analisa deck inimigo
        deck_analysis = self.get_deck_analysis(enemy_cards_played)
        
        # Identifica cartas esperadas
        expected_cards = []
        if deck_analysis:
            missing_cards = deck_analysis.get("missing_cards", [])
            for card in missing_cards:
                expected_cards.append({
                    "card": card,
                    "probability": deck_analysis.get("confidence", 0.5),
                    "counters": self.get_counter_suggestions(card, our_deck)
                })
        
        # Sugere preparação
        preparation_moves = []
        for expected in expected_cards:
            if expected["counters"]:
                preparation_moves.append({
                    "action": "save_counter",
                    "counter": expected["counters"][0],
                    "for_card": expected["card"],
                    "priority": "high" if expected["probability"] > 0.7 else "medium"
                })
        
        return {
            "deck_analysis": deck_analysis,
            "expected_cards": expected_cards,
            "preparation_moves": preparation_moves
        }
    
    def get_situational_strategy(self, game_state: Dict) -> Dict:
        """Retorna estratégia baseada na situação atual do jogo"""
        elixir = game_state.get("elixir", 0)
        under_pressure = game_state.get("under_pressure", False)
        advantage = game_state.get("advantage", False)
        
        if advantage:
            situation = "advantage_state"
        elif under_pressure:
            situation = "disadvantage_state"
        else:
            situation = "even_state"
        
        strategies = self.chess_strategies.get("situational_analysis", {}).get(situation, {})
        
        return {
            "situation": situation,
            "strategies": strategies,
            "recommended_moves": self.get_chess_strategy_moves(situation, game_state)
        }
    
    def get_counter_chain_analysis(self, enemy_card: str, our_deck: List[str]) -> List[Dict]:
        """Analisa cadeia de counters para uma carta inimiga"""
        if enemy_card not in self.counters:
            return []
        
        counter_data = self.counters[enemy_card]
        advanced_counters = counter_data.get("advanced_counters", {})
        
        chain_analysis = []
        for counter_name, counter_info in advanced_counters.items():
            if counter_name in our_deck:
                # Analisa riscos e follow-ups
                risks = counter_info.get("risks", [])
                followups = counter_info.get("best_followup", [])
                
                # Verifica se temos follow-ups disponíveis
                available_followups = [f for f in followups if f in our_deck]
                
                chain_analysis.append({
                    "counter": counter_name,
                    "effectiveness": counter_info.get("effectiveness", "unknown"),
                    "elixir_trade": counter_info.get("elixir_trade", "0"),
                    "risks": risks,
                    "available_followups": available_followups,
                    "counter_push_potential": counter_info.get("counter_push", "unknown"),
                    "recommended_positioning": counter_info.get("positioning", "unknown")
                })
        
        # Ordena por eficiência
        effectiveness_order = {"excellent": 0, "good": 1, "neutral": 2, "poor": 3}
        chain_analysis.sort(key=lambda x: effectiveness_order.get(x["effectiveness"], 2))
        
        return chain_analysis
    
    def get_cycling_strategy(self, situation: str, our_deck: List[str], game_state: Dict) -> Dict:
        """Retorna estratégia de cycling para uma situação específica"""
        cycling_data = self.cycling_strategies.get("cycling_situations", {})
        
        if situation in cycling_data:
            scenarios = cycling_data[situation]["scenarios"]
            
            # Filtra cenários baseado no estado do jogo
            filtered_scenarios = []
            for scenario in scenarios:
                elixir_cost = scenario.get("elixir_cost", 0)
                current_elixir = game_state.get("elixir", 0)
                
                # Só inclui cenários que podemos pagar
                if elixir_cost == 0 or elixir_cost == "variable" or elixir_cost == "cheap_cards" or elixir_cost <= current_elixir:
                    filtered_scenarios.append(scenario)
            
            # Ordena por prioridade
            priority_order = {"highest": 0, "high": 1, "medium": 2, "low": 3}
            filtered_scenarios.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 2))
            
            return {
                "situation": situation,
                "scenarios": filtered_scenarios,
                "recommended_actions": self._get_cycling_actions(filtered_scenarios, our_deck)
            }
        
        return {}
    
    def _get_cycling_actions(self, scenarios: List[Dict], our_deck: List[str]) -> List[Dict]:
        """Gera ações de cycling baseadas nos cenários"""
        actions = []
        
        for scenario in scenarios:
            situation = scenario.get("situation", "")
            
            if situation == "need_win_condition":
                # Encontrar win conditions no deck
                win_conditions = [card for card in our_deck if card in ["giant", "balloon", "hog_rider", "pekka"]]
                if win_conditions:
                    actions.append({
                        "action": "cycle_to_win_condition",
                        "target": win_conditions[0],
                        "priority": scenario.get("priority", "medium"),
                        "elixir_cost": "variable"
                    })
            
            elif situation == "enemy_committed":
                # Ciclar com cartas baratas
                cheap_cards = [card for card in our_deck if self._get_card_cost(card) <= 3]
                if cheap_cards:
                    actions.append({
                        "action": "cycle_cheap_cards",
                        "cards": cheap_cards,
                        "priority": scenario.get("priority", "medium"),
                        "elixir_cost": "cheap_cards"
                    })
            
            elif situation == "need_counter":
                # Ciclar para encontrar counters
                counter_cards = [card for card in our_deck if card in ["minipekka", "fireball", "zap"]]
                if counter_cards:
                    actions.append({
                        "action": "cycle_to_counter",
                        "target": counter_cards[0],
                        "priority": scenario.get("priority", "medium"),
                        "elixir_cost": "variable"
                    })
        
        return actions
    
    def _get_card_cost(self, card_name: str) -> int:
        """Retorna o custo de elixir de uma carta"""
        card_costs = {
            "zap": 2, "arrows": 3, "fireball": 4, "poison": 4, "lightning": 6, "rocket": 6,
            "knight": 3, "archers": 3, "musketeer": 4, "minipekka": 4, "giant": 5, "pekka": 7,
            "witch": 5, "baby_dragon": 4, "minions": 3, "bats": 2, "goblin_barrel": 3,
            "cannon": 3, "tesla": 4, "inferno_tower": 5
        }
        return card_costs.get(card_name, 4)
    
    def calculate_our_elixir(self, base_elixir: float, time_elapsed: float, spent_elixir: float) -> float:
        """Calcula nosso elixir atual"""
        time_bonus = time_elapsed * 0.1  # 0.1 elixir por segundo
        current_elixir = base_elixir + time_bonus - spent_elixir
        return min(10.0, max(0.0, current_elixir))
    
    def estimate_enemy_elixir(self, enemy_actions: List[Dict], time_since_last_action: float) -> Dict:
        """Estima o elixir do inimigo"""
        estimated_elixir = 5.0  # Começa com 5 elixir
        
        # Subtrai elixir gasto em ações conhecidas
        for action in enemy_actions:
            card_cost = self._get_card_cost(action.get("card", ""))
            estimated_elixir -= card_cost
        
        # Adiciona elixir ganho por tempo
        time_bonus = time_since_last_action * 0.1
        estimated_elixir += time_bonus
        
        # Limita entre 0 e 10
        estimated_elixir = min(10.0, max(0.0, estimated_elixir))
        
        # Determina estado do elixir
        if estimated_elixir <= 3:
            elixir_state = "elixir_dry"
        elif estimated_elixir <= 7:
            elixir_state = "medium_elixir"
        else:
            elixir_state = "full_elixir"
        
        return {
            "estimated_elixir": estimated_elixir,
            "elixir_state": elixir_state,
            "confidence": 0.8  # Confiança da estimativa
        }
    
    def calculate_elixir_advantage(self, our_elixir: float, enemy_elixir: float) -> Dict:
        """Calcula vantagem de elixir"""
        advantage = our_elixir - enemy_elixir
        
        if advantage >= 3:
            strategic_implication = "advantage_3+"
            recommendation = "Aplicar pressão agressiva"
        elif advantage >= 1:
            strategic_implication = "advantage_1-2"
            recommendation = "Manter pressão moderada"
        elif advantage >= -1:
            strategic_implication = "equilibrium"
            recommendation = "Jogar equilibrado"
        elif advantage >= -3:
            strategic_implication = "disadvantage_1-2"
            recommendation = "Jogar defensivo"
        else:
            strategic_implication = "disadvantage_3+"
            recommendation = "Jogar muito defensivo"
        
        return {
            "advantage": advantage,
            "strategic_implication": strategic_implication,
            "recommendation": recommendation,
            "our_elixir": our_elixir,
            "enemy_elixir": enemy_elixir
        }
    
    def get_optimal_cycling_moment(self, game_state: Dict, enemy_elixir_state: str) -> Dict:
        """Determina o momento ideal para ciclar"""
        cycling_data = self.cycling_strategies.get("advanced_cycling_strategies", {})
        timing_data = cycling_data.get("cycle_timing", {})
        
        optimal_moments = timing_data.get("optimal_moments", [])
        avoid_moments = timing_data.get("avoid_cycling", [])
        
        # Analisa se é um bom momento para ciclar
        current_situation = {
            "enemy_elixir_state": enemy_elixir_state,
            "our_elixir": game_state.get("elixir", 0),
            "under_pressure": game_state.get("under_pressure", False)
        }
        
        # Verifica se deve evitar cycling
        for avoid_moment in avoid_moments:
            if self._should_avoid_cycling(avoid_moment, current_situation):
                return {
                    "should_cycle": False,
                    "reason": avoid_moment.get("reason", "unknown"),
                    "alternative": avoid_moment.get("alternative", "wait"),
                    "priority": "high"
                }
        
        # Verifica se é um bom momento
        for optimal_moment in optimal_moments:
            if self._is_optimal_cycling_moment(optimal_moment, current_situation):
                return {
                    "should_cycle": True,
                    "moment": optimal_moment.get("moment", "unknown"),
                    "advantage": optimal_moment.get("advantage", "unknown"),
                    "risk": optimal_moment.get("risk", "unknown"),
                    "priority": "high"
                }
        
        # Situação neutra
        return {
            "should_cycle": True,
            "moment": "neutral_situation",
            "advantage": "safe_cycling",
            "risk": "minimal",
            "priority": "medium"
        }
    
    def _should_avoid_cycling(self, avoid_moment: Dict, situation: Dict) -> bool:
        """Verifica se deve evitar cycling"""
        moment = avoid_moment.get("moment", "")
        
        if moment == "enemy_full_elixir" and situation["enemy_elixir_state"] == "full_elixir":
            return True
        elif moment == "under_pressure" and situation["under_pressure"]:
            return True
        elif moment == "low_elixir" and situation["our_elixir"] < 4:
            return True
        
        return False
    
    def _is_optimal_cycling_moment(self, optimal_moment: Dict, situation: Dict) -> bool:
        """Verifica se é um momento ótimo para cycling"""
        moment = optimal_moment.get("moment", "")
        
        if moment == "during_advantage" and situation["our_elixir"] > 6:
            return True
        elif moment == "before_enemy_push" and situation["enemy_elixir_state"] == "full_elixir":
            return True
        
        return False
    
    def get_cycle_efficiency_tips(self, our_deck: List[str]) -> List[Dict]:
        """Retorna dicas para cycling eficiente"""
        cycling_data = self.cycling_strategies.get("advanced_cycling_strategies", {})
        efficiency_data = cycling_data.get("cycle_efficiency", {})
        
        efficient_strategies = efficiency_data.get("efficient_cycling", [])
        inefficient_mistakes = efficiency_data.get("inefficient_cycling", [])
        
        tips = []
        
        # Adiciona estratégias eficientes
        for strategy in efficient_strategies:
            if self._can_apply_strategy(strategy, our_deck):
                tips.append({
                    "type": "efficient_strategy",
                    "strategy": strategy.get("strategy", ""),
                    "description": strategy.get("description", ""),
                    "elixir_saved": strategy.get("elixir_saved", ""),
                    "priority": strategy.get("priority", "medium")
                })
        
        # Adiciona avisos sobre erros
        for mistake in inefficient_mistakes:
            if self._should_warn_about_mistake(mistake, our_deck):
                tips.append({
                    "type": "avoid_mistake",
                    "mistake": mistake.get("mistake", ""),
                    "description": mistake.get("description", ""),
                    "avoidance": mistake.get("avoidance", ""),
                    "priority": "high"
                })
        
        return tips
    
    def _can_apply_strategy(self, strategy: Dict, our_deck: List[str]) -> bool:
        """Verifica se uma estratégia pode ser aplicada com nosso deck"""
        strategy_name = strategy.get("strategy", "")
        
        if strategy_name == "cheapest_card_first":
            return len([card for card in our_deck if self._get_card_cost(card) <= 3]) >= 2
        elif strategy_name == "defensive_cycling":
            return len([card for card in our_deck if card in ["knight", "archers", "cannon"]]) >= 2
        
        return True
    
    def _should_warn_about_mistake(self, mistake: Dict, our_deck: List[str]) -> bool:
        """Verifica se deve avisar sobre um erro específico"""
        mistake_name = mistake.get("mistake", "")
        
        if mistake_name == "expensive_cycle":
            return len([card for card in our_deck if self._get_card_cost(card) >= 5]) >= 3
        elif mistake_name == "unsafe_cycle":
            return len([card for card in our_deck if card in ["minions", "bats"]]) >= 1
        
        return True


# Instância global da base de conhecimento
knowledge_base = KnowledgeBase()

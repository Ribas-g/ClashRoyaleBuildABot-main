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
        self.card_intelligence = self.load_card_intelligence()
        self.dynamic_positioning = self.load_dynamic_positioning()
        self.clash_royale_database = self.load_clash_royale_database()
        
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
    
    def load_card_intelligence(self) -> Dict:
        """Carrega inteligência de cartas e posicionamento"""
        return self.load_json_file("card_intelligence.json")
    
    def load_dynamic_positioning(self) -> Dict:
        """Carrega sistema de posicionamento dinâmico"""
        return self.load_json_file("dynamic_positioning.json")
    
    def load_clash_royale_database(self) -> Dict:
        """Carrega base de dados completa do Clash Royale"""
        return self.load_json_file("clash_royale_database.json")
    
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
    
    def get_card_intelligence(self, card_name: str) -> Dict:
        """Retorna inteligência completa de uma carta"""
        return self.card_intelligence.get("card_purposes", {}).get(card_name, {})
    
    def get_card_purpose(self, card_name: str) -> str:
        """Retorna o propósito principal de uma carta"""
        card_data = self.get_card_intelligence(card_name)
        return card_data.get("purpose", "unknown")
    
    def get_card_type(self, card_name: str) -> str:
        """Retorna o tipo de uma carta"""
        card_data = self.get_card_intelligence(card_name)
        return card_data.get("type", "unknown")
    
    def get_optimal_positioning(self, card_name: str, situation: str = "defensive") -> Dict:
        """Retorna posicionamento ótimo para uma carta"""
        card_data = self.get_card_intelligence(card_name)
        positioning = card_data.get("positioning", {})
        
        if situation == "offensive":
            return positioning.get("offensive", positioning.get("defensive", {}))
        else:
            return positioning.get("defensive", positioning.get("offensive", {}))
    
    def should_use_card(self, card_name: str, game_state: Dict) -> Dict:
        """Determina se deve usar uma carta baseado na situação"""
        card_data = self.get_card_intelligence(card_name)
        if not card_data:
            return {"should_use": False, "reason": "card_not_found"}
        
        current_elixir = game_state.get("elixir", 0)
        under_pressure = game_state.get("under_pressure", False)
        enemy_has_counters = game_state.get("enemy_has_counters", False)
        
        # Verifica condições para usar
        when_to_use = card_data.get("when_to_use", [])
        avoid_using = card_data.get("avoid_using", [])
        
        # Verifica se deve evitar
        if "low_elixir" in avoid_using and current_elixir < 4:
            return {"should_use": False, "reason": "low_elixir"}
        
        if "under_pressure" in avoid_using and under_pressure:
            return {"should_use": False, "reason": "under_pressure"}
        
        if "enemy_has_counters" in avoid_using and enemy_has_counters:
            return {"should_use": False, "reason": "enemy_has_counters"}
        
        # Verifica se deve usar
        if "elixir_advantage" in when_to_use and current_elixir >= 6:
            return {"should_use": True, "reason": "elixir_advantage"}
        
        if "counter_push_opportunity" in when_to_use and not under_pressure:
            return {"should_use": True, "reason": "counter_push_opportunity"}
        
        # Situação neutra
        return {"should_use": True, "reason": "neutral_situation"}
    
    def get_card_usage_guide(self, card_name: str) -> Dict:
        """Retorna guia completo de uso de uma carta"""
        card_data = self.get_card_intelligence(card_name)
        if not card_data:
            return {}
        
        return {
            "purpose": card_data.get("purpose", ""),
            "usage": card_data.get("usage", ""),
            "when_to_use": card_data.get("when_to_use", []),
            "avoid_using": card_data.get("avoid_using", []),
            "positioning": card_data.get("positioning", {}),
            "type": card_data.get("type", "")
        }
    
    def get_similar_cards_guide(self) -> Dict:
        """Retorna guia para distinguir cartas similares"""
        return self.card_intelligence.get("detection_improvements", {}).get("similar_cards", {})
    
    def get_positioning_rules(self) -> Dict:
        """Retorna regras gerais de posicionamento"""
        return self.card_intelligence.get("positioning_rules", {})
    
    def get_usage_conditions(self) -> Dict:
        """Retorna condições de uso das cartas"""
        return self.card_intelligence.get("usage_conditions", {})
    
    def analyze_card_decision(self, card_name: str, game_state: Dict, enemy_analysis: Dict = None) -> Dict:
        """Análise completa de decisão para usar uma carta"""
        card_data = self.get_card_intelligence(card_name)
        if not card_data:
            return {"decision": "unknown", "reason": "card_not_found"}
        
        # Análise básica
        should_use = self.should_use_card(card_name, game_state)
        
        # Análise de posicionamento
        situation = "offensive" if game_state.get("advantage", False) else "defensive"
        positioning = self.get_optimal_positioning(card_name, situation)
        
        # Análise de elixir
        current_elixir = game_state.get("elixir", 0)
        card_cost = self._get_card_cost(card_name)
        elixir_sufficient = current_elixir >= card_cost
        
        # Análise de contexto
        context_analysis = {
            "card_type": card_data.get("type", ""),
            "purpose": card_data.get("purpose", ""),
            "elixir_cost": card_cost,
            "elixir_available": current_elixir,
            "situation": situation
        }
        
        # Decisão final
        if not should_use["should_use"]:
            decision = "avoid"
            reason = should_use["reason"]
        elif not elixir_sufficient:
            decision = "wait"
            reason = "insufficient_elixir"
        else:
            decision = "use"
            reason = should_use["reason"]
        
        return {
            "decision": decision,
            "reason": reason,
            "positioning": positioning,
            "context": context_analysis,
            "card_data": card_data
        }
    
    def get_spell_targeting_guide(self, spell_name: str) -> Dict:
        """Guia específico para targeting de spells"""
        spell_data = self.get_card_intelligence(spell_name)
        if not spell_data or spell_data.get("type") != "spell":
            return {}
        
        return {
            "purpose": spell_data.get("purpose", ""),
            "when_to_use": spell_data.get("when_to_use", []),
            "avoid_using": spell_data.get("avoid_using", []),
            "positioning": spell_data.get("positioning", {}),
            "targeting_rules": self._get_spell_targeting_rules(spell_name)
        }
    
    def _get_spell_targeting_rules(self, spell_name: str) -> Dict:
        """Regras específicas de targeting para spells"""
        targeting_rules = {
            "fireball": {
                "target_groups": "3+ tropas agrupadas",
                "target_tower": "Quando torre está baixa",
                "avoid_single": "Não usar em tropa única",
                "target_position": "Centro para máximo alcance",
                "tower_damage": "Usar na torre quando há vantagem"
            },
            "zap": {
                "target_inferno": "Resetar inferno tower/dragon",
                "target_swarm": "Stun swarm de tropas",
                "target_low_health": "Finalizar tropas com pouca vida",
                "target_position": "Centro para stun"
            },
            "goblin_barrel": {
                "target_tower": "Sempre na torre inimiga",
                "bait_spells": "Para forçar zap/arrows",
                "target_position": "Tile 8,5 na torre"
            }
        }
        
        return targeting_rules.get(spell_name, {})
    
    def get_win_condition_usage(self, card_name: str, game_state: Dict) -> Dict:
        """Análise específica para win conditions"""
        card_data = self.get_card_intelligence(card_name)
        if not card_data or card_data.get("type") != "win_condition":
            return {"should_use": False, "reason": "not_win_condition"}
        
        current_elixir = game_state.get("elixir", 0)
        under_pressure = game_state.get("under_pressure", False)
        enemy_elixir_state = game_state.get("enemy_elixir_state", "unknown")
        
        # Win conditions precisam de elixir suficiente
        if current_elixir < 5:
            return {"should_use": False, "reason": "insufficient_elixir"}
        
        # Não usar win condition sob pressão
        if under_pressure:
            return {"should_use": False, "reason": "under_pressure"}
        
        # Usar quando inimigo está com pouco elixir
        if enemy_elixir_state == "elixir_dry":
            return {"should_use": True, "reason": "enemy_elixir_dry"}
        
        # Usar com vantagem de elixir
        if current_elixir >= 7:
            return {"should_use": True, "reason": "elixir_advantage"}
        
        return {"should_use": False, "reason": "wait_for_better_opportunity"}
    
    def get_support_usage(self, card_name: str, game_state: Dict) -> Dict:
        """Análise específica para cartas de suporte"""
        card_data = self.get_card_intelligence(card_name)
        if not card_data or card_data.get("type") != "support":
            return {"should_use": False, "reason": "not_support"}
        
        current_elixir = game_state.get("elixir", 0)
        has_tank = game_state.get("has_tank", False)
        need_air_defense = game_state.get("need_air_defense", False)
        
        # Suporte precisa de tank ou necessidade específica
        if has_tank and current_elixir >= 3:
            return {"should_use": True, "reason": "support_tank"}
        
        if need_air_defense and current_elixir >= 3:
            return {"should_use": True, "reason": "air_defense"}
        
        return {"should_use": False, "reason": "no_support_needed"}
    
    def get_dynamic_position(self, card_name: str, game_state: Dict, enemy_units: List = None, our_units: List = None) -> Dict:
        """Calcula posição dinâmica baseada na situação atual"""
        card_data = self.get_card_intelligence(card_name)
        if not card_data:
            return self._get_fallback_position(card_name)
        
        card_type = card_data.get("type", "unknown")
        
        # Analisa situação atual
        situation_analysis = self._analyze_current_situation(game_state, enemy_units, our_units)
        
        # Determina estratégia de posicionamento
        positioning_strategy = self._determine_positioning_strategy(card_type, situation_analysis)
        
        # Calcula posição baseada na estratégia
        position = self._calculate_position_from_strategy(positioning_strategy, situation_analysis)
        
        return {
            "position": position,
            "strategy": positioning_strategy,
            "reasoning": self._explain_positioning_decision(card_name, positioning_strategy, situation_analysis),
            "alternatives": self._get_alternative_positions(positioning_strategy, situation_analysis)
        }
    
    def _analyze_current_situation(self, game_state: Dict, enemy_units: List = None, our_units: List = None) -> Dict:
        """Analisa a situação atual do jogo"""
        analysis = {
            "elixir_advantage": game_state.get("elixir", 0) - game_state.get("enemy_elixir", 5),
            "under_pressure": game_state.get("under_pressure", False),
            "advantage": game_state.get("advantage", False),
            "tower_health": game_state.get("tower_health", 100),
            "game_time": game_state.get("game_time", 0)
        }
        
        # Análise de unidades inimigas
        if enemy_units:
            analysis["enemy_tanks"] = [unit for unit in enemy_units if unit.get("name") in ["giant", "pekka", "golem", "royal_giant", "electro_giant"]]
            analysis["enemy_air_units"] = [unit for unit in enemy_units if unit.get("name") in ["baby_dragon", "minions", "bats", "balloon", "lava_hound"]]
            analysis["enemy_swarm"] = [unit for unit in enemy_units if unit.get("name") in ["minions", "bats", "skeleton_army", "goblin_gang"]]
            analysis["enemy_supports"] = [unit for unit in enemy_units if unit.get("name") in ["musketeer", "witch", "baby_dragon", "archers"]]
        
        # Análise de nossas unidades
        if our_units:
            analysis["our_tanks"] = [unit for unit in our_units if unit.get("name") in ["giant", "pekka", "golem", "royal_giant", "electro_giant"]]
            analysis["our_supports"] = [unit for unit in our_units if unit.get("name") in ["musketeer", "witch", "baby_dragon", "archers"]]
            analysis["our_buildings"] = [unit for unit in our_units if unit.get("name") in ["cannon", "tesla", "inferno_tower"]]
        
        return analysis
    
    def _determine_positioning_strategy(self, card_type: str, situation_analysis: Dict) -> str:
        """Determina a estratégia de posicionamento baseada no tipo de carta e situação"""
        if card_type == "win_condition":
            return self._get_tank_positioning_strategy(situation_analysis)
        elif card_type == "support":
            return self._get_support_positioning_strategy(situation_analysis)
        elif card_type == "spell":
            return self._get_spell_positioning_strategy(situation_analysis)
        elif card_type == "building":
            return self._get_building_positioning_strategy(situation_analysis)
        else:
            return "default_positioning"
    
    def _get_tank_positioning_strategy(self, situation_analysis: Dict) -> str:
        """Determina estratégia de posicionamento para tanks"""
        if situation_analysis.get("under_pressure", False):
            return "center_defense"
        elif situation_analysis.get("elixir_advantage", 0) >= 2:
            return "bridge_push"
        elif situation_analysis.get("advantage", False):
            return "split_push"
        else:
            return "counter_push"
    
    def _get_support_positioning_strategy(self, situation_analysis: Dict) -> str:
        """Determina estratégia de posicionamento para suporte"""
        if situation_analysis.get("enemy_air_units"):
            return "air_defense"
        elif situation_analysis.get("enemy_swarm"):
            return "swarm_defense"
        elif situation_analysis.get("our_tanks"):
            return "behind_tank"
        else:
            return "cycle_position"
    
    def _get_spell_positioning_strategy(self, situation_analysis: Dict) -> str:
        """Determina estratégia de posicionamento para spells"""
        if situation_analysis.get("enemy_swarm") and len(situation_analysis["enemy_swarm"]) >= 3:
            return "group_damage"
        elif situation_analysis.get("tower_health", 100) < 50:
            return "tower_damage"
        elif situation_analysis.get("enemy_tanks"):
            return "inferno_reset"
        else:
            return "finish_low_health"
    
    def _get_building_positioning_strategy(self, situation_analysis: Dict) -> str:
        """Determina estratégia de posicionamento para buildings"""
        if situation_analysis.get("enemy_tanks"):
            return "tank_distraction"
        elif situation_analysis.get("enemy_units"):
            return "center_attraction"
        else:
            return "lane_control"
    
    def _calculate_position_from_strategy(self, strategy: str, situation_analysis: Dict) -> Dict:
        """Calcula posição baseada na estratégia"""
        positioning_data = self.dynamic_positioning.get("positioning_analysis", {})
        position_calculators = positioning_data.get("position_calculators", {})
        
        if strategy in position_calculators:
            calculator = position_calculators[strategy]
            logic = calculator.get("logic", {})
            
            # Tenta posição primária
            primary = logic.get("primary", "tile_4_5")
            if self._is_position_valid(primary, situation_analysis):
                return self._parse_tile_position(primary)
            
            # Tenta posições alternativas
            alternatives = logic.get("alternatives", ["tile_4_5"])
            for alt in alternatives:
                if self._is_position_valid(alt, situation_analysis):
                    return self._parse_tile_position(alt)
        
        # Fallback
        return self._get_fallback_position_by_type(strategy)
    
    def _is_position_valid(self, position: str, situation_analysis: Dict) -> bool:
        """Verifica se uma posição é válida na situação atual"""
        # Implementação básica - pode ser expandida
        return True
    
    def _parse_tile_position(self, tile_str: str) -> Dict:
        """Converte string de tile para coordenadas"""
        if tile_str == "tile_7_5":
            return {"tile_x": 7, "tile_y": 5, "description": "Bridge position"}
        elif tile_str == "tile_4_5":
            return {"tile_x": 4, "tile_y": 5, "description": "Center position"}
        elif tile_str == "tile_6_5":
            return {"tile_x": 6, "tile_y": 5, "description": "Behind tank position"}
        elif tile_str == "tile_8_5":
            return {"tile_x": 8, "tile_y": 5, "description": "Tower position"}
        elif tile_str == "tile_3_5":
            return {"tile_x": 3, "tile_y": 5, "description": "Back position"}
        elif tile_str == "tile_5_5":
            return {"tile_x": 5, "tile_y": 5, "description": "Forward position"}
        else:
            return {"tile_x": 4, "tile_y": 5, "description": "Default position"}
    
    def _get_fallback_position(self, card_name: str) -> Dict:
        """Retorna posição de fallback para uma carta"""
        fallback_positions = self.dynamic_positioning.get("fallback_positions", {})
        
        card_data = self.get_card_intelligence(card_name)
        card_type = card_data.get("type", "unknown")
        
        if card_type == "win_condition":
            return self._parse_tile_position(fallback_positions.get("default_offensive", "tile_7_5"))
        elif card_type == "support":
            return self._parse_tile_position(fallback_positions.get("default_support", "tile_6_5"))
        elif card_type == "spell":
            return self._parse_tile_position(fallback_positions.get("default_spell", "tile_4_5"))
        elif card_type == "building":
            return self._parse_tile_position(fallback_positions.get("default_building", "tile_4_5"))
        else:
            return self._parse_tile_position(fallback_positions.get("default_defensive", "tile_4_5"))
    
    def _get_fallback_position_by_type(self, strategy: str) -> Dict:
        """Retorna posição de fallback baseada na estratégia"""
        if "defense" in strategy:
            return {"tile_x": 4, "tile_y": 5, "description": "Defensive fallback"}
        elif "push" in strategy:
            return {"tile_x": 7, "tile_y": 5, "description": "Offensive fallback"}
        elif "support" in strategy:
            return {"tile_x": 6, "tile_y": 5, "description": "Support fallback"}
        else:
            return {"tile_x": 4, "tile_y": 5, "description": "Default fallback"}
    
    def _explain_positioning_decision(self, card_name: str, strategy: str, situation_analysis: Dict) -> str:
        """Explica a decisão de posicionamento"""
        card_data = self.get_card_intelligence(card_name)
        card_type = card_data.get("type", "unknown")
        
        explanation = f"Posicionando {card_name} ({card_type}) usando estratégia '{strategy}'"
        
        if situation_analysis.get("under_pressure"):
            explanation += " - Sob pressão, posicionamento defensivo"
        elif situation_analysis.get("advantage"):
            explanation += " - Com vantagem, posicionamento ofensivo"
        elif situation_analysis.get("elixir_advantage", 0) >= 2:
            explanation += " - Vantagem de elixir, posicionamento agressivo"
        
        return explanation
    
    def _get_alternative_positions(self, strategy: str, situation_analysis: Dict) -> List[Dict]:
        """Retorna posições alternativas"""
        alternatives = []
        
        # Adiciona posições alternativas baseadas na estratégia
        if strategy == "bridge_push":
            alternatives.extend([
                {"tile_x": 6, "tile_y": 5, "description": "Safer bridge"},
                {"tile_x": 8, "tile_y": 5, "description": "Aggressive bridge"}
            ])
        elif strategy == "center_defense":
            alternatives.extend([
                {"tile_x": 3, "tile_y": 5, "description": "Back defense"},
                {"tile_x": 5, "tile_y": 5, "description": "Forward defense"}
            ])
        
        return alternatives
    
    # ===== MÉTODOS PARA USAR O CLASH ROYALE DATABASE =====
    
    def get_optimal_positioning_from_database(self, card_name: str, situation: str = "default") -> Dict:
        """Retorna posicionamento ótimo do banco de dados"""
        if not self.clash_royale_database or "cards" not in self.clash_royale_database:
            return {}
        
        card_data = self.clash_royale_database["cards"].get(card_name, {})
        if not card_data:
            return {}
        
        # Retorna posicionamento para a situação específica
        positioning = card_data.get(situation, card_data.get("default", {}))
        
        return {
            "tile_x": positioning.get("tile_x", 4),
            "tile_y": positioning.get("tile_y", 10),
            "description": positioning.get("description", "Default positioning"),
            "priority": positioning.get("priority", "medium")
        }
    
    def get_strategy_for_game_phase(self, phase: str) -> Dict:
        """Retorna estratégias para uma fase específica do jogo"""
        if not self.clash_royale_database:
            return {}
        
        phase_strategies = {
            "opening": self.clash_royale_database.get("opening_strategies", {}),
            "mid_game": self.clash_royale_database.get("mid_game_strategies", {}),
            "late_game": self.clash_royale_database.get("late_game_strategies", {})
        }
        
        return phase_strategies.get(phase, {})
    
    def get_prediction_strategies(self) -> Dict:
        """Retorna estratégias de predição"""
        if not self.clash_royale_database:
            return {}
        
        return self.clash_royale_database.get("prediction_strategies", {})
    
    def get_advanced_tactics(self) -> Dict:
        """Retorna táticas avançadas"""
        if not self.clash_royale_database:
            return {}
        
        return self.clash_royale_database.get("advanced_tactics", {})
    
    def get_state_inference_rules(self) -> List[Dict]:
        """Retorna regras de inferência de estado"""
        if not self.clash_royale_database:
            return []
        
        return self.clash_royale_database.get("state_inference_rules", [])
    
    def infer_game_state(self, game_state: Dict) -> str:
        """Inferência de estado baseada nas regras do banco de dados"""
        rules = self.get_state_inference_rules()
        
        for rule in rules:
            condition = rule.get("if", "")
            if self._evaluate_state_condition(condition, game_state):
                return rule.get("then_state", "unknown")
        
        return "unknown"
    
    def _evaluate_state_condition(self, condition: str, game_state: Dict) -> bool:
        """Avalia uma condição de estado"""
        try:
            # Implementação básica - pode ser expandida
            if "opponent_elixir_estimated <= 3" in condition:
                enemy_elixir = game_state.get("enemy_elixir", 5)
                return enemy_elixir <= 3
            elif "we defended with surviving troops >= 6 elixir value" in condition:
                surviving_troops = game_state.get("surviving_troops_elixir", 0)
                return surviving_troops >= 6
            elif "double elixir time" in condition:
                game_time = game_state.get("game_time", 0)
                return game_time > 120  # 2 minutos
            elif "our tower < 1000 hp" in condition:
                tower_hp = game_state.get("tower_hp", 1000)
                return tower_hp < 1000
            return False
        except Exception as e:
            logger.warning(f"Error evaluating state condition: {e}")
            return False
    
    def get_ml_training_schema(self) -> Dict:
        """Retorna schema para treinamento de ML"""
        if not self.clash_royale_database:
            return {}
        
        return self.clash_royale_database.get("ml_training_schema", {})
    
    def get_popular_decks(self) -> List[Dict]:
        """Retorna decks populares"""
        if not self.clash_royale_database:
            return []
        
        return self.clash_royale_database.get("popular_decks", [])
    
    def get_strategy_moves(self, strategy_name: str, game_state: Dict) -> List[Dict]:
        """Retorna movimentos para uma estratégia específica"""
        if not self.clash_royale_database:
            return []
        
        # Procura em todas as estratégias
        all_strategies = {
            **self.clash_royale_database.get("opening_strategies", {}),
            **self.clash_royale_database.get("mid_game_strategies", {}),
            **self.clash_royale_database.get("late_game_strategies", {}),
            **self.clash_royale_database.get("prediction_strategies", {}),
            **self.clash_royale_database.get("advanced_tactics", {})
        }
        
        strategy_data = all_strategies.get(strategy_name, {})
        moves = strategy_data.get("moves", [])
        
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


# Instância global da base de conhecimento
knowledge_base = KnowledgeBase()

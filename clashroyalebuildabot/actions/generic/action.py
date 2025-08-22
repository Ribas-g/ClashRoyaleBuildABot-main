from abc import ABC
from abc import abstractmethod
from typing import Dict, Optional

from clashroyalebuildabot.namespaces.cards import Card
from clashroyalebuildabot.knowledge_base import knowledge_base


class Action(ABC):
    CARD: Card = None

    def __init__(self, index, tile_x, tile_y):
        self.index = index
        self.tile_x = tile_x
        self.tile_y = tile_y
        self._optimal_positioning = None

    def __repr__(self):
        return f"{self.CARD.name} at ({self.tile_x}, {self.tile_y})"

    @abstractmethod
    def calculate_score(self, state):
        pass
    
    def get_optimal_positioning(self, state, situation: str = "default") -> Dict:
        """Retorna posicionamento ótimo baseado no banco de dados"""
        if self._optimal_positioning is None:
            card_name = self.CARD.name.lower() if self.CARD else "unknown"
            self._optimal_positioning = knowledge_base.get_optimal_positioning_from_database(
                card_name, situation
            )
        return self._optimal_positioning
    
    def should_use_intelligent_positioning(self, state) -> bool:
        """Determina se deve usar posicionamento inteligente"""
        # Verifica se temos dados suficientes para posicionamento inteligente
        if not state or not hasattr(state, 'numbers') or not state.numbers:
            return False
        
        # Verifica se temos elixir suficiente
        elixir = getattr(state.numbers, 'elixir', None)
        if not elixir or not hasattr(elixir, 'number'):
            return False
        
        return elixir.number >= 3  # Só usa posicionamento inteligente com elixir suficiente
    
    def get_situation_based_positioning(self, state) -> str:
        """Determina a situação atual para posicionamento"""
        if not state or not hasattr(state, 'numbers'):
            return "default"
        
        # Análise básica da situação
        try:
            # Verifica se está sob pressão
            left_hp = getattr(state.numbers, 'left_ally_princess_hp', None)
            right_hp = getattr(state.numbers, 'right_ally_princess_hp', None)
            
            if left_hp and right_hp and hasattr(left_hp, 'number') and hasattr(right_hp, 'number'):
                if left_hp.number < 1000 or right_hp.number < 1000:
                    return "defensive"
            
            # Verifica se tem vantagem
            enemy_left_hp = getattr(state.numbers, 'left_enemy_princess_hp', None)
            enemy_right_hp = getattr(state.numbers, 'right_enemy_princess_hp', None)
            
            if (enemy_left_hp and enemy_right_hp and 
                hasattr(enemy_left_hp, 'number') and hasattr(enemy_right_hp, 'number')):
                our_total = (left_hp.number if left_hp else 1000) + (right_hp.number if right_hp else 1000)
                enemy_total = enemy_left_hp.number + enemy_right_hp.number
                
                if our_total > enemy_total + 1000:  # Vantagem significativa
                    return "offensive"
            
            # Verifica elixir
            elixir = getattr(state.numbers, 'elixir', None)
            if elixir and hasattr(elixir, 'number'):
                if elixir.number >= 8:
                    return "offensive"
                elif elixir.number <= 3:
                    return "defensive"
            
        except Exception:
            pass
        
        return "default"

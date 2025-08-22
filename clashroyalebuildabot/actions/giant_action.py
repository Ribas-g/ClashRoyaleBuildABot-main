from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.generic.action import Action


class GiantAction(Action):
    CARD = Cards.GIANT

    def calculate_score(self, state):
        if state.numbers.elixir.number != 10:
            return [0]

        # Usa posicionamento inteligente se disponível
        if self.should_use_intelligent_positioning(state):
            situation = self.get_situation_based_positioning(state)
            optimal_pos = self.get_optimal_positioning(state, situation)
            
            if optimal_pos and optimal_pos.get("tile_x") == self.tile_x and optimal_pos.get("tile_y") == self.tile_y:
                # Bônus para posicionamento ótimo
                base_score = 1.5
            else:
                base_score = 1.0
        else:
            base_score = 1.0

        left_hp = state.numbers.left_enemy_princess_hp.number
        right_hp = state.numbers.right_enemy_princess_hp.number

        if (self.tile_x, self.tile_y) == (3, 15):
            return [base_score, left_hp > 0, left_hp <= right_hp]

        if (self.tile_x, self.tile_y) == (14, 15):
            return [base_score, right_hp > 0, right_hp <= left_hp]

        return [0]

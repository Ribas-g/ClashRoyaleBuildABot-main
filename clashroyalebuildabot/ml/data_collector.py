"""
Data collection system for machine learning training
"""

import json
import os
from datetime import datetime
from loguru import logger


class GameDataCollector:
    def __init__(self, save_path="game_data.json"):
        self.save_path = save_path
        self.current_game = None
        self.game_history = []
        self.load_existing_data()
    
    def load_existing_data(self):
        """Carrega dados existentes se disponíveis"""
        try:
            if os.path.exists(self.save_path):
                with open(self.save_path, 'r') as f:
                    self.game_history = json.load(f)
                logger.info(f"Loaded {len(self.game_history)} existing games")
        except Exception as e:
            logger.warning(f"Could not load existing data: {e}")
            self.game_history = []
    
    def start_new_game(self):
        """Inicia uma nova partida para coleta de dados"""
        self.current_game = {
            'timestamp': datetime.now().isoformat(),
            'actions': [],
            'states': [],
            'rewards': [],
            'result': None,
            'game_id': len(self.game_history) + 1
        }
        logger.info("Started new game data collection")
    
    def record_action(self, action, state, reward):
        """Registra uma ação e seu resultado"""
        if self.current_game:
            action_data = {
                'action': str(action),
                'action_index': action.index,
                'tile_x': action.tile_x,
                'tile_y': action.tile_y,
                'reward': reward,
                'elixir': state.numbers.elixir.number,
                'ally_towers': [
                    state.numbers.left_ally_princess_hp.number,
                    state.numbers.right_ally_princess_hp.number
                ],
                'enemy_towers': [
                    state.numbers.left_enemy_princess_hp.number,
                    state.numbers.right_enemy_princess_hp.number
                ],
                'allies_count': len(state.allies),
                'enemies_count': len(state.enemies),
                'ready_cards': list(state.ready),
                'timestamp': datetime.now().isoformat()
            }
            
            self.current_game['actions'].append(action_data)
            logger.debug(f"Recorded action: {action} with reward {reward}")
    
    def end_game(self, result):
        """Finaliza a partida e salva os dados"""
        if self.current_game:
            self.current_game['result'] = result
            self.current_game['duration'] = len(self.current_game['actions'])
            self.game_history.append(self.current_game)
            self.save_data()
            
            logger.info(f"Game ended with result: {result}. "
                       f"Recorded {len(self.current_game['actions'])} actions")
            
            self.current_game = None
    
    def save_data(self):
        """Salva os dados coletados em arquivo JSON"""
        try:
            with open(self.save_path, 'w') as f:
                json.dump(self.game_history, f, indent=2)
            logger.debug(f"Saved {len(self.game_history)} games to {self.save_path}")
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
    
    def get_training_data(self):
        """Retorna dados formatados para treinamento"""
        return self.game_history
    
    def get_stats(self):
        """Retorna estatísticas dos dados coletados"""
        if not self.game_history:
            return {
                'total_games': 0,
                'total_actions': 0,
                'win_rate': 0,
                'avg_actions_per_game': 0
            }
        
        total_games = len(self.game_history)
        total_actions = sum(len(game['actions']) for game in self.game_history)
        wins = sum(1 for game in self.game_history if game.get('result') == 'win')
        
        return {
            'total_games': total_games,
            'total_actions': total_actions,
            'win_rate': wins / total_games if total_games > 0 else 0,
            'avg_actions_per_game': total_actions / total_games if total_games > 0 else 0
        }

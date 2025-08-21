"""
Machine Learning model for Clash Royale Bot
"""

import os
import numpy as np
import joblib
from loguru import logger
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


class MLBot:
    def __init__(self, model_path="ml_model.pkl"):
        self.model_path = model_path
        self.model = RandomForestRegressor(
            n_estimators=100, 
            random_state=42,
            max_depth=10
        )
        self.scaler = StandardScaler()
        self.trained = False
        self.load_model()
    
    def extract_features(self, state, enemy_analysis=None):
        """Extrai características do estado do jogo"""
        features = []
        
        # Estado básico do jogo
        features.extend([
            state.numbers.elixir.number,
            state.numbers.left_ally_princess_hp.number,
            state.numbers.right_ally_princess_hp.number,
            state.numbers.left_enemy_princess_hp.number,
            state.numbers.right_enemy_princess_hp.number,
            len(state.allies),
            len(state.enemies),
            len(state.ready)
        ])
        
        # Cartas disponíveis (one-hot encoding)
        for i in range(8):
            features.append(1 if i in state.ready else 0)
        
        # Características das unidades no campo
        ally_types = [unit.unit.name for unit in state.allies]
        enemy_types = [unit.unit.name for unit in state.enemies]
        
        # Conta tipos de unidades
        features.extend([
            ally_types.count('knight'),
            ally_types.count('archers'),
            ally_types.count('musketeer'),
            ally_types.count('giant'),
            ally_types.count('witch'),
            ally_types.count('baby_dragon'),
            enemy_types.count('knight'),
            enemy_types.count('archers'),
            enemy_types.count('musketeer'),
            enemy_types.count('giant'),
            enemy_types.count('witch'),
            enemy_types.count('baby_dragon')
        ])
        
        # Características do deck do inimigo (se disponível)
        if enemy_analysis:
            # Número de cartas conhecidas do inimigo
            features.append(enemy_analysis.get('cards_played', 0))
            
            # Confiança da predição do deck
            deck_pred = enemy_analysis.get('deck_prediction', {})
            features.append(deck_pred.get('confidence', 0))
            
            # Número de fraquezas identificadas
            features.append(len(enemy_analysis.get('weaknesses', [])))
            
            # Número de estratégias sugeridas
            features.append(len(enemy_analysis.get('strategies', [])))
            
            # Cartas esperadas do inimigo
            expected_cards = enemy_analysis.get('next_expected', [])
            features.append(len(expected_cards))
            
            # Probabilidade média das cartas esperadas
            if expected_cards:
                avg_prob = sum(card.get('probability', 0) for card in expected_cards) / len(expected_cards)
                features.append(avg_prob)
            else:
                features.append(0)
        else:
            # Valores padrão se não há análise do inimigo
            features.extend([0, 0, 0, 0, 0, 0])
        
        return np.array(features).reshape(1, -1)
    
    def predict_action_score(self, state, action, enemy_analysis=None):
        """Prediz o score de uma ação específica"""
        if not self.trained:
            return 0.5  # Score neutro se não treinado
        
        try:
            # Extrai características do estado
            state_features = self.extract_features(state, enemy_analysis)
            state_features_scaled = self.scaler.transform(state_features)
            
            # Características da ação
            action_features = np.array([
                action.index,  # Índice da carta
                action.tile_x,  # Posição X
                action.tile_y,  # Posição Y
                # Normaliza posições
                action.tile_x / 18.0,  # Normaliza X (0-18)
                action.tile_y / 15.0,  # Normaliza Y (0-15)
            ]).reshape(1, -1)
            
            # Combina características
            combined_features = np.hstack([state_features_scaled, action_features])
            
            # Prediz o score
            predicted_score = self.model.predict(combined_features)[0]
            
            # Normaliza o score entre 0 e 1
            predicted_score = max(0.0, min(1.0, predicted_score))
            
            return predicted_score
            
        except Exception as e:
            logger.warning(f"ML prediction failed: {e}")
            return 0.5  # Score neutro em caso de erro
    
    def train(self, game_data):
        """Treina o modelo com dados de partidas"""
        if not game_data or len(game_data) < 2:
            logger.info("Not enough data to train ML model")
            return
        
        try:
            X = []  # Features
            y = []  # Rewards
            
            for game in game_data:
                if game.get('result') is None:
                    continue
                
                # Calcula recompensa final baseada no resultado
                game_result = game['result']
                final_reward = 1.0 if game_result == 'win' else -0.5 if game_result == 'lose' else 0.0
                
                for i, action_data in enumerate(game['actions']):
                    # Features do estado
                    features = np.array([
                        action_data['elixir'],
                        action_data['ally_towers'][0],
                        action_data['ally_towers'][1],
                        action_data['enemy_towers'][0],
                        action_data['enemy_towers'][1],
                        action_data['allies_count'],
                        action_data['enemies_count'],
                        len(action_data['ready_cards']),
                        # Cartas disponíveis
                        1 if 0 in action_data['ready_cards'] else 0,
                        1 if 1 in action_data['ready_cards'] else 0,
                        1 if 2 in action_data['ready_cards'] else 0,
                        1 if 3 in action_data['ready_cards'] else 0,
                        1 if 4 in action_data['ready_cards'] else 0,
                        1 if 5 in action_data['ready_cards'] else 0,
                        1 if 6 in action_data['ready_cards'] else 0,
                        1 if 7 in action_data['ready_cards'] else 0,
                        # Características da ação
                        action_data['action_index'],
                        action_data['tile_x'],
                        action_data['tile_y'],
                        action_data['tile_x'] / 18.0,
                        action_data['tile_y'] / 15.0
                    ])
                    
                    X.append(features)
                    
                    # Recompensa: combina recompensa imediata com resultado final
                    immediate_reward = action_data.get('reward', 0)
                    # Peso maior para ações no final da partida
                    time_weight = (i + 1) / len(game['actions'])
                    combined_reward = immediate_reward + (final_reward * time_weight)
                    y.append(combined_reward)
            
            if len(X) < 10:
                logger.info("Not enough training samples")
                return
            
            X = np.array(X)
            y = np.array(y)
            
            # Normaliza as features
            X_scaled = self.scaler.fit_transform(X)
            
            # Treina o modelo
            self.model.fit(X_scaled, y)
            self.trained = True
            self.save_model()
            
            logger.info(f"ML model trained with {len(X)} samples from {len(game_data)} games")
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
    
    def save_model(self):
        """Salva o modelo treinado"""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'trained': self.trained
            }
            joblib.dump(model_data, self.model_path)
            logger.info(f"ML model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def load_model(self):
        """Carrega modelo treinado se disponível"""
        try:
            if os.path.exists(self.model_path):
                data = joblib.load(self.model_path)
                self.model = data['model']
                self.scaler = data['scaler']
                self.trained = data['trained']
                logger.info("ML model loaded successfully")
            else:
                self.trained = False
                logger.info("No existing ML model found")
        except Exception as e:
            logger.warning(f"Failed to load ML model: {e}")
            self.trained = False
    
    def get_model_info(self):
        """Retorna informações sobre o modelo"""
        return {
            'trained': self.trained,
            'model_path': self.model_path,
            'model_type': 'RandomForestRegressor',
            'n_estimators': self.model.n_estimators if self.trained else 0
        }

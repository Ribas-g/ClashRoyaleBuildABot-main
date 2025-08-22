"""
Machine Learning model for Clash Royale Bot
"""

import os
import numpy as np
import joblib
from typing import Dict
from loguru import logger
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


class MLBot:
    def __init__(self, model_path="ml_model.pkl", generation_manager=None):
        self.model_path = model_path
        self.generation_manager = generation_manager
        
        try:
            self.model = RandomForestRegressor(
                n_estimators=100, 
                random_state=42,
                max_depth=10
            )
            logger.debug("RandomForestRegressor initialized")
        except Exception as e:
            logger.error(f"Error initializing RandomForestRegressor: {e}")
            raise
        
        try:
            self.scaler = StandardScaler()
            logger.debug("StandardScaler initialized")
        except Exception as e:
            logger.error(f"Error initializing StandardScaler: {e}")
            raise
        
        self.trained = False
        
        # Tentar carregar melhor geração se disponível
        if self.generation_manager:
            try:
                best_model, best_scaler, gen_info = self.generation_manager.load_best_generation()
                if best_model is not None:
                    self.model = best_model
                    self.scaler = best_scaler
                    self.trained = True
                    logger.info(f"Loaded best generation from generation manager")
                else:
                    self.load_model()  # Fallback para modelo local
            except Exception as e:
                logger.warning(f"Error loading from generation manager: {e}")
                self.load_model()  # Fallback para modelo local
        else:
            try:
                self.load_model()
                logger.debug("Model loading completed")
            except Exception as e:
                logger.warning(f"Error loading model (this is normal for first run): {e}")
                # Não falhar se não há modelo salvo
    
    def extract_features(self, state, enemy_analysis=None):
        """Extrai características do estado do jogo"""
        features = []
        
        # Estado básico do jogo com verificações de segurança
        try:
            elixir = state.numbers.elixir.number if hasattr(state.numbers, 'elixir') and state.numbers.elixir is not None else 0
            left_ally_hp = state.numbers.left_ally_princess_hp.number if hasattr(state.numbers, 'left_ally_princess_hp') and state.numbers.left_ally_princess_hp is not None else 0
            right_ally_hp = state.numbers.right_ally_princess_hp.number if hasattr(state.numbers, 'right_ally_princess_hp') and state.numbers.right_ally_princess_hp is not None else 0
            left_enemy_hp = state.numbers.left_enemy_princess_hp.number if hasattr(state.numbers, 'left_enemy_princess_hp') and state.numbers.left_enemy_princess_hp is not None else 0
            right_enemy_hp = state.numbers.right_enemy_princess_hp.number if hasattr(state.numbers, 'right_enemy_princess_hp') and state.numbers.right_enemy_princess_hp is not None else 0
            
            features.extend([
                elixir,
                left_ally_hp,
                right_ally_hp,
                left_enemy_hp,
                right_enemy_hp,
                len(state.allies) if hasattr(state, 'allies') else 0,
                len(state.enemies) if hasattr(state, 'enemies') else 0,
                len(state.ready) if hasattr(state, 'ready') else 0
            ])
        except Exception as e:
            logger.warning(f"Error extracting basic features: {e}")
            # Valores padrão em caso de erro
            features.extend([0, 0, 0, 0, 0, 0, 0, 0])
        
        # Cartas disponíveis (one-hot encoding)
        try:
            ready_cards = state.ready if hasattr(state, 'ready') else []
            for i in range(8):
                features.append(1 if i in ready_cards else 0)
        except Exception as e:
            logger.warning(f"Error extracting ready cards: {e}")
            features.extend([0] * 8)
        
        # Características das unidades no campo
        try:
            allies = state.allies if hasattr(state, 'allies') else []
            enemies = state.enemies if hasattr(state, 'enemies') else []
            
            ally_types = [unit.unit.name for unit in allies if hasattr(unit, 'unit') and hasattr(unit.unit, 'name')]
            enemy_types = [unit.unit.name for unit in enemies if hasattr(unit, 'unit') and hasattr(unit.unit, 'name')]
        except Exception as e:
            logger.warning(f"Error extracting unit types: {e}")
            ally_types = []
            enemy_types = []
        
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
        try:
            if enemy_analysis and isinstance(enemy_analysis, dict):
                # Número de cartas conhecidas do inimigo
                features.append(enemy_analysis.get('cards_played', 0))
                
                # Confiança da predição do deck
                deck_pred = enemy_analysis.get('deck_prediction', {})
                features.append(deck_pred.get('confidence', 0) if isinstance(deck_pred, dict) else 0)
                
                # Número de fraquezas identificadas
                weaknesses = enemy_analysis.get('weaknesses', [])
                features.append(len(weaknesses) if isinstance(weaknesses, list) else 0)
                
                # Número de estratégias sugeridas
                strategies = enemy_analysis.get('strategies', [])
                features.append(len(strategies) if isinstance(strategies, list) else 0)
                
                # Cartas esperadas do inimigo
                expected_cards = enemy_analysis.get('next_expected', [])
                features.append(len(expected_cards) if isinstance(expected_cards, list) else 0)
                
                # Probabilidade média das cartas esperadas
                if expected_cards and isinstance(expected_cards, list):
                    try:
                        avg_prob = sum(card.get('probability', 0) for card in expected_cards if isinstance(card, dict)) / len(expected_cards)
                        features.append(avg_prob)
                    except (ZeroDivisionError, TypeError):
                        features.append(0)
                else:
                    features.append(0)
            else:
                # Valores padrão se não há análise do inimigo
                features.extend([0, 0, 0, 0, 0, 0])
        except Exception as e:
            logger.warning(f"Error extracting enemy analysis features: {e}")
            # Valores padrão em caso de erro
            features.extend([0, 0, 0, 0, 0, 0])
        
        return np.array(features).reshape(1, -1)
    
    def predict_action_score(self, state, action, enemy_analysis=None):
        """Prediz o score de uma ação específica"""
        if not self.trained:
            return 0.5  # Score neutro se não treinado
        
        try:
            # Extrai características do estado
            state_features = self.extract_features(state, enemy_analysis)
            
            # Verificar se o scaler foi treinado
            if not hasattr(self.scaler, 'mean_') or self.scaler.mean_ is None:
                logger.warning("Scaler not trained, using raw features")
                state_features_scaled = state_features
            else:
                # Verificar compatibilidade de features
                expected_features = self.scaler.n_features_in_
                actual_features = state_features.shape[1]
                
                if expected_features != actual_features:
                    logger.warning(f"Feature mismatch: expected {expected_features}, got {actual_features}. Using neutral score.")
                    return 0.5
                
                state_features_scaled = self.scaler.transform(state_features)
            
            # Características da ação com verificações de segurança
            try:
                action_index = action.index if hasattr(action, 'index') else 0
                tile_x = action.tile_x if hasattr(action, 'tile_x') else 0
                tile_y = action.tile_y if hasattr(action, 'tile_y') else 0
                
                action_features = np.array([
                    action_index,  # Índice da carta
                    tile_x,  # Posição X
                    tile_y,  # Posição Y
                    # Normaliza posições
                    tile_x / 18.0,  # Normaliza X (0-18)
                    tile_y / 15.0,  # Normaliza Y (0-15)
                ]).reshape(1, -1)
            except Exception as e:
                logger.warning(f"Error extracting action features: {e}")
                # Valores padrão em caso de erro
                action_features = np.array([0, 0, 0, 0, 0]).reshape(1, -1)
            
            # Combina características
            combined_features = np.hstack([state_features_scaled, action_features])
            
            # Verificar se o modelo foi treinado
            if not hasattr(self.model, 'predict'):
                logger.warning("Model not properly trained, returning neutral score")
                return 0.5
            
            # Verificar compatibilidade de features do modelo
            if hasattr(self.model, 'n_features_in_'):
                expected_model_features = self.model.n_features_in_
                actual_combined_features = combined_features.shape[1]
                
                if expected_model_features != actual_combined_features:
                    logger.warning(f"Model feature mismatch: expected {expected_model_features}, got {actual_combined_features}. Using neutral score.")
                    return 0.5
            
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
    
    def evolve_if_needed(self, performance_metrics: Dict, games_played: int) -> bool:
        """Verifica se deve evoluir e cria nova geração se necessário"""
        if not self.generation_manager:
            return False
        
        try:
            if self.generation_manager.should_evolve(performance_metrics, games_played):
                # Criar nova geração
                generation_id = self.generation_manager.create_new_generation(
                    self.model, self.scaler, performance_metrics
                )
                
                if generation_id > 0:
                    logger.info(f"🎯 EVOLUTION: Created generation {generation_id}")
                    logger.info(f"📊 Performance: Win rate {performance_metrics.get('win_rate', 0):.2%}")
                    
                    # Carregar a melhor geração (que pode ser a nova)
                    best_model, best_scaler, gen_info = self.generation_manager.load_best_generation()
                    if best_model is not None:
                        self.model = best_model
                        self.scaler = best_scaler
                        logger.info("🔄 Loaded best generation after evolution")
                    
                    return True
                else:
                    logger.warning("Failed to create new generation")
            
            return False
            
        except Exception as e:
            logger.error(f"Error in evolution: {e}")
            return False
    
    def get_generation_info(self) -> Dict:
        """Retorna informações sobre gerações"""
        if not self.generation_manager:
            return {'generations_enabled': False}
        
        try:
            stats = self.generation_manager.get_generation_statistics()
            recommendations = self.generation_manager.get_evolution_recommendations({})
            
            return {
                'generations_enabled': True,
                'statistics': stats,
                'recommendations': recommendations
            }
        except Exception as e:
            logger.error(f"Error getting generation info: {e}")
            return {'generations_enabled': False, 'error': str(e)}

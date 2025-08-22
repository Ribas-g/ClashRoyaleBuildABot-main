"""
Sistema de Deep Learning Avançado
Implementa redes neurais para aprendizado profundo do jogo
"""
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict, Tuple, Optional
from loguru import logger
import json
import os


class ClashRoyaleNet(nn.Module):
    """Rede neural para Clash Royale"""
    
    def __init__(self, input_size=128, hidden_size=256, output_size=64):
        super(ClashRoyaleNet, self).__init__()
        
        # Camadas da rede
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU()
        )
        
        # Head para valor (V)
        self.value_head = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Linear(hidden_size // 4, 1),
            nn.Tanh()  # Valor entre -1 e 1
        )
        
        # Head para política (P)
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Linear(hidden_size // 4, output_size),
            nn.Softmax(dim=1)
        )
        
        # Head para ação específica
        self.action_head = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Linear(hidden_size // 4, 8),  # 8 cartas
            nn.Softmax(dim=1)
        )
    
    def forward(self, x):
        features = self.feature_extractor(x)
        value = self.value_head(features)
        policy = self.policy_head(features)
        action = self.action_head(features)
        
        return value, policy, action


class GameStateDataset(Dataset):
    """Dataset para dados de estado do jogo"""
    
    def __init__(self, game_data: List[Dict]):
        self.data = []
        
        for game in game_data:
            if game.get('result') is None:
                continue
            
            # Converter resultado para valor
            result_value = 1.0 if game['result'] == 'win' else -1.0 if game['result'] == 'lose' else 0.0
            
            for action_data in game['actions']:
                # Features do estado
                features = self._extract_features(action_data)
                
                # Target para valor
                value_target = result_value
                
                # Target para política (one-hot encoding da ação tomada)
                policy_target = np.zeros(64)  # 64 possíveis ações
                action_index = action_data.get('action_index', 0)
                if action_index < 64:
                    policy_target[action_index] = 1.0
                
                # Target para ação específica
                action_target = np.zeros(8)  # 8 cartas
                card_index = action_data.get('card_index', 0)
                if card_index < 8:
                    action_target[card_index] = 1.0
                
                self.data.append({
                    'features': features,
                    'value_target': value_target,
                    'policy_target': policy_target,
                    'action_target': action_target
                })
    
    def _extract_features(self, action_data: Dict) -> np.ndarray:
        """Extrai features do estado do jogo"""
        features = []
        
        # Estado básico
        features.extend([
            action_data.get('elixir', 0) / 10.0,  # Normalizar elixir
            action_data.get('ally_towers', [1.0, 1.0])[0],
            action_data.get('ally_towers', [1.0, 1.0])[1],
            action_data.get('enemy_towers', [1.0, 1.0])[0],
            action_data.get('enemy_towers', [1.0, 1.0])[1],
            action_data.get('allies_count', 0) / 10.0,
            action_data.get('enemies_count', 0) / 10.0,
        ])
        
        # Cartas disponíveis (one-hot encoding)
        ready_cards = action_data.get('ready_cards', [])
        for i in range(8):
            features.append(1.0 if i in ready_cards else 0.0)
        
        # Posição da ação
        features.extend([
            action_data.get('tile_x', 9) / 18.0,  # Normalizar X
            action_data.get('tile_y', 7) / 15.0,  # Normalizar Y
        ])
        
        # Features avançadas (preencher com zeros se não disponível)
        advanced_features = [0.0] * 100  # Placeholder para features avançadas
        features.extend(advanced_features)
        
        return np.array(features, dtype=np.float32)
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        return {
            'features': torch.FloatTensor(item['features']),
            'value_target': torch.FloatTensor([item['value_target']]),
            'policy_target': torch.FloatTensor(item['policy_target']),
            'action_target': torch.FloatTensor(item['action_target'])
        }


class DeepLearningSystem:
    """Sistema de deep learning para Clash Royale"""
    
    def __init__(self, model_path="deep_learning_model.pth"):
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Inicializar modelo
        self.model = ClashRoyaleNet().to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        
        # Configurações de treinamento
        self.batch_size = 32
        self.epochs = 10
        self.learning_rate = 0.001
        
        # Carregar modelo se existir
        self.load_model()
    
    def train(self, game_data: List[Dict]):
        """Treina o modelo com dados de partidas"""
        try:
            if len(game_data) < 5:
                logger.info("Not enough data for deep learning training")
                return
            
            # Criar dataset
            dataset = GameStateDataset(game_data)
            dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
            
            logger.info(f"Training deep learning model with {len(dataset)} samples")
            
            # Critérios de loss
            value_criterion = nn.MSELoss()
            policy_criterion = nn.CrossEntropyLoss()
            action_criterion = nn.CrossEntropyLoss()
            
            # Treinamento
            self.model.train()
            for epoch in range(self.epochs):
                total_loss = 0
                
                for batch in dataloader:
                    features = batch['features'].to(self.device)
                    value_targets = batch['value_target'].to(self.device)
                    policy_targets = batch['policy_target'].to(self.device)
                    action_targets = batch['action_target'].to(self.device)
                    
                    # Forward pass
                    value_pred, policy_pred, action_pred = self.model(features)
                    
                    # Calcular losses
                    value_loss = value_criterion(value_pred, value_targets)
                    policy_loss = policy_criterion(policy_pred, policy_targets)
                    action_loss = action_criterion(action_pred, action_targets)
                    
                    # Loss total
                    total_batch_loss = value_loss + policy_loss + action_loss
                    
                    # Backward pass
                    self.optimizer.zero_grad()
                    total_batch_loss.backward()
                    self.optimizer.step()
                    
                    total_loss += total_batch_loss.item()
                
                avg_loss = total_loss / len(dataloader)
                logger.info(f"Epoch {epoch+1}/{self.epochs}, Average Loss: {avg_loss:.4f}")
            
            # Salvar modelo
            self.save_model()
            logger.info("Deep learning model training completed")
            
        except Exception as e:
            logger.error(f"Error in deep learning training: {e}")
    
    def predict_action(self, game_state: Dict) -> Dict:
        """Prediz a melhor ação baseada no estado do jogo"""
        try:
            self.model.eval()
            
            # Extrair features do estado
            features = self._extract_state_features(game_state)
            features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                value_pred, policy_pred, action_pred = self.model(features_tensor)
            
            # Converter predições
            value = value_pred.item()
            policy_probs = policy_pred.cpu().numpy()[0]
            action_probs = action_pred.cpu().numpy()[0]
            
            # Encontrar melhor ação
            best_action_idx = np.argmax(policy_probs)
            best_card_idx = np.argmax(action_probs)
            
            return {
                'value': value,
                'best_action': best_action_idx,
                'best_card': best_card_idx,
                'action_confidence': policy_probs[best_action_idx],
                'card_confidence': action_probs[best_card_idx],
                'all_action_probs': policy_probs.tolist(),
                'all_card_probs': action_probs.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in action prediction: {e}")
            return {
                'value': 0.0,
                'best_action': 0,
                'best_card': 0,
                'action_confidence': 0.0,
                'card_confidence': 0.0
            }
    
    def _extract_state_features(self, game_state: Dict) -> np.ndarray:
        """Extrai features do estado atual do jogo"""
        features = []
        
        # Estado básico
        features.extend([
            game_state.get('elixir', 0) / 10.0,
            game_state.get('ally_tower_health', [1.0, 1.0])[0],
            game_state.get('ally_tower_health', [1.0, 1.0])[1],
            game_state.get('enemy_tower_health', [1.0, 1.0])[0],
            game_state.get('enemy_tower_health', [1.0, 1.0])[1],
            len(game_state.get('ally_units', [])) / 10.0,
            len(game_state.get('enemy_units', [])) / 10.0,
        ])
        
        # Cartas disponíveis
        ready_cards = game_state.get('ready_cards', [])
        for i in range(8):
            features.append(1.0 if i in ready_cards else 0.0)
        
        # Posição atual (padrão)
        features.extend([9.0/18.0, 7.0/15.0])
        
        # Features avançadas
        advanced_features = [0.0] * 100
        features.extend(advanced_features)
        
        return np.array(features, dtype=np.float32)
    
    def save_model(self):
        """Salva o modelo treinado"""
        try:
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'model_config': {
                    'input_size': 128,
                    'hidden_size': 256,
                    'output_size': 64
                }
            }, self.model_path)
            logger.info(f"Deep learning model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving deep learning model: {e}")
    
    def load_model(self):
        """Carrega modelo treinado"""
        try:
            if os.path.exists(self.model_path):
                checkpoint = torch.load(self.model_path, map_location=self.device)
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                logger.info("Deep learning model loaded successfully")
            else:
                logger.info("No existing deep learning model found")
        except Exception as e:
            logger.warning(f"Error loading deep learning model: {e}")
    
    def get_model_info(self) -> Dict:
        """Retorna informações sobre o modelo"""
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        return {
            'model_type': 'ClashRoyaleNet',
            'device': str(self.device),
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'model_path': self.model_path,
            'batch_size': self.batch_size,
            'learning_rate': self.learning_rate
        }

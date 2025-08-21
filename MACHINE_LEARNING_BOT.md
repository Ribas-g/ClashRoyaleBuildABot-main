# 🤖 Machine Learning no Bot Clash Royale

## 📊 Status Atual do Bot

### **O que o bot já tem:**
✅ **ONNX Runtime** - Para detecção de objetos  
✅ **Modelos pré-treinados** - Para reconhecer cartas e unidades  
✅ **Sistema de pontuação** - Cada ação tem um `calculate_score()`  
✅ **Detecção de estado** - Reconhece o que está acontecendo no jogo  

### **O que o bot NÃO tem ainda:**
❌ **Aprendizado de máquina** - Não aprende com as partidas  
❌ **Reinforcement Learning** - Não melhora com experiência  
❌ **Análise de resultados** - Não avalia se jogou bem  
❌ **Adaptação dinâmica** - Não ajusta estratégia automaticamente  

## 🧠 Como Implementar Machine Learning

### **1. Sistema de Recompensas (Reinforcement Learning)**

O bot precisa aprender se suas jogadas foram boas ou ruins:

```python
class GameReward:
    def __init__(self):
        self.rewards = {
            'tower_damage': 10,      # Dano na torre inimiga
            'tower_lost': -20,       # Perder torre
            'elixir_efficiency': 5,  # Usar elixir eficientemente
            'counter_play': 8,       # Contra-jogada boa
            'bad_positioning': -5,   # Posicionamento ruim
            'win': 100,              # Ganhar partida
            'lose': -50              # Perder partida
        }
```

### **2. Coleta de Dados de Treinamento**

```python
class GameDataCollector:
    def __init__(self):
        self.game_history = []
        self.current_game = {
            'actions': [],
            'states': [],
            'rewards': [],
            'result': None
        }
    
    def record_action(self, action, state, reward):
        self.current_game['actions'].append(action)
        self.current_game['states'].append(state)
        self.current_game['rewards'].append(reward)
    
    def end_game(self, result):
        self.current_game['result'] = result
        self.game_history.append(self.current_game)
        self.save_data()
```

### **3. Modelo de Machine Learning**

```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

class MLBot:
    def __init__(self):
        self.model = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            max_iter=1000,
            random_state=42
        )
        self.trained = False
    
    def extract_features(self, state):
        """Extrai características do estado do jogo"""
        features = []
        
        # Elixir disponível
        features.append(state.numbers.elixir.number)
        
        # HP das torres
        features.append(state.numbers.left_ally_princess_hp.number)
        features.append(state.numbers.right_ally_princess_hp.number)
        features.append(state.numbers.left_enemy_princess_hp.number)
        features.append(state.numbers.right_enemy_princess_hp.number)
        
        # Número de unidades no campo
        features.append(len(state.allies))
        features.append(len(state.enemies))
        
        # Cartas disponíveis
        for i in range(8):
            if i in state.ready:
                features.append(1)
            else:
                features.append(0)
        
        return np.array(features)
    
    def predict_best_action(self, state, available_actions):
        if not self.trained:
            return random.choice(available_actions)
        
        features = self.extract_features(state)
        predictions = []
        
        for action in available_actions:
            # Simula o resultado da ação
            predicted_reward = self.model.predict_proba([features])[0]
            predictions.append((action, predicted_reward[1]))
        
        # Retorna a ação com maior probabilidade de sucesso
        best_action = max(predictions, key=lambda x: x[1])[0]
        return best_action
```

## 🚀 Implementação Prática

### **Passo 1: Criar o Sistema de Coleta de Dados**

```python
# clashroyalebuildabot/ml/data_collector.py
import json
import time
from datetime import datetime

class GameDataCollector:
    def __init__(self, save_path="game_data.json"):
        self.save_path = save_path
        self.current_game = None
        self.game_history = []
    
    def start_new_game(self):
        self.current_game = {
            'timestamp': datetime.now().isoformat(),
            'actions': [],
            'states': [],
            'rewards': [],
            'result': None
        }
    
    def record_action(self, action, state, reward):
        if self.current_game:
            self.current_game['actions'].append({
                'action': str(action),
                'reward': reward,
                'elixir': state.numbers.elixir.number,
                'ally_towers': [
                    state.numbers.left_ally_princess_hp.number,
                    state.numbers.right_ally_princess_hp.number
                ],
                'enemy_towers': [
                    state.numbers.left_enemy_princess_hp.number,
                    state.numbers.right_enemy_princess_hp.number
                ]
            })
    
    def end_game(self, result):
        if self.current_game:
            self.current_game['result'] = result
            self.game_history.append(self.current_game)
            self.save_data()
    
    def save_data(self):
        with open(self.save_path, 'w') as f:
            json.dump(self.game_history, f, indent=2)
```

### **Passo 2: Criar o Modelo de ML**

```python
# clashroyalebuildabot/ml/ml_bot.py
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

class MLBot:
    def __init__(self, model_path="ml_model.pkl"):
        self.model_path = model_path
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.trained = False
        self.load_model()
    
    def extract_features(self, state):
        features = []
        
        # Estado do jogo
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
        
        # Cartas disponíveis
        for i in range(8):
            features.append(1 if i in state.ready else 0)
        
        return np.array(features).reshape(1, -1)
    
    def predict_action_score(self, state, action):
        if not self.trained:
            return 0.5  # Score neutro se não treinado
        
        features = self.extract_features(state)
        features_scaled = self.scaler.transform(features)
        
        # Adiciona características da ação
        action_features = np.array([
            action.index,  # Índice da carta
            action.tile_x,  # Posição X
            action.tile_y,  # Posição Y
        ]).reshape(1, -1)
        
        # Combina características
        combined_features = np.hstack([features_scaled, action_features])
        
        # Prediz o score
        predicted_score = self.model.predict(combined_features)[0]
        return predicted_score
    
    def train(self, game_data):
        if not game_data:
            return
        
        X = []  # Features
        y = []  # Rewards
        
        for game in game_data:
            for action_data in game['actions']:
                # Extrai features do estado
                features = np.array([
                    action_data['elixir'],
                    action_data['ally_towers'][0],
                    action_data['ally_towers'][1],
                    action_data['enemy_towers'][0],
                    action_data['enemy_towers'][1]
                ])
                
                X.append(features)
                y.append(action_data['reward'])
        
        if X and y:
            X = np.array(X)
            y = np.array(y)
            
            # Normaliza as features
            X_scaled = self.scaler.fit_transform(X)
            
            # Treina o modelo
            self.model.fit(X_scaled, y)
            self.trained = True
            self.save_model()
    
    def save_model(self):
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'trained': self.trained
        }, self.model_path)
    
    def load_model(self):
        try:
            data = joblib.load(self.model_path)
            self.model = data['model']
            self.scaler = data['scaler']
            self.trained = data['trained']
        except FileNotFoundError:
            self.trained = False
```

### **Passo 3: Integrar com o Bot Principal**

```python
# Modificar clashroyalebuildabot/bot/bot.py

from clashroyalebuildabot.ml.data_collector import GameDataCollector
from clashroyalebuildabot.ml.ml_bot import MLBot

class Bot:
    def __init__(self, actions, config):
        # ... código existente ...
        
        # Adicionar ML
        self.data_collector = GameDataCollector()
        self.ml_bot = MLBot()
        self.game_started = False
    
    def _handle_game_step(self):
        actions = self.get_actions()
        if not actions:
            self._log_and_wait("No actions available", self.play_action_delay)
            return
        
        # Iniciar coleta de dados se necessário
        if not self.game_started:
            self.data_collector.start_new_game()
            self.game_started = True
        
        # Usar ML para escolher a melhor ação
        best_action = None
        best_score = -float('inf')
        
        for action in actions:
            # Score original do bot
            original_score = action.calculate_score(self.state)
            
            # Score do ML (se treinado)
            ml_score = self.ml_bot.predict_action_score(self.state, action)
            
            # Combina os scores (70% ML, 30% original)
            combined_score = 0.7 * ml_score + 0.3 * original_score
            
            if combined_score > best_score:
                best_score = combined_score
                best_action = action
        
        if best_action:
            # Executa a ação
            self.play_action(best_action)
            
            # Calcula recompensa (simplificado)
            reward = self._calculate_reward(best_action)
            
            # Registra para treinamento
            self.data_collector.record_action(best_action, self.state, reward)
            
            self._log_and_wait(
                f"Playing {best_action} with ML score {best_score:.2f}",
                self.play_action_delay,
            )
    
    def _calculate_reward(self, action):
        """Calcula recompensa baseada no resultado da ação"""
        reward = 0
        
        # Recompensa base
        reward += action.calculate_score(self.state) / 100
        
        # Penalidade por usar muito elixir
        if self.state.numbers.elixir.number < 2:
            reward -= 0.5
        
        # Bônus por posicionamento defensivo
        if action.tile_y < 10:  # Lado defensivo
            reward += 0.2
        
        return reward
    
    def end_game(self, result):
        """Chamado quando a partida termina"""
        self.data_collector.end_game(result)
        self.game_started = False
        
        # Treina o modelo com os dados coletados
        self.ml_bot.train(self.data_collector.game_history)
```

## 📈 Como Usar o Sistema de ML

### **1. Instalar Dependências**

```bash
pip install scikit-learn joblib numpy
```

### **2. Configurar no config.yaml**

```yaml
bot:
  log_level: "INFO"
  load_deck: False
  auto_start_game: False
  enable_gui: True
  enable_ml: True  # Ativar machine learning

ml:
  enabled: True
  model_path: "ml_model.pkl"
  data_path: "game_data.json"
  training_frequency: 10  # Treinar a cada 10 partidas
```

### **3. Executar o Bot com ML**

```bash
python main.py
```

## 🎯 Benefícios do Machine Learning

### **1. Aprendizado Contínuo**
- O bot melhora com cada partida
- Aprende estratégias específicas do seu deck
- Adapta-se ao seu estilo de jogo

### **2. Decisões Mais Inteligentes**
- Considera o histórico de sucesso das ações
- Aprende padrões de jogo dos oponentes
- Otimiza o uso de elixir

### **3. Personalização**
- Cada bot se torna único
- Aprende com seus erros e acertos
- Desenvolve estratégias personalizadas

## 🔧 Próximos Passos

1. **Implementar o sistema básico** de coleta de dados
2. **Criar o modelo de ML** simples
3. **Integrar com o bot** existente
4. **Testar e ajustar** os parâmetros
5. **Adicionar features mais avançadas**

**Quer que eu implemente esse sistema de machine learning no seu bot?** 🚀

# 🎯 Guia de Configuração do Deck e Melhorias do Bot

## 🃏 Cartas Disponíveis no Bot

O bot suporta as seguintes cartas:

### **Tropas:**
- **Archers** (Arqueiras)
- **Baby Dragon** (Bebê Dragão)
- **Bats** (Morcegos)
- **Giant** (Gigante)
- **Goblin Barrel** (Barril de Goblins)
- **Knight** (Cavaleiro)
- **Minions** (Servos)
- **Minipekka** (Mini Pekka)
- **Musketeer** (Mosqueteira)
- **Witch** (Bruxa)

### **Feitiços:**
- **Arrows** (Flechas)
- **Fireball** (Bola de Fogo)
- **Zap** (Choque)

### **Construções:**
- **Cannon** (Canhão)

## 🔧 Como Configurar o Deck

### **Método 1: Interface Gráfica (Recomendado)**

1. **Execute o bot**: `python main.py`
2. **Clique em "Start Bot"**
3. **Vá na aba "Settings"**
4. **Configure as opções:**
   - **Log Level**: DEBUG (para ver mais detalhes)
   - **Action Delay**: 1.0 (ajuste conforme necessário)
   - **Load deck on startup**: Marque se quiser carregar deck automaticamente
   - **Enable visualizer**: Marque para ver o que o bot está vendo

### **Método 2: Editar o Código**

Edite o arquivo `main.py` para escolher suas 8 cartas:

```python
def main():
    check_and_pull_updates()
    actions = [
        # Escolha 8 cartas aqui:
        ArchersAction,        # Arqueiras
        MusketeerAction,      # Mosqueteira
        GiantAction,          # Gigante
        WitchAction,          # Bruxa
        BabyDragonAction,     # Bebê Dragão
        KnightAction,         # Cavaleiro
        FireballAction,       # Bola de Fogo
        ZapAction,            # Choque
    ]
    # ... resto do código
```

## 🎮 Decks Recomendados

### **Deck 1: Control (Controle)**
```python
actions = [
    ArchersAction,        # Arqueiras - Defesa aérea
    MusketeerAction,      # Mosqueteira - Dano aéreo
    GiantAction,          # Gigante - Tanque
    WitchAction,          # Bruxa - Suporte
    BabyDragonAction,     # Bebê Dragão - Ataque aéreo
    KnightAction,         # Cavaleiro - Defesa terrestre
    FireballAction,       # Bola de Fogo - Feitiço
    ZapAction,            # Choque - Feitiço rápido
]
```

### **Deck 2: Beatdown (Ataque)**
```python
actions = [
    GiantAction,          # Gigante - Tanque principal
    BabyDragonAction,     # Bebê Dragão - Suporte aéreo
    MusketeerAction,      # Mosqueteira - Dano
    WitchAction,          # Bruxa - Suporte
    MinipekkaAction,      # Mini Pekka - Dano alto
    ArchersAction,        # Arqueiras - Defesa
    FireballAction,       # Bola de Fogo - Feitiço
    ZapAction,            # Choque - Feitiço rápido
]
```

### **Deck 3: Cycle (Ciclo Rápido)**
```python
actions = [
    ArchersAction,        # Arqueiras - Defesa
    KnightAction,         # Cavaleiro - Defesa
    MusketeerAction,      # Mosqueteira - Dano
    MinipekkaAction,      # Mini Pekka - Dano
    BatsAction,           # Morcegos - Ciclo rápido
    GoblinBarrelAction,   # Barril de Goblins - Ataque
    ZapAction,            # Choque - Feitiço
    ArrowsAction,         # Flechas - Feitiço
]
```

## ⚙️ Configurações para Melhorar o Desempenho

### **1. Ajustar Delay entre Ações**

No arquivo `clashroyalebuildabot/config.yaml`:

```yaml
ingame:
  # Delay entre ações (em segundos)
  # 0.5 = Muito rápido (PC potente)
  # 1.0 = Padrão
  # 1.5 = Mais lento (PC fraco)
  play_action: 1.0
```

### **2. Configurações de Visualização**

```yaml
visuals:
  show_images: True    # Ver o que o bot está vendo
  save_images: False   # Salvar imagens (desative para melhor performance)
  save_labels: False   # Salvar labels (desative para melhor performance)
```

### **3. Configurações de Log**

```yaml
bot:
  log_level: "INFO"    # INFO = Menos logs, DEBUG = Mais detalhes
```

## 🎯 Estratégias para Reduzir Erros

### **1. Resolução da Tela**
- Configure o BlueStacks para **1920x1080** (recomendado)
- Ou **1280x720** (funciona, mas menos preciso)

### **2. Posicionamento das Cartas**
- O bot funciona melhor quando as cartas estão na ordem correta
- Certifique-se de que o deck no jogo corresponde ao deck configurado

### **3. Timing das Ações**
- **Action Delay**: 1.0 segundo é um bom equilíbrio
- Se o bot estiver muito lento: diminua para 0.8
- Se estiver fazendo muitas jogadas erradas: aumente para 1.2

### **4. Configurações do Emulador**
- Mantenha o BlueStacks em **tela cheia**
- Não minimize durante o jogo
- Feche outros programas para melhor performance

## 🔍 Como Monitorar o Desempenho

### **1. Logs em Tempo Real**
- Vá na aba **"Logs"** na interface do bot
- Monitore mensagens como:
  - `"Playing [carta] at (x, y)"` - Jogadas feitas
  - `"No actions available"` - Bot esperando
  - `"Unknown screen"` - Bot não reconhece a tela

### **2. Visualização**
- Vá na aba **"Visualize"** para ver o que o bot está vendo
- Isso ajuda a identificar problemas de detecção

### **3. Pausar/Retomar**
- Use **Ctrl+P** para pausar o bot
- Use **Ctrl+P** novamente para retomar
- Ou clique no botão **⏸️** na interface

## 🛠️ Solução de Problemas Comuns

### **Problema: Bot não joga cartas**
**Solução:**
- Verifique se o deck está configurado corretamente
- Certifique-se de que as cartas estão disponíveis no jogo
- Ajuste o Action Delay

### **Problema: Bot joga cartas no lugar errado**
**Solução:**
- Verifique a resolução da tela
- Certifique-se de que o Clash Royale está em tela cheia
- Reinicie o emulador

### **Problema: Bot não detecta inimigos**
**Solução:**
- Ative `show_images: True` para ver o que o bot está vendo
- Verifique se há problemas de iluminação na tela
- Ajuste a resolução para 1920x1080

### **Problema: Bot muito lento**
**Solução:**
- Diminua o Action Delay para 0.8
- Desative `save_images` e `save_labels`
- Feche outros programas
- Use `log_level: "INFO"` em vez de "DEBUG"

## 🎉 Próximos Passos

1. **Escolha um deck** das opções acima
2. **Configure as ações** no `main.py`
3. **Ajuste as configurações** no `config.yaml`
4. **Teste o bot** em partidas simples
5. **Monitore os logs** para identificar problemas
6. **Ajuste conforme necessário**

**Lembre-se: O bot aprende com o tempo. Quanto mais você o usar, melhor ele ficará!** 🚀

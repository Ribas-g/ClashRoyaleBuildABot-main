# 🎮 Guia de Configuração do Bot Clash Royale

## ✅ Status da Instalação

✅ **Python 3.11.0** - Instalado  
✅ **Dependências Python** - Instaladas  
✅ **ONNX Runtime** - Instalado  
✅ **Interface Gráfica** - Funcionando  
✅ **ADB** - Baixado automaticamente pelo bot  

## 🔧 Próximos Passos Necessários

### 1. Instalar um Emulador Android

Você precisa de um emulador Android para rodar o Clash Royale. Recomendamos:

**Opção A: BlueStacks (Mais Fácil)**
1. Baixe o BlueStacks: https://www.bluestacks.com/
2. Instale e configure
3. Instale o Clash Royale no BlueStacks
4. Configure a resolução para 1920x1080

**Opção B: LDPlayer**
1. Baixe o LDPlayer: https://www.ldplayer.net/
2. Instale e configure
3. Instale o Clash Royale no LDPlayer

**Opção C: NoxPlayer**
1. Baixe o NoxPlayer: https://www.bignox.com/
2. Instale e configure
3. Instale o Clash Royale no NoxPlayer

### 2. Configurar o Emulador

1. **Ative o modo desenvolvedor** no emulador
2. **Ative a depuração USB**
3. **Configure a resolução** para 1920x1080
4. **Instale o Clash Royale** e faça login

### 3. Conectar o Emulador ao Bot

1. **Inicie o emulador**
2. **Abra o Clash Royale** no emulador
3. **Execute o bot**: `python main.py`
4. **Clique em "Start Bot"** na interface

### 4. Configuração do ADB

O bot baixou automaticamente o ADB, mas você pode precisar configurar:

```bash
# Verificar dispositivos conectados
adb devices

# Se não aparecer nenhum dispositivo, tente:
adb kill-server
adb start-server
adb devices
```

### 5. Configuração do Bot

Edite o arquivo `clashroyalebuildabot/config.yaml`:

```yaml
adb:
  # Para emulador local
  ip: "127.0.0.1"
  # Serial do dispositivo (será detectado automaticamente)
  device_serial: auto

bot:
  log_level: "DEBUG"
  load_deck: False
  auto_start_game: False
  enable_gui: True

visuals:
  save_labels: False
  save_images: False
  show_images: True  # Ative para ver o que o bot está vendo

ingame:
  play_action: 1  # Delay entre ações
```

## 🎯 Como Usar o Bot

1. **Inicie o emulador** com Clash Royale
2. **Execute**: `python main.py`
3. **Clique em "Start Bot"**
4. **Configure seu deck** na interface
5. **Inicie uma partida** no Clash Royale
6. **O bot jogará automaticamente**

## 🔧 Solução de Problemas

### Erro: "No connected devices found"
- Verifique se o emulador está rodando
- Ative a depuração USB no emulador
- Execute `adb devices` para verificar conexão

### Erro: "ADB command failed"
- Reinicie o emulador
- Execute `adb kill-server` e `adb start-server`
- Verifique se o emulador tem permissões de ADB

### Bot não detecta cartas
- Verifique se a resolução está em 1920x1080
- Certifique-se de que o Clash Royale está em tela cheia
- Tente ajustar a configuração de detecção

## 📱 Configuração para Dispositivo Físico

Se quiser usar um dispositivo Android real:

1. **Ative o modo desenvolvedor** no seu Android
2. **Ative a depuração USB**
3. **Conecte via USB** ou **WiFi**
4. **Configure o IP** no `config.yaml`:
   ```yaml
   adb:
     ip: "192.168.1.XXX"  # IP do seu dispositivo
     device_serial: auto
   ```

## ⚠️ Aviso Legal

Este bot é **APENAS para fins educacionais e de pesquisa**. 
- Não é afiliado à Supercell
- O uso pode violar os Termos de Serviço do Clash Royale
- Use por sua conta e risco
- Pode resultar em banimento da conta

## 🆘 Suporte

Se tiver problemas:
1. Verifique os logs na interface do bot
2. Consulte a documentação oficial: https://github.com/Pbatch/ClashRoyaleBuildABot/wiki
3. Entre no Discord: https://discord.gg/K4UfbsfcMa

## 🎉 Próximos Passos

Após configurar o emulador:
1. Teste o bot com uma partida simples
2. Configure seu deck favorito
3. Ajuste as estratégias de jogo
4. Monitore o desempenho do bot

**Boa sorte e divirta-se! 🎮**

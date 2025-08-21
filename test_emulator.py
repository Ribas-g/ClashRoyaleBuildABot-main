#!/usr/bin/env python3
"""
Script para testar especificamente a conexão com o emulador
"""

import subprocess
import os
import time

def run_adb_command(command, device_serial="emulator-5554"):
    """Executa um comando ADB específico"""
    try:
        adb_path = os.path.join(os.path.dirname(__file__), 
                               "clashroyalebuildabot", "emulator", "platform-tools", "adb.exe")
        
        full_command = [adb_path, "-s", device_serial] + command
        result = subprocess.run(full_command, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 60)
    print("    TESTE ESPECÍFICO DO EMULADOR")
    print("=" * 60)
    print()
    
    device_serial = "emulator-5554"
    
    # Teste 1: Verificar se o dispositivo está online
    print("1. Verificando status do dispositivo...")
    success, stdout, stderr = run_adb_command(["get-state"], device_serial)
    if success:
        print(f"✅ Dispositivo {device_serial} está: {stdout.strip()}")
    else:
        print(f"❌ Erro ao verificar status: {stderr}")
        return
    
    print()
    
    # Teste 2: Verificar se o dispositivo responde
    print("2. Testando resposta do dispositivo...")
    success, stdout, stderr = run_adb_command(["shell", "echo", "test"], device_serial)
    if success:
        print("✅ Dispositivo responde aos comandos")
    else:
        print(f"❌ Dispositivo não responde: {stderr}")
        return
    
    print()
    
    # Teste 3: Verificar resolução da tela
    print("3. Verificando resolução da tela...")
    success, stdout, stderr = run_adb_command(["shell", "wm", "size"], device_serial)
    if success:
        print(f"✅ Resolução: {stdout.strip()}")
    else:
        print(f"❌ Erro ao obter resolução: {stderr}")
        print("   Isso pode indicar que o emulador não está totalmente carregado")
    
    print()
    
    # Teste 4: Verificar se o Clash Royale está instalado
    print("4. Verificando se o Clash Royale está instalado...")
    success, stdout, stderr = run_adb_command(["shell", "pm", "list", "packages", "com.supercell.clashroyale"], device_serial)
    if success and "com.supercell.clashroyale" in stdout:
        print("✅ Clash Royale está instalado")
    else:
        print("⚠️  Clash Royale não encontrado ou não instalado")
    
    print()
    
    # Teste 5: Verificar se o Clash Royale está rodando
    print("5. Verificando se o Clash Royale está rodando...")
    success, stdout, stderr = run_adb_command(["shell", "ps", "|", "grep", "clashroyale"], device_serial)
    if success and "clashroyale" in stdout:
        print("✅ Clash Royale está rodando")
    else:
        print("ℹ️  Clash Royale não está rodando (isso é normal se você acabou de abrir)")
    
    print()
    print("=" * 60)
    print("    RECOMENDAÇÕES")
    print("=" * 60)
    print()
    
    if "Physical size: 1920x1080" in stdout:
        print("✅ Resolução está correta (1920x1080)")
    else:
        print("⚠️  Recomendo configurar a resolução para 1920x1080")
        print("   No emulador, vá em Configurações > Display > Resolution")
    
    print()
    print("Para usar o bot:")
    print("1. Certifique-se de que o Clash Royale está aberto")
    print("2. Execute: python main.py")
    print("3. Clique em 'Start Bot'")
    print()
    print("Se ainda houver problemas:")
    print("- Reinicie o emulador")
    print("- Verifique se a depuração USB está ativada")
    print("- Execute este teste novamente")

if __name__ == "__main__":
    main()


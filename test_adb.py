#!/usr/bin/env python3
"""
Script para testar a conexão ADB e verificar dispositivos conectados
"""

import subprocess
import sys
import os

def run_adb_command(command):
    """Executa um comando ADB e retorna o resultado"""
    try:
        # Tenta usar o ADB do bot primeiro
        adb_path = os.path.join(os.path.dirname(__file__), 
                               "clashroyalebuildabot", "emulator", "platform-tools", "adb.exe")
        
        if os.path.exists(adb_path):
            full_command = [adb_path] + command
        else:
            # Se não encontrar, usa o ADB do sistema
            full_command = ["adb"] + command
            
        result = subprocess.run(full_command, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout ao executar comando ADB"
    except FileNotFoundError:
        return False, "", "ADB não encontrado"
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 50)
    print("    TESTE DE CONEXÃO ADB")
    print("=" * 50)
    print()
    
    # Teste 1: Verificar se o ADB está funcionando
    print("1. Testando ADB...")
    success, stdout, stderr = run_adb_command(["version"])
    if success:
        print("✅ ADB funcionando!")
        print(f"   Versão: {stdout.strip()}")
    else:
        print("❌ ADB não funcionando!")
        print(f"   Erro: {stderr}")
        return
    
    print()
    
    # Teste 2: Matar servidor ADB
    print("2. Reiniciando servidor ADB...")
    run_adb_command(["kill-server"])
    print("✅ Servidor ADB reiniciado")
    
    print()
    
    # Teste 3: Iniciar servidor ADB
    print("3. Iniciando servidor ADB...")
    success, stdout, stderr = run_adb_command(["start-server"])
    if success:
        print("✅ Servidor ADB iniciado")
    else:
        print("❌ Erro ao iniciar servidor ADB")
        print(f"   Erro: {stderr}")
    
    print()
    
    # Teste 4: Listar dispositivos
    print("4. Verificando dispositivos conectados...")
    success, stdout, stderr = run_adb_command(["devices"])
    if success:
        devices = stdout.strip().split('\n')[1:]  # Remove a primeira linha (header)
        devices = [d for d in devices if d.strip()]  # Remove linhas vazias
        
        if devices:
            print("✅ Dispositivos encontrados:")
            for device in devices:
                print(f"   {device}")
        else:
            print("⚠️  Nenhum dispositivo encontrado")
            print()
            print("SOLUÇÃO:")
            print("1. Verifique se o emulador está rodando")
            print("2. Ative a depuração USB no emulador")
            print("3. Reinicie o emulador")
            print("4. Execute este script novamente")
    else:
        print("❌ Erro ao listar dispositivos")
        print(f"   Erro: {stderr}")
    
    print()
    print("=" * 50)
    print("    INSTRUÇÕES PARA CONECTAR")
    print("=" * 50)
    print()
    print("Se nenhum dispositivo foi encontrado:")
    print()
    print("1. INSTALE UM EMULADOR:")
    print("   - BlueStacks: https://www.bluestacks.com/")
    print("   - LDPlayer: https://www.ldplayer.net/")
    print("   - NoxPlayer: https://www.bignox.com/")
    print()
    print("2. CONFIGURE O EMULADOR:")
    print("   - Ative o modo desenvolvedor")
    print("   - Ative a depuração USB")
    print("   - Configure resolução 1920x1080")
    print("   - Instale o Clash Royale")
    print()
    print("3. TESTE NOVAMENTE:")
    print("   - Execute: python test_adb.py")
    print()
    print("4. EXECUTE O BOT:")
    print("   - Execute: python main.py")
    print("   - Clique em 'Start Bot'")
    print()

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Script para testar usando o ADB do BlueStacks
"""

import subprocess
import os
import time

def find_bluestacks_adb():
    """Procura o ADB do BlueStacks"""
    possible_paths = [
        r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe",
        r"C:\Program Files (x86)\BlueStacks_nxt\HD-Adb.exe",
        r"C:\Program Files\BlueStacks_nxt\HD-Player.exe",
        r"C:\Program Files (x86)\BlueStacks_nxt\HD-Player.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\BlueStacks_nxt\HD-Adb.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\BlueStacks_nxt\HD-Player.exe")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def run_bluestacks_adb_command(command):
    """Executa comando usando ADB do BlueStacks"""
    try:
        adb_path = find_bluestacks_adb()
        if not adb_path:
            return False, "", "ADB do BlueStacks não encontrado"
        
        # Se encontrou HD-Player.exe, tenta usar HD-Adb.exe
        if "HD-Player.exe" in adb_path:
            adb_path = adb_path.replace("HD-Player.exe", "HD-Adb.exe")
        
        full_command = [adb_path] + command
        result = subprocess.run(full_command, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 60)
    print("    TESTE COM ADB DO BLUESTACKS")
    print("=" * 60)
    print()
    
    # Procurar ADB do BlueStacks
    print("1. Procurando ADB do BlueStacks...")
    adb_path = find_bluestacks_adb()
    if adb_path:
        print(f"✅ ADB encontrado: {adb_path}")
    else:
        print("❌ ADB do BlueStacks não encontrado")
        print("   Tentando usar ADB do bot...")
        adb_path = os.path.join(os.path.dirname(__file__), 
                               "clashroyalebuildabot", "emulator", "platform-tools", "adb.exe")
        if os.path.exists(adb_path):
            print(f"✅ Usando ADB do bot: {adb_path}")
        else:
            print("❌ Nenhum ADB encontrado")
            return
    
    print()
    
    # Teste 1: Conectar ao BlueStacks
    print("2. Conectando ao BlueStacks...")
    success, stdout, stderr = run_bluestacks_adb_command(["connect", "127.0.0.1:5555"])
    if success:
        print("✅ Conectado ao BlueStacks")
    else:
        print(f"❌ Erro ao conectar: {stderr}")
    
    print()
    
    # Teste 2: Listar dispositivos
    print("3. Verificando dispositivos...")
    success, stdout, stderr = run_bluestacks_adb_command(["devices"])
    if success:
        print("✅ Dispositivos:")
        print(stdout)
    else:
        print(f"❌ Erro ao listar dispositivos: {stderr}")
    
    print()
    
    # Teste 3: Testar comando shell
    print("4. Testando comando shell...")
    success, stdout, stderr = run_bluestacks_adb_command(["-s", "127.0.0.1:5555", "shell", "echo", "test"])
    if success:
        print("✅ Comando shell funcionando")
        print(f"   Resposta: {stdout.strip()}")
    else:
        print(f"❌ Erro no comando shell: {stderr}")
    
    print()
    print("=" * 60)
    print("    INSTRUÇÕES")
    print("=" * 60)
    print()
    
    if "127.0.0.1:5555" in stdout and "device" in stdout:
        print("✅ BlueStacks está funcionando com ADB!")
        print()
        print("Agora você pode:")
        print("1. Execute: python main.py")
        print("2. Clique em 'Start Bot'")
        print("3. Configure seu deck")
        print("4. Comece a jogar!")
    else:
        print("⚠️  BlueStacks ainda precisa ser configurado")
        print()
        print("Siga estas etapas:")
        print("1. Abra o BlueStacks")
        print("2. Vá em Configurações (ícone de engrenagem)")
        print("3. Vá em 'Advanced'")
        print("4. Ative 'Android Debug Bridge (ADB)'")
        print("5. Reinicie o BlueStacks")
        print("6. Execute este teste novamente")

if __name__ == "__main__":
    main()


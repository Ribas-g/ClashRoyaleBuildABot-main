#!/usr/bin/env python3
"""
Script para identificar automaticamente qual emulador está sendo usado
"""

import subprocess
import os
import psutil

def check_processes():
    """Verifica quais processos de emulador estão rodando"""
    emuladores = {
        'BlueStacks': ['HD-Player.exe', 'HD-Adb.exe', 'BlueStacks.exe'],
        'LDPlayer': ['dnplayer.exe', 'LDPlayer.exe', 'LD9.exe'],
        'NoxPlayer': ['Nox.exe', 'NoxVMHandle.exe'],
        'MEmu': ['MEmu.exe', 'MEmuHeadless.exe'],
        'Genymotion': ['genymotion.exe', 'player.exe']
    }
    
    running_emulators = []
    
    for process in psutil.process_iter(['pid', 'name']):
        try:
            process_name = process.info['name'].lower()
            for emulator, processes in emuladores.items():
                for proc in processes:
                    if proc.lower() in process_name:
                        running_emulators.append(emulator)
                        break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return list(set(running_emulators))

def check_ports():
    """Verifica quais portas estão sendo usadas por emuladores"""
    ports = {
        5555: 'BlueStacks/LDPlayer',
        5556: 'BlueStacks/LDPlayer',
        5557: 'BlueStacks/LDPlayer',
        5558: 'BlueStacks/LDPlayer',
        62001: 'NoxPlayer',
        62002: 'NoxPlayer',
        62003: 'NoxPlayer',
        62004: 'NoxPlayer',
        21503: 'MEmu'
    }
    
    used_ports = []
    
    for port, emulator in ports.items():
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                used_ports.append((port, emulator))
        except:
            pass
    
    return used_ports

def main():
    print("=" * 60)
    print("    IDENTIFICAÇÃO DO EMULADOR")
    print("=" * 60)
    print()
    
    # Verificar processos
    print("1. Verificando processos de emulador...")
    running_emulators = check_processes()
    
    if running_emulators:
        print("✅ Emuladores detectados:")
        for emulator in running_emulators:
            print(f"   - {emulator}")
    else:
        print("⚠️  Nenhum processo de emulador detectado")
    
    print()
    
    # Verificar portas
    print("2. Verificando portas de emulador...")
    used_ports = check_ports()
    
    if used_ports:
        print("✅ Portas de emulador detectadas:")
        for port, emulator in used_ports:
            print(f"   - Porta {port}: {emulator}")
    else:
        print("⚠️  Nenhuma porta de emulador detectada")
    
    print()
    
    # Determinar emulador mais provável
    print("3. Análise final...")
    
    if running_emulators:
        most_likely = running_emulators[0]
        print(f"🎯 Emulador mais provável: {most_likely}")
        
        if most_likely == "BlueStacks":
            print()
            print("📋 INSTRUÇÕES PARA BLUESTACKS:")
            print("1. Abra o BlueStacks")
            print("2. Clique no ícone de engrenagem (Configurações)")
            print("3. Vá em 'Advanced'")
            print("4. Ative 'Android Debug Bridge (ADB)'")
            print("5. Reinicie o BlueStacks")
            print("6. Teste novamente com: python test_emulator.py")
            
        elif most_likely == "LDPlayer":
            print()
            print("📋 INSTRUÇÕES PARA LDPLAYER:")
            print("1. Abra o LDPlayer")
            print("2. Vá em Configurações")
            print("3. Clique em 'Other Settings'")
            print("4. Ative 'ADB Debug'")
            print("5. Reinicie o LDPlayer")
            print("6. Teste novamente com: python test_emulator.py")
            
        elif most_likely == "NoxPlayer":
            print()
            print("📋 INSTRUÇÕES PARA NOXPLAYER:")
            print("1. Abra o NoxPlayer")
            print("2. Vá em Configurações")
            print("3. Clique em 'Advanced'")
            print("4. Ative 'ADB Debug'")
            print("5. Reinicie o NoxPlayer")
            print("6. Teste novamente com: python test_emulator.py")
            
    else:
        print("❓ Não foi possível identificar o emulador")
        print()
        print("💡 Tente uma das seguintes opções:")
        print("1. Verifique se o emulador está rodando")
        print("2. Reinicie o emulador")
        print("3. Use BlueStacks 5 (mais confiável)")
        print("4. Consulte o arquivo SOLUCAO_EMULADOR.md")
    
    print()
    print("=" * 60)
    print("    PRÓXIMOS PASSOS")
    print("=" * 60)
    print()
    print("Após configurar o emulador:")
    print("1. Execute: python test_emulator.py")
    print("2. Se funcionar, execute: python main.py")
    print("3. Configure seu deck e comece a jogar!")

if __name__ == "__main__":
    main()

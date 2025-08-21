#!/usr/bin/env python3
"""
Script para diagnosticar problemas do bot
"""

import time
from clashroyalebuildabot.emulator.emulator import Emulator
from clashroyalebuildabot.detectors.detector import Detector
from clashroyalebuildabot.visualizer import Visualizer
from clashroyalebuildabot.namespaces import Screens

def main():
    print("=" * 60)
    print("    DIAGNÓSTICO DO BOT")
    print("=" * 60)
    print()
    
    try:
        # Inicializa componentes
        print("🔧 Inicializando componentes...")
        emulator = Emulator("auto", "127.0.0.1")
        
        # Cartas do deck configurado
        from clashroyalebuildabot.actions import (
            GiantAction, MusketeerAction, WitchAction, BabyDragonAction,
            KnightAction, ArchersAction, FireballAction, ZapAction
        )
        cards = [
            GiantAction, MusketeerAction, WitchAction, BabyDragonAction,
            KnightAction, ArchersAction, FireballAction, ZapAction
        ]
        
        detector = Detector(cards=cards)
        visualizer = Visualizer()
        
        print("✅ Componentes inicializados")
        print()
        
        # Testa screenshot
        print("📸 Testando screenshot...")
        screenshot = emulator.take_screenshot()
        print(f"✅ Screenshot capturado: {screenshot.shape if hasattr(screenshot, 'shape') else 'N/A'}")
        print()
        
        # Testa detecção
        print("🔍 Testando detecção...")
        state = detector.run(screenshot)
        
        if state:
            print(f"✅ Estado detectado: {state.screen}")
            print(f"   Cards: {len(state.cards) if hasattr(state, 'cards') and state.cards else 0}")
            print(f"   Ready: {state.ready if hasattr(state, 'ready') else 'N/A'}")
            print(f"   Elixir: {state.numbers.elixir.number if hasattr(state.numbers, 'elixir') else 'N/A'}")
            
            if hasattr(state, 'cards') and state.cards:
                print("   Cards detectadas:")
                for i, card in enumerate(state.cards):
                    if card:
                        print(f"     {i}: {card.name} (custo: {card.cost})")
        else:
            print("❌ Nenhum estado detectado")
        
        print()
        
        # Testa visualizer
        print("👁️ Testando visualizer...")
        visualizer.run(screenshot, state)
        print("✅ Visualizer executado")
        print()
        
        # Testa múltiplas capturas
        print("🔄 Testando múltiplas capturas...")
        for i in range(3):
            print(f"   Captura {i+1}:")
            screenshot = emulator.take_screenshot()
            state = detector.run(screenshot)
            if state:
                print(f"     Screen: {state.screen}")
                print(f"     Cards: {len(state.cards) if hasattr(state, 'cards') and state.cards else 0}")
                print(f"     Ready: {state.ready if hasattr(state, 'ready') else 'N/A'}")
            else:
                print("     ❌ Nenhum estado detectado")
            time.sleep(1)
        
        print()
        print("✅ Diagnóstico concluído!")
        
    except Exception as e:
        print(f"❌ Erro durante diagnóstico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

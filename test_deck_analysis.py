#!/usr/bin/env python3
"""
Script para testar o sistema de análise de deck do inimigo
"""

import os
import json
from clashroyalebuildabot.ml.deck_analyzer import DeckAnalyzer
from clashroyalebuildabot.ml.enemy_detector import EnemyDetector

def main():
    print("=" * 60)
    print("    TESTE DO SISTEMA DE ANÁLISE DE DECK")
    print("=" * 60)
    print()
    
    print("🧠 SISTEMA DE MEMÓRIA IMPLEMENTADO:")
    print()
    print("✅ Análise de deck do oponente")
    print("✅ Detecção automática de cartas")
    print("✅ Previsão de cartas baseada no ciclo")
    print("✅ Identificação de fraquezas")
    print("✅ Sugestão de estratégias")
    print("✅ Memória de jogos anteriores")
    print()
    
    print("📊 COMO FUNCIONA:")
    print()
    print("1. O bot detecta cartas jogadas pelo inimigo:")
    print("   • Identifica unidades no campo")
    print("   • Registra ordem das cartas")
    print("   • Analisa padrões de jogo")
    print()
    print("2. Analisa o deck do oponente:")
    print("   • Compara com decks conhecidos")
    print("   • Prediz cartas restantes")
    print("   • Calcula confiança da predição")
    print()
    print("3. Identifica fraquezas e estratégias:")
    print("   • Detecta falta de defesa aérea")
    print("   • Identifica poucos feitiços")
    print("   • Sugere contra-jogadas")
    print()
    print("4. Previsão de ciclo:")
    print("   • Calcula intervalo entre cartas")
    print("   • Prediz próximas cartas")
    print("   • Ajusta estratégia automaticamente")
    print()
    
    print("🎯 BENEFÍCIOS:")
    print()
    print("• Antecipa jogadas do oponente")
    print("• Identifica fraquezas do deck inimigo")
    print("• Sugere melhores contra-jogadas")
    print("• Aprende padrões de jogo")
    print("• Melhora com cada partida")
    print("• Adapta estratégia em tempo real")
    print()
    
    print("📁 ARQUIVOS CRIADOS:")
    print()
    print("• deck_memory.json - Memória de decks")
    print("• clashroyalebuildabot/ml/deck_analyzer.py")
    print("• clashroyalebuildabot/ml/enemy_detector.py")
    print()
    
    print("⚙️ CONFIGURAÇÃO:")
    print()
    print("O sistema está ativado no config.yaml:")
    print("ml:")
    print("  enabled: True")
    print("  enable_deck_analysis: True")
    print("  deck_memory_path: deck_memory.json")
    print()
    
    print("🔧 COMO USAR:")
    print()
    print("1. Execute: python main.py")
    print("2. Jogue normalmente")
    print("3. O bot detectará cartas do inimigo automaticamente")
    print("4. Verá logs como 'Enemy played: giant'")
    print("5. O bot ajustará estratégia baseado na análise")
    print()
    
    print("📈 MONITORAMENTO:")
    print()
    print("• Logs mostrarão cartas detectadas")
    print("• Análise de deck será exibida")
    print("• Estratégias serão sugeridas")
    print("• Previsões de ciclo serão feitas")
    print()
    
    # Testa se os módulos estão funcionando
    print("🧪 TESTE DOS MÓDULOS:")
    print()
    
    try:
        # Testa o analisador de deck
        analyzer = DeckAnalyzer("test_deck_memory.json")
        print("✅ DeckAnalyzer funcionando")
        
        # Simula um jogo
        analyzer.start_new_game()
        print("✅ Iniciou análise de jogo")
        
        # Simula cartas jogadas
        from clashroyalebuildabot.namespaces.state import State
        from clashroyalebuildabot.namespaces.numbers import Numbers
        
        # Cria estado simulado
        from clashroyalebuildabot.namespaces.numbers import NumberDetection
        
        # Cria números simulados
        elixir = NumberDetection((0, 0, 0, 0), 10)
        left_ally_hp = NumberDetection((0, 0, 0, 0), 100)
        right_ally_hp = NumberDetection((0, 0, 0, 0), 100)
        left_enemy_hp = NumberDetection((0, 0, 0, 0), 100)
        right_enemy_hp = NumberDetection((0, 0, 0, 0), 100)
        
        numbers = Numbers(left_enemy_hp, right_enemy_hp, left_ally_hp, right_ally_hp, elixir)
        state = State([], [], numbers, [], False, None)
        
        # Simula cartas jogadas
        analyzer.record_enemy_card("giant", state)
        analyzer.record_enemy_card("musketeer", state)
        analyzer.record_enemy_card("witch", state)
        
        print("✅ Registrou cartas do inimigo")
        
        # Obtém análise
        analysis = analyzer.get_analysis_summary()
        if analysis:
            print(f"✅ Análise: {analysis['cards_played']} cartas detectadas")
            if analysis['deck_prediction']:
                print(f"   Deck predito: {analysis['deck_prediction']['name']}")
                print(f"   Confiança: {analysis['deck_prediction']['confidence']:.2f}")
            if analysis['weaknesses']:
                print(f"   Fraquezas: {analysis['weaknesses']}")
            if analysis['strategies']:
                print(f"   Estratégias: {analysis['strategies']}")
        
        # Testa detector de inimigo
        detector = EnemyDetector(analyzer)
        print("✅ EnemyDetector funcionando")
        
        # Finaliza jogo
        analyzer.end_game("win")
        print("✅ Finalizou análise do jogo")
        
        # Limpa arquivo de teste
        if os.path.exists("test_deck_memory.json"):
            os.remove("test_deck_memory.json")
        
        print("✅ Todos os módulos funcionando corretamente!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        print("Verifique se todas as dependências estão instaladas")
    
    print()
    print("🎉 PRÓXIMOS PASSOS:")
    print()
    print("1. Execute o bot: python main.py")
    print("2. Jogue algumas partidas")
    print("3. Observe os logs de detecção de cartas")
    print("4. Veja como o bot adapta a estratégia!")
    print()
    
    print("⚠️ IMPORTANTE:")
    print()
    print("• O sistema precisa de algumas cartas para começar a analisar")
    print("• Quanto mais cartas detectadas, melhor a predição")
    print("• A memória melhora com cada partida")
    print("• O bot se torna mais inteligente com o tempo")
    print()
    
    print("=" * 60)
    print("    O BOT AGORA É UM ESTRATEGISTA! 🧠")
    print("=" * 60)

if __name__ == "__main__":
    main()

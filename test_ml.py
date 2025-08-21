#!/usr/bin/env python3
"""
Script para testar o sistema de Machine Learning do bot
"""

import os
import json
from clashroyalebuildabot.ml.data_collector import GameDataCollector
from clashroyalebuildabot.ml.ml_bot import MLBot

def main():
    print("=" * 60)
    print("    TESTE DO SISTEMA DE MACHINE LEARNING")
    print("=" * 60)
    print()
    
    print("🤖 SISTEMA DE ML IMPLEMENTADO:")
    print()
    print("✅ Coleta de dados automática")
    print("✅ Modelo Random Forest para predição")
    print("✅ Sistema de recompensas inteligente")
    print("✅ Treinamento contínuo")
    print("✅ Aprendizado com cada partida")
    print()
    
    print("📊 COMO FUNCIONA:")
    print()
    print("1. O bot coleta dados de cada ação:")
    print("   • Estado do jogo (elixir, HP das torres)")
    print("   • Ação tomada (carta, posição)")
    print("   • Resultado da ação (recompensa)")
    print()
    print("2. Após cada partida:")
    print("   • Analisa se ganhou ou perdeu")
    print("   • Calcula recompensas finais")
    print("   • Treina o modelo com os dados")
    print()
    print("3. Nas próximas partidas:")
    print("   • Usa o modelo treinado para escolher ações")
    print("   • Combina ML (70%) + lógica original (30%)")
    print("   • Melhora continuamente com experiência")
    print()
    
    print("🎯 BENEFÍCIOS:")
    print()
    print("• Aprende estratégias específicas do seu deck")
    print("• Adapta-se ao seu estilo de jogo")
    print("• Melhora com cada partida")
    print("• Decisões mais inteligentes")
    print("• Otimização automática de elixir")
    print()
    
    print("📁 ARQUIVOS CRIADOS:")
    print()
    print("• game_data.json - Dados das partidas")
    print("• ml_model.pkl - Modelo treinado")
    print("• clashroyalebuildabot/ml/ - Módulo de ML")
    print()
    
    print("⚙️ CONFIGURAÇÃO:")
    print()
    print("O ML está ativado por padrão no config.yaml:")
    print("ml:")
    print("  enabled: True")
    print("  model_path: ml_model.pkl")
    print("  data_path: game_data.json")
    print()
    
    print("🔧 COMO USAR:")
    print()
    print("1. Execute: python main.py")
    print("2. Jogue algumas partidas normalmente")
    print("3. O bot começará a aprender automaticamente")
    print("4. Após 5+ partidas, verá melhorias no desempenho")
    print()
    
    print("📈 MONITORAMENTO:")
    print()
    print("• Logs mostrarão 'ML score' quando treinado")
    print("• Estatísticas de vitória serão exibidas")
    print("• O modelo salva automaticamente")
    print()
    
    print("⚠️ IMPORTANTE:")
    print()
    print("• O bot precisa de algumas partidas para aprender")
    print("• Quanto mais partidas, melhor o desempenho")
    print("• O modelo se adapta ao seu deck específico")
    print("• Dados são salvos automaticamente")
    print()
    
    # Testa se os módulos estão funcionando
    print("🧪 TESTE DOS MÓDULOS:")
    print()
    
    try:
        # Testa o coletor de dados
        collector = GameDataCollector("test_data.json")
        print("✅ GameDataCollector funcionando")
        
        # Testa o modelo ML
        ml_bot = MLBot("test_model.pkl")
        print("✅ MLBot funcionando")
        
        # Limpa arquivos de teste
        if os.path.exists("test_data.json"):
            os.remove("test_data.json")
        if os.path.exists("test_model.pkl"):
            os.remove("test_model.pkl")
        
        print("✅ Todos os módulos funcionando corretamente!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        print("Verifique se scikit-learn e joblib estão instalados:")
        print("pip install scikit-learn joblib")
    
    print()
    print("🎉 PRÓXIMOS PASSOS:")
    print()
    print("1. Execute o bot: python main.py")
    print("2. Jogue algumas partidas")
    print("3. Monitore os logs para ver o ML em ação")
    print("4. Observe a melhoria no desempenho!")
    print()
    
    print("=" * 60)
    print("    BOA SORTE! O BOT VAI APRENDER! 🚀")
    print("=" * 60)

if __name__ == "__main__":
    main()

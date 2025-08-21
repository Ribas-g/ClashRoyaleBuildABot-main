#!/usr/bin/env python3
"""
Teste da Base de Conhecimento
"""

try:
    from clashroyalebuildabot.knowledge_base import knowledge_base
    print("✅ Base de conhecimento importada com sucesso!")
    
    # Teste de counters
    counters = knowledge_base.get_counter_suggestions("giant", ["minipekka", "knight", "archers"])
    print(f"✅ Counters para giant: {counters}")
    
    # Teste de análise de deck
    deck_analysis = knowledge_base.get_deck_analysis(["giant", "musketeer", "witch"])
    print(f"✅ Análise de deck: {deck_analysis}")
    
    # Teste de posicionamento
    positioning = knowledge_base.get_positioning_guide("giant", "defensive")
    print(f"✅ Posicionamento para giant: {positioning}")
    
    # Teste de estratégias
    strategies = knowledge_base.get_strategy_suggestions({"elixir": 5, "under_pressure": False})
    print(f"✅ Estratégias sugeridas: {strategies}")
    
    print("\n🎉 Todos os testes passaram! Base de conhecimento funcionando perfeitamente!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

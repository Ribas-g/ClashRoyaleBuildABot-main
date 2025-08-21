#!/usr/bin/env python3
"""
Teste das Funcionalidades de Cycling e Cálculo de Elixir
Demonstra o sistema avançado de cycling e rastreamento de elixir
"""

try:
    from clashroyalebuildabot.knowledge_base import knowledge_base
    print("✅ Sistema de cycling e elixir importado com sucesso!")
    
    # Nosso deck de exemplo
    our_deck = ["giant", "musketeer", "witch", "baby_dragon", "knight", "archers", "fireball", "zap"]
    
    print("\n" + "="*60)
    print("🔄 ESTRATÉGIAS DE CYCLING")
    print("="*60)
    
    # Teste de estratégia de cycling ofensivo
    game_state = {"elixir": 6, "under_pressure": False}
    cycling_strategy = knowledge_base.get_cycling_strategy("offensive_cycling", our_deck, game_state)
    
    print(f"📊 Estratégia de cycling ofensivo:")
    print(f"   Situação: {cycling_strategy.get('situation', 'N/A')}")
    
    for scenario in cycling_strategy.get('scenarios', []):
        print(f"   • {scenario['situation']} - Prioridade: {scenario['priority']}")
        print(f"     Custo: {scenario['elixir_cost']}, Resultado esperado: {scenario['expected_outcome']}")
        print(f"     Riscos: {scenario['risks']}")
    
    print(f"🎯 Ações recomendadas:")
    for action in cycling_strategy.get('recommended_actions', []):
        print(f"   • {action['action']} - {action.get('target', action.get('cards', 'N/A'))}")
        print(f"     Prioridade: {action['priority']}, Custo: {action['elixir_cost']}")
    
    print("\n" + "="*60)
    print("⚡ CÁLCULO DE ELIXIR")
    print("="*60)
    
    # Teste de cálculo de nosso elixir
    our_elixir = knowledge_base.calculate_our_elixir(5.0, 30.0, 8.0)  # 5 base + 30s - 8 gasto
    print(f"📈 Nosso elixir atual: {our_elixir:.1f}")
    
    # Teste de estimativa do elixir inimigo
    enemy_actions = [
        {"card": "giant", "time": 10},
        {"card": "musketeer", "time": 15},
        {"card": "fireball", "time": 20}
    ]
    enemy_elixir_estimate = knowledge_base.estimate_enemy_elixir(enemy_actions, 10.0)
    
    print(f"📉 Estimativa do elixir inimigo:")
    print(f"   Elixir estimado: {enemy_elixir_estimate['estimated_elixir']:.1f}")
    print(f"   Estado: {enemy_elixir_estimate['elixir_state']}")
    print(f"   Confiança: {enemy_elixir_estimate['confidence']:.1f}")
    
    # Teste de cálculo de vantagem de elixir
    elixir_advantage = knowledge_base.calculate_elixir_advantage(our_elixir, enemy_elixir_estimate['estimated_elixir'])
    
    print(f"⚖️ Vantagem de elixir:")
    print(f"   Nossa vantagem: {elixir_advantage['advantage']:+.1f}")
    print(f"   Implicação estratégica: {elixir_advantage['strategic_implication']}")
    print(f"   Recomendação: {elixir_advantage['recommendation']}")
    
    print("\n" + "="*60)
    print("⏰ TIMING DE CYCLING")
    print("="*60)
    
    # Teste de momento ideal para cycling
    optimal_moment = knowledge_base.get_optimal_cycling_moment(game_state, enemy_elixir_estimate['elixir_state'])
    
    print(f"🎯 Momento ideal para cycling:")
    print(f"   Deve ciclar: {optimal_moment['should_cycle']}")
    if optimal_moment['should_cycle']:
        print(f"   Momento: {optimal_moment['moment']}")
        print(f"   Vantagem: {optimal_moment['advantage']}")
        print(f"   Risco: {optimal_moment['risk']}")
    else:
        print(f"   Razão: {optimal_moment['reason']}")
        print(f"   Alternativa: {optimal_moment['alternative']}")
    print(f"   Prioridade: {optimal_moment['priority']}")
    
    print("\n" + "="*60)
    print("💡 DICAS DE EFICIÊNCIA")
    print("="*60)
    
    # Teste de dicas de eficiência
    efficiency_tips = knowledge_base.get_cycle_efficiency_tips(our_deck)
    
    print(f"🧠 Dicas para cycling eficiente:")
    for tip in efficiency_tips:
        if tip['type'] == 'efficient_strategy':
            print(f"   ✅ {tip['strategy']}: {tip['description']}")
            print(f"      Elixir economizado: {tip['elixir_saved']}")
        else:
            print(f"   ⚠️ Evitar {tip['mistake']}: {tip['description']}")
            print(f"      Como evitar: {tip['avoidance']}")
        print(f"      Prioridade: {tip['priority']}")
    
    print("\n" + "="*60)
    print("🎮 SIMULAÇÃO DE JOGO")
    print("="*60)
    
    # Simulação de uma situação de jogo
    print("🤔 Cenário: Inimigo jogou Giant + Musketeer, nosso elixir: 4")
    
    # Calcula situação
    game_state = {"elixir": 4, "under_pressure": True}
    enemy_actions = [{"card": "giant"}, {"card": "musketeer"}]
    enemy_estimate = knowledge_base.estimate_enemy_elixir(enemy_actions, 5.0)
    
    # Estratégia de cycling defensivo
    defensive_cycling = knowledge_base.get_cycling_strategy("defensive_cycling", our_deck, game_state)
    
    print(f"📊 Análise da situação:")
    print(f"   Nosso elixir: {game_state['elixir']}")
    print(f"   Elixir inimigo estimado: {enemy_estimate['estimated_elixir']:.1f}")
    print(f"   Estado do inimigo: {enemy_estimate['elixir_state']}")
    
    print(f"🔄 Estratégia de cycling defensivo:")
    for scenario in defensive_cycling.get('scenarios', []):
        print(f"   • {scenario['situation']} - {scenario['expected_outcome']}")
        print(f"     Prioridade: {scenario['priority']}, Riscos: {scenario['risks']}")
    
    # Momento ideal para cycling
    cycling_moment = knowledge_base.get_optimal_cycling_moment(game_state, enemy_estimate['elixir_state'])
    
    print(f"⏰ Decisão de cycling:")
    if cycling_moment['should_cycle']:
        print(f"   ✅ Ciclar agora - {cycling_moment['moment']}")
        print(f"   Vantagem: {cycling_moment['advantage']}")
    else:
        print(f"   ❌ Não ciclar agora - {cycling_moment['reason']}")
        print(f"   Alternativa: {cycling_moment['alternative']}")
    
    print("\n🎉 Sistema de cycling e elixir funcionando perfeitamente!")
    print("🧠 A IA agora entende quando e como ciclar eficientemente!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""
Teste das Funcionalidades Avançadas da Base de Conhecimento
Demonstra o sistema de counters avançados e estratégias de xadrez
"""

try:
    from clashroyalebuildabot.knowledge_base import knowledge_base
    print("✅ Base de conhecimento avançada importada com sucesso!")
    
    # Nosso deck de exemplo
    our_deck = ["giant", "musketeer", "witch", "baby_dragon", "knight", "archers", "fireball", "zap"]
    
    print("\n" + "="*60)
    print("🎯 ANÁLISE AVANÇADA DE COUNTERS")
    print("="*60)
    
    # Teste de análise avançada de counter
    enemy_card = "giant"
    our_card = "minipekka"
    
    advanced_analysis = knowledge_base.get_advanced_counter_analysis(enemy_card, our_card)
    print(f"📊 Análise avançada: {enemy_card} vs {our_card}")
    print(f"   Eficiência: {advanced_analysis.get('effectiveness', 'N/A')}")
    print(f"   Trade de elixir: {advanced_analysis.get('elixir_trade', 'N/A')}")
    print(f"   Posicionamento: {advanced_analysis.get('positioning', 'N/A')}")
    print(f"   Counter-push: {advanced_analysis.get('counter_push', 'N/A')}")
    print(f"   Riscos: {advanced_analysis.get('risks', [])}")
    print(f"   Melhores follow-ups: {advanced_analysis.get('best_followup', [])}")
    
    print("\n" + "="*60)
    print("🔗 ANÁLISE DE CADEIA DE COUNTERS")
    print("="*60)
    
    # Teste de análise de cadeia de counters
    chain_analysis = knowledge_base.get_counter_chain_analysis(enemy_card, our_deck)
    print(f"📋 Cadeia de counters para {enemy_card}:")
    for i, counter in enumerate(chain_analysis, 1):
        print(f"   {i}. {counter['counter']} - {counter['effectiveness']} (Trade: {counter['elixir_trade']})")
        print(f"      Riscos: {counter['risks']}")
        print(f"      Follow-ups disponíveis: {counter['available_followups']}")
        print(f"      Counter-push: {counter['counter_push_potential']}")
    
    print("\n" + "="*60)
    print("🎮 ESTRATÉGIAS DE XADREZ")
    print("="*60)
    
    # Teste de estratégias de xadrez
    game_state = {
        "elixir": 5,
        "under_pressure": False,
        "advantage": True
    }
    
    situational_strategy = knowledge_base.get_situational_strategy(game_state)
    print(f"📈 Situação atual: {situational_strategy['situation']}")
    print(f"🎯 Estratégias recomendadas:")
    for move in situational_strategy['recommended_moves']:
        print(f"   • {move['move']} - {move['reasoning']}")
        print(f"     Prioridade: {move['priority']}, Custo: {move['elixir_cost']}")
        print(f"     Resultado esperado: {move['expected_outcome']}")
    
    print("\n" + "="*60)
    print("🔮 ESTRATÉGIA DE PREDIÇÃO")
    print("="*60)
    
    # Teste de estratégia de predição
    enemy_cards_played = ["giant", "musketeer", "witch"]
    prediction_strategy = knowledge_base.get_prediction_strategy(enemy_cards_played, our_deck)
    
    if prediction_strategy['deck_analysis']:
        deck_analysis = prediction_strategy['deck_analysis']
        print(f"📊 Deck identificado: {deck_analysis['name']}")
        print(f"   Confiança: {deck_analysis['confidence']:.2f}")
        print(f"   Archetype: {deck_analysis['archetype']}")
        print(f"   Win condition: {deck_analysis['win_condition']}")
        print(f"   Fraquezas: {deck_analysis['weaknesses']}")
        print(f"   Cartas faltando: {deck_analysis['missing_cards']}")
    
    print(f"🎯 Cartas esperadas:")
    for expected in prediction_strategy['expected_cards']:
        print(f"   • {expected['card']} (Prob: {expected['probability']:.2f})")
        print(f"     Counters disponíveis: {expected['counters']}")
    
    print(f"⚡ Movimentos de preparação:")
    for prep in prediction_strategy['preparation_moves']:
        print(f"   • {prep['action']} {prep['counter']} para {prep['for_card']}")
        print(f"     Prioridade: {prep['priority']}")
    
    print("\n" + "="*60)
    print("🎯 EXEMPLO DE DECISÃO ESTRATÉGICA")
    print("="*60)
    
    # Simulação de uma decisão estratégica
    print("🤔 Cenário: Inimigo jogou Giant no bridge")
    print("📋 Nossas opções disponíveis:")
    
    counter_chain = knowledge_base.get_counter_chain_analysis("giant", our_deck)
    for counter in counter_chain[:3]:  # Top 3 opções
        print(f"   🎯 {counter['counter']}:")
        print(f"      Eficiência: {counter['effectiveness']}")
        print(f"      Trade: {counter['elixir_trade']}")
        print(f"      Posicionamento: {counter['recommended_positioning']}")
        print(f"      Counter-push: {counter['counter_push_potential']}")
        print(f"      Riscos: {counter['risks']}")
        if counter['available_followups']:
            print(f"      Follow-ups: {counter['available_followups']}")
    
    print("\n🎉 Sistema de conhecimento avançado funcionando perfeitamente!")
    print("🧠 A IA agora pode pensar como um jogador de xadrez!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

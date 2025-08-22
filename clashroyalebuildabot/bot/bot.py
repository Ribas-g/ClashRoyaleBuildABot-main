import random
import threading
import time
from typing import Dict, List, Optional, Tuple

import keyboard
from loguru import logger

from clashroyalebuildabot.constants import ALL_TILES
from clashroyalebuildabot.constants import ALLY_TILES
from clashroyalebuildabot.constants import DISPLAY_CARD_DELTA_X
from clashroyalebuildabot.constants import DISPLAY_CARD_HEIGHT
from clashroyalebuildabot.constants import DISPLAY_CARD_INIT_X
from clashroyalebuildabot.constants import DISPLAY_CARD_WIDTH
from clashroyalebuildabot.constants import DISPLAY_CARD_Y
from clashroyalebuildabot.constants import DISPLAY_HEIGHT
from clashroyalebuildabot.constants import LEFT_PRINCESS_TILES
from clashroyalebuildabot.constants import RIGHT_PRINCESS_TILES
from clashroyalebuildabot.constants import TILE_HEIGHT
from clashroyalebuildabot.constants import TILE_INIT_X
from clashroyalebuildabot.constants import TILE_INIT_Y
from clashroyalebuildabot.constants import TILE_WIDTH
from clashroyalebuildabot.detectors.detector import Detector
from clashroyalebuildabot.emulator.emulator import Emulator
from clashroyalebuildabot.ml.data_collector import GameDataCollector
from clashroyalebuildabot.ml.ml_bot import MLBot
from clashroyalebuildabot.ml.deck_analyzer import DeckAnalyzer
from clashroyalebuildabot.ml.enemy_detector import EnemyDetector
from clashroyalebuildabot.ml.generation_manager import GenerationManager
from clashroyalebuildabot.memory import DeckMemory
from clashroyalebuildabot.intelligence import AttentionSystem, TacticalAnalyzer, ComboTiming, MatchupValidator, StrategicThinking, ComboIntelligence, FireballIntelligence, PatternAnalyzer, AdaptiveStrategy
from clashroyalebuildabot.detectors.advanced_detector import AdvancedDetector
from clashroyalebuildabot.intelligence.advanced_mechanics import AdvancedMechanics
try:
    from clashroyalebuildabot.knowledge_base import knowledge_base
    logger.debug("Knowledge base imported successfully")
except Exception as e:
    logger.error(f"Error importing knowledge base: {e}")
    import traceback
    logger.error(f"Knowledge base import traceback: {traceback.format_exc()}")
    # Criar um objeto dummy para evitar erros
    class DummyKnowledgeBase:
        def get_dynamic_position(self, *args, **kwargs):
            return None
        def analyze_card_decision(self, *args, **kwargs):
            return {"decision": "use", "reason": "fallback"}
        def get_counter_suggestions(self, *args, **kwargs):
            return []
        def get_chess_strategy_moves(self, *args, **kwargs):
            return []
        def get_cycling_strategy(self, *args, **kwargs):
            return {"strategy": "neutral", "reason": "fallback"}
        def get_card_intelligence(self, *args, **kwargs):
            return {"type": "unknown", "purpose": "unknown"}
    
    knowledge_base = DummyKnowledgeBase()
    logger.warning("Using dummy knowledge base due to import error")
from clashroyalebuildabot.namespaces import Screens
from clashroyalebuildabot.visualizer import Visualizer
from error_handling import WikifiedError

pause_event = threading.Event()
pause_event.set()
is_paused_logged = False
is_resumed_logged = True


class Bot:
    is_paused_logged = False
    is_resumed_logged = True

    def __init__(self, actions, config):
        self.actions = actions
        self.auto_start = config.get("bot", {}).get("auto_start_game", False)
        self.auto_restart = config.get("bot", {}).get("auto_restart", True)  # Novo: auto restart
        self.end_of_game_clicked = False
        self.should_run = True
        self.games_played = 0  # Contador de partidas jogadas
        self.game_start_time = None  # Tempo de início da partida atual

        cards = [action.CARD for action in actions]
        if len(cards) != 8:
            raise WikifiedError(
                "005", f"Must provide 8 cards but {len(cards)} was given"
            )
        self.cards_to_actions = dict(zip(cards, actions))

        try:
            self.visualizer = Visualizer(**config["visuals"])
            logger.debug("Visualizer initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing visualizer: {e}")
            import traceback
            logger.error(f"Visualizer initialization traceback: {traceback.format_exc()}")
            # Criar um visualizer dummy para evitar erros
            class DummyVisualizer:
                def run(self, *args, **kwargs):
                    pass
            self.visualizer = DummyVisualizer()
            logger.warning("Using dummy visualizer due to initialization error")
        
        try:
            self.emulator = Emulator(**config["adb"])
            logger.debug("Emulator initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing emulator: {e}")
            import traceback
            logger.error(f"Emulator initialization traceback: {traceback.format_exc()}")
            raise  # Emulator é crítico, não podemos continuar sem ele
        
        try:
            self.detector = Detector(cards=cards)
            logger.debug("Detector initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing detector: {e}")
            import traceback
            logger.error(f"Detector initialization traceback: {traceback.format_exc()}")
            raise  # Detector é crítico, não podemos continuar sem ele
        
        # Detector de telas avançado
        try:
            from clashroyalebuildabot.detectors.advanced_screen_detector import AdvancedScreenDetector
            self.advanced_screen_detector = AdvancedScreenDetector()
            logger.debug("Advanced screen detector initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing advanced screen detector: {e}")
            # Fallback para detector dummy
            class DummyAdvancedScreenDetector:
                def run(self, *args): return Screens.UNKNOWN
                def get_screen_info(self, *args): return {'error': 'dummy'}
            self.advanced_screen_detector = DummyAdvancedScreenDetector()
            logger.warning("Using dummy advanced screen detector due to error")
        self.state = None
        self.play_action_delay = config.get("ingame", {}).get("play_action", 1)

        # Sistema de memória de deck
        try:
            self.deck_memory = DeckMemory()
            logger.debug("Deck memory system initialized")
        except Exception as e:
            logger.error(f"Error initializing deck memory: {e}")
            # Criar um sistema dummy
            class DummyDeckMemory:
                def reset_for_new_game(self): pass
                def record_our_card_played(self, card): pass
                def record_enemy_card_seen(self, card): pass
                def get_deck_analysis(self): return {'our_deck': {}, 'enemy_deck': {}}
                def should_expect_card(self, card, within=2): return 0.0
            self.deck_memory = DummyDeckMemory()

        # Sistema de inteligência de atenção (reativado gradualmente)
        try:
            self.attention_system = AttentionSystem()
            logger.debug("Attention system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing attention system: {e}")
            # Fallback para sistema dummy
            class DummyAttentionSystem:
                def calculate_attention_from_position(self, *args): return {'safe_placement': True, 'attention_score': 0}
                def find_safe_position(self, *args): return None
                def analyze_unit_formation(self, *args): return {'formation_type': 'unknown', 'front_line': [], 'back_line': []}
                def _calculate_threat_level(self, *args): return 1.0
            self.attention_system = DummyAttentionSystem()
            logger.warning("Using dummy attention system due to error")

        # Sistema de análise tática profunda
        try:
            self.tactical_analyzer = TacticalAnalyzer()
            logger.debug("Tactical analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing tactical analyzer: {e}")
            # Fallback para sistema dummy
            class DummyTacticalAnalyzer:
                def analyze_threat_situation(self, *args): return {'threat_type': 'none', 'threat_level': 0}
                def analyze_counter_push_opportunity(self, *args): return {'has_opportunity': False}
                def calculate_luring_strategy(self, *args): return {'should_lure': False}
                def evaluate_tactical_decision(self, *args): return {'recommended_action': 'wait'}
            self.tactical_analyzer = DummyTacticalAnalyzer()
            logger.warning("Using dummy tactical analyzer due to error")

        # Sistema de timing de combos
        try:
            self.combo_timing = ComboTiming()
            logger.debug("Combo timing system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing combo timing: {e}")
            # Fallback para sistema dummy
            class DummyComboTiming:
                def should_wait_for_tank(self, *args): return {'should_wait': False, 'wait_time': 0}
                def calculate_combo_timing(self, *args): return {'tank_placement': 'immediate', 'support_delays': {}}
            self.combo_timing = DummyComboTiming()
            logger.warning("Using dummy combo timing due to error")

        # Sistema de validação de matchups
        try:
            self.matchup_validator = MatchupValidator()
            logger.debug("Matchup validator initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing matchup validator: {e}")
            # Fallback para sistema dummy
            class DummyMatchupValidator:
                def validate_card_placement(self, *args): return {'is_valid': True, 'warnings': []}
                def suggest_counter_positioning(self, *args): return {'position': (8, 8), 'reasoning': 'default'}
            self.matchup_validator = DummyMatchupValidator()
            logger.warning("Using dummy matchup validator due to error")

        # Sistema de pensamento estratégico
        try:
            self.strategic_thinking = StrategicThinking()
            logger.debug("Strategic thinking system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing strategic thinking: {e}")
            # Fallback para sistema dummy
            class DummyStrategicThinking:
                def analyze_turn_consequences(self, *args): return {'recommendation': 'proceed', 'reasoning': ['default']}
                def record_turn(self, *args): pass
            self.strategic_thinking = DummyStrategicThinking()
            logger.warning("Using dummy strategic thinking due to error")

        # Sistema de inteligência de combos
        try:
            self.combo_intelligence = ComboIntelligence()
            logger.debug("Combo intelligence system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing combo intelligence: {e}")
            # Fallback para sistema dummy
            class DummyComboIntelligence:
                def analyze_combo_opportunity(self, *args): return {'should_combo': False, 'reasoning': ['default']}
                def should_wait_for_combo(self, *args): return {'should_wait': False, 'reasoning': ['default']}
                def record_combo_execution(self, *args): pass
                def get_combo_timing_instructions(self, *args): return {'instructions': ['default']}
            self.combo_intelligence = DummyComboIntelligence()
            logger.warning("Using dummy combo intelligence due to error")

        # Sistema de inteligência da bola de fogo
        try:
            self.fireball_intelligence = FireballIntelligence()
            logger.debug("Fireball intelligence system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing fireball intelligence: {e}")
            # Fallback para sistema dummy
            class DummyFireballIntelligence:
                def analyze_fireball_targets(self, *args): return {'should_cast': False, 'reasoning': ['default']}
                def record_fireball_usage(self, *args): pass
                def get_fireball_statistics(self): return {'total_uses': 0, 'success_rate': 0.0}
            self.fireball_intelligence = DummyFireballIntelligence()
            logger.warning("Using dummy fireball intelligence due to error")

        # Sistema de gerações ML
        try:
            self.generation_manager = GenerationManager()
            logger.debug("Generation manager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing generation manager: {e}")
            # Fallback para sistema dummy
            class DummyGenerationManager:
                def should_evolve(self, *args): return False
                def create_new_generation(self, *args): return 0
                def load_best_generation(self): return None, None, {}
                def get_generation_statistics(self): return {}
            self.generation_manager = DummyGenerationManager()
            logger.warning("Using dummy generation manager due to error")

        # Sistema de detecção avançada
        try:
            self.advanced_detector = AdvancedDetector()
            logger.debug("Advanced detector initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing advanced detector: {e}")
            # Fallback para sistema dummy
            class DummyAdvancedDetector:
                def detect_units_on_field(self, *args): return []
                def detect_buildings(self, *args): return []
                def detect_cards_in_hand(self, *args): return []
                def detect_elixir(self, *args): return 0.0
                def detect_tower_health(self, *args): return {'ally_left': 1.0, 'ally_right': 1.0, 'enemy_left': 1.0, 'enemy_right': 1.0}
                def get_game_state(self, *args): return {}
            self.advanced_detector = DummyAdvancedDetector()
            logger.warning("Using dummy advanced detector due to error")

        # Sistema de mecânicas avançadas
        try:
            self.advanced_mechanics = AdvancedMechanics()
            logger.debug("Advanced mechanics initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing advanced mechanics: {e}")
            # Fallback para sistema dummy
            class DummyAdvancedMechanics:
                def calculate_unit_interaction(self, *args): return {}
                def calculate_optimal_positioning(self, *args): return (9, 7)
                def calculate_spell_value(self, *args): return 0.0
                def calculate_push_timing(self, *args): return {}
                def calculate_counter_push_opportunity(self, *args): return {}
                def calculate_elixir_efficiency(self, *args): return 0.0
                def get_unit_priorities(self, *args): return {}
            self.advanced_mechanics = DummyAdvancedMechanics()
            logger.warning("Using dummy advanced mechanics due to error")

        # Sistema de análise de padrões
        try:
            self.pattern_analyzer = PatternAnalyzer()
            logger.debug("Pattern analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing pattern analyzer: {e}")
            # Fallback para sistema dummy
            class DummyPatternAnalyzer:
                def record_opponent_action(self, *args): pass
                def get_opponent_profile(self): return {'playstyle': 'unknown', 'confidence': 0.0}
                def end_game(self, *args): pass
                def get_analysis_summary(self): return {'analysis_confidence': 0.0}
            self.pattern_analyzer = DummyPatternAnalyzer()
            logger.warning("Using dummy pattern analyzer due to error")

        # Sistema de estratégia adaptativa
        try:
            self.adaptive_strategy = AdaptiveStrategy()
            logger.debug("Adaptive strategy initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing adaptive strategy: {e}")
            # Fallback para sistema dummy
            class DummyAdaptiveStrategy:
                def analyze_opponent_and_adapt(self, *args): return {'strategy': 'balanced', 'config': {}, 'reason': 'default'}
                def get_strategy_recommendations(self, *args): return {'strategy': 'balanced', 'should_push': False, 'should_defend': True}
                def get_adaptation_summary(self): return {'current_strategy': 'balanced', 'adaptation_count': 0}
                def reset_strategy(self): pass
            self.adaptive_strategy = DummyAdaptiveStrategy()
            logger.warning("Using dummy adaptive strategy due to error")

        # Machine Learning components
        self.enable_ml = config.get("ml", {}).get("enabled", True)
        if self.enable_ml:
            try:
                logger.debug("Initializing GameDataCollector...")
                self.data_collector = GameDataCollector(
                    config.get("ml", {}).get("data_path", "game_data.json")
                )
                logger.debug("GameDataCollector initialized")
                
                logger.debug("Initializing MLBot with generation manager...")
                self.ml_bot = MLBot(
                    config.get("ml", {}).get("model_path", "ml_model.pkl"),
                    generation_manager=self.generation_manager
                )
                logger.debug("MLBot initialized with generation support")
                
                # Deck analysis system
                logger.debug("Initializing DeckAnalyzer...")
                self.deck_analyzer = DeckAnalyzer(
                    config.get("ml", {}).get("deck_memory_path", "deck_memory.json")
                )
                logger.debug("DeckAnalyzer initialized")
                
                logger.debug("Initializing EnemyDetector...")
                self.enemy_detector = EnemyDetector(self.deck_analyzer)
                logger.debug("EnemyDetector initialized")
                
                self.game_started = False
                logger.info("Machine Learning and Deck Analysis system initialized")
            except Exception as e:
                logger.error(f"Error initializing ML components: {e}")
                import traceback
                logger.error(f"ML initialization traceback: {traceback.format_exc()}")
                # Fallback: disable ML if initialization fails
                self.enable_ml = False
                self.data_collector = None
                self.ml_bot = None
                self.deck_analyzer = None
                self.enemy_detector = None
                logger.warning("ML system disabled due to initialization error")
        else:
            self.data_collector = None
            self.ml_bot = None
            self.deck_analyzer = None
            self.enemy_detector = None
            logger.info("Machine Learning disabled")

        try:
            keyboard_thread = threading.Thread(
                target=self._handle_keyboard_shortcut, daemon=True
            )
            keyboard_thread.start()
            logger.debug("Keyboard thread started successfully")
        except Exception as e:
            logger.error(f"Error starting keyboard thread: {e}")
            # Não falhar a inicialização por causa do keyboard thread

        try:
            if config["bot"]["load_deck"]:
                self.emulator.load_deck(cards)
                logger.debug("Deck loaded successfully")
        except Exception as e:
            logger.error(f"Error loading deck: {e}")
            # Não falhar a inicialização por causa do carregamento do deck

    @staticmethod
    def _log_and_wait(prefix, delay):
        suffix = ""
        if delay > 1:
            suffix = "s"
        message = f"{prefix}. Waiting for {delay} second{suffix}."
        logger.info(message)
        time.sleep(delay)

    @staticmethod
    def _handle_keyboard_shortcut():
        while True:
            keyboard.wait("ctrl+p")
            Bot.pause_or_resume()

    @staticmethod
    def pause_or_resume():
        if pause_event.is_set():
            logger.info("Bot paused.")
            pause_event.clear()
            Bot.is_paused_logged = True
            Bot.is_resumed_logged = False
        else:
            logger.info("Bot resumed.")
            pause_event.set()
            Bot.is_resumed_logged = True
            Bot.is_paused_logged = False

    @staticmethod
    def _get_nearest_tile(x, y):
        tile_x = round(((x - TILE_INIT_X) / TILE_WIDTH) - 0.5)
        tile_y = round(
            ((DISPLAY_HEIGHT - TILE_INIT_Y - y) / TILE_HEIGHT) - 0.5
        )
        return tile_x, tile_y

    @staticmethod
    def _get_tile_centre(tile_x, tile_y):
        x = TILE_INIT_X + (tile_x + 0.5) * TILE_WIDTH
        y = DISPLAY_HEIGHT - TILE_INIT_Y - (tile_y + 0.5) * TILE_HEIGHT
        return x, y

    @staticmethod
    def _get_card_centre(card_n):
        x = (
            DISPLAY_CARD_INIT_X
            + DISPLAY_CARD_WIDTH / 2
            + card_n * DISPLAY_CARD_DELTA_X
        )
        y = DISPLAY_CARD_Y + DISPLAY_CARD_HEIGHT / 2
        return x, y

    def _get_valid_tiles(self):
        tiles = ALLY_TILES
        
        # Verifica torres inimigas destruídas
        left_enemy_tower_destroyed = self.state.numbers.left_enemy_princess_hp.number == 0
        right_enemy_tower_destroyed = self.state.numbers.right_enemy_princess_hp.number == 0
        
        if left_enemy_tower_destroyed:
            tiles += LEFT_PRINCESS_TILES
            logger.debug("Left enemy tower destroyed - expanded tiles")
        if right_enemy_tower_destroyed:
            tiles += RIGHT_PRINCESS_TILES
            logger.debug("Right enemy tower destroyed - expanded tiles")
        
        return tiles
    
    def _analyze_tower_situation(self):
        """Analisa situação das torres"""
        tower_analysis = {
            'our_towers': {
                'left': {'destroyed': False, 'health': 100, 'under_attack': False},
                'right': {'destroyed': False, 'health': 100, 'under_attack': False},
                'king': {'destroyed': False, 'health': 100, 'under_attack': False}
            },
            'enemy_towers': {
                'left': {'destroyed': False, 'health': 100, 'under_attack': False},
                'right': {'destroyed': False, 'health': 100, 'under_attack': False},
                'king': {'destroyed': False, 'health': 100, 'under_attack': False}
            },
            'strategy_changes': []
        }
        
        # Analisa torres inimigas (corrigido para evitar falsos positivos)
        try:
            if hasattr(self.state.numbers, 'left_enemy_princess_hp'):
                left_hp = self.state.numbers.left_enemy_princess_hp.number
                tower_analysis['enemy_towers']['left']['health'] = left_hp
                logger.debug(f"Left enemy tower HP detected: {left_hp}")
                
                # Só considera destruída se HP for realmente 0 e confirmado
                if left_hp < 0.1:  # Muito próximo de 0
                    if not hasattr(self, '_enemy_left_tower_destroyed_logged'):
                        tower_analysis['enemy_towers']['left']['destroyed'] = True
                        tower_analysis['strategy_changes'].append('enemy_left_tower_down')
                        logger.info("Enemy left tower destroyed!")
                        self._enemy_left_tower_destroyed_logged = True
                else:
                    logger.debug(f"Enemy left tower alive with HP: {left_hp}")
            else:
                logger.debug("Enemy left tower HP not detected, assuming alive")
        except Exception as e:
            logger.debug(f"Error reading enemy left tower HP: {e}")
        
        try:
            if hasattr(self.state.numbers, 'right_enemy_princess_hp'):
                right_hp = self.state.numbers.right_enemy_princess_hp.number
                tower_analysis['enemy_towers']['right']['health'] = right_hp
                logger.debug(f"Right enemy tower HP detected: {right_hp}")
                
                # Só considera destruída se HP for realmente 0 e confirmado
                if right_hp < 0.1:  # Muito próximo de 0
                    if not hasattr(self, '_enemy_right_tower_destroyed_logged'):
                        tower_analysis['enemy_towers']['right']['destroyed'] = True
                        tower_analysis['strategy_changes'].append('enemy_right_tower_down')
                        logger.info("Enemy right tower destroyed!")
                        self._enemy_right_tower_destroyed_logged = True
                else:
                    logger.debug(f"Enemy right tower alive with HP: {right_hp}")
            else:
                logger.debug("Enemy right tower HP not detected, assuming alive")
        except Exception as e:
            logger.debug(f"Error reading enemy right tower HP: {e}")
        
        # Analisa nossas torres (corrigido - estava detectando torres próprias como destruídas)
        # IMPORTANTE: No Clash Royale, as torres aliadas têm nomes diferentes
        # Vamos verificar se as propriedades existem antes de usar
        try:
            if hasattr(self.state.numbers, 'left_ally_princess_hp'):
                left_hp = self.state.numbers.left_ally_princess_hp.number
                tower_analysis['our_towers']['left']['health'] = left_hp
                logger.debug(f"Left ally tower HP detected: {left_hp}")
                
                # TEMPORÁRIO: Desabilitando detecção de torre destruída para debug
                # Só considera destruída se HP for realmente 0 e confirmado
                if left_hp < 0.1:  # Muito próximo de 0
                    if not hasattr(self, '_left_tower_destroyed_logged'):
                        tower_analysis['our_towers']['left']['destroyed'] = True
                        tower_analysis['strategy_changes'].append('our_left_tower_down')
                        logger.warning("Our left tower destroyed!")
                        self._left_tower_destroyed_logged = True
                else:
                    logger.debug(f"Left ally tower alive with HP: {left_hp}")
            else:
                # Se não consegue detectar, assume que está viva
                tower_analysis['our_towers']['left']['health'] = 100
                logger.debug("Left ally tower HP not detected, assuming alive")
        except Exception as e:
            logger.debug(f"Error reading left ally tower HP: {e}")
            tower_analysis['our_towers']['left']['health'] = 100
        
        try:
            if hasattr(self.state.numbers, 'right_ally_princess_hp'):
                right_hp = self.state.numbers.right_ally_princess_hp.number
                tower_analysis['our_towers']['right']['health'] = right_hp
                logger.debug(f"Right ally tower HP detected: {right_hp}")
                
                # TEMPORÁRIO: Desabilitando detecção de torre destruída para debug
                # Só considera destruída se HP for realmente 0 e confirmado
                if right_hp < 0.1:  # Muito próximo de 0
                    if not hasattr(self, '_right_tower_destroyed_logged'):
                        tower_analysis['our_towers']['right']['destroyed'] = True
                        tower_analysis['strategy_changes'].append('our_right_tower_down')
                        logger.warning("Our right tower destroyed!")
                        self._right_tower_destroyed_logged = True
                else:
                    logger.debug(f"Right ally tower alive with HP: {right_hp}")
            else:
                # Se não consegue detectar, assume que está viva
                tower_analysis['our_towers']['right']['health'] = 100
                logger.debug("Right ally tower HP not detected, assuming alive")
        except Exception as e:
            logger.debug(f"Error reading right ally tower HP: {e}")
            tower_analysis['our_towers']['right']['health'] = 100
        
        # Verifica se torres estão sob ataque
        enemy_units = self._get_enemy_units()
        for unit in enemy_units:
            x, y = unit['position']
            if y > 14:  # Próximo das nossas torres
                if x < 9:  # Lane esquerda
                    tower_analysis['our_towers']['left']['under_attack'] = True
                else:  # Lane direita
                    tower_analysis['our_towers']['right']['under_attack'] = True
        
        return tower_analysis

    def get_actions(self):
        if not self.state:
            logger.warning("No state available")
            return []
        
        # Adiciona logs para diagnosticar
        logger.debug(f"State ready cards: {self.state.ready}")
        logger.debug(f"State cards: {len(self.state.cards) if self.state.cards else 0}")
        logger.debug(f"State elixir: {self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 'N/A'}")
        
        valid_tiles = self._get_valid_tiles()
        actions = []
        for i in self.state.ready:
            card = self.state.cards[i + 1]
            if self.state.numbers.elixir.number < card.cost:
                logger.debug(f"Card {card.name} too expensive: {card.cost} > {self.state.numbers.elixir.number}")
                continue

            tiles = ALL_TILES if card.target_anywhere else valid_tiles
            card_actions = [
                self.cards_to_actions[card](i, x, y) for (x, y) in tiles
            ]
            actions.extend(card_actions)

        logger.debug(f"Generated {len(actions)} actions")
        return actions

    def set_state(self):
        try:
            logger.debug("Taking screenshot from emulator")
            screenshot = self.emulator.take_screenshot()
            logger.debug("Screenshot taken successfully")
            
            logger.debug("Running detector on screenshot")
            self.state = self.detector.run(screenshot)
            logger.debug("Detector run completed")
            
            # Usar detector avançado se o detector normal não conseguiu detectar
            if hasattr(self.state, 'screen') and self.state.screen.name == 'unknown':
                logger.debug("Unknown screen detected, trying advanced detector")
                try:
                    advanced_screen = self.advanced_screen_detector.run(screenshot)
                    if advanced_screen.name != 'unknown':
                        logger.info(f"Advanced detector found: {advanced_screen.name}")
                        # Atualizar a tela detectada
                        self.state.screen = advanced_screen
                        
                        # Se detectou tela de resultado, adicionar coordenadas de clique
                        if advanced_screen.name == 'result_screen':
                            logger.info("🎯 Tela de resultado detectada pelo detector avançado")
                            # Criar uma tela de resultado com coordenadas de clique
                            from clashroyalebuildabot.namespaces.screens import Screen
                            result_screen = Screen(
                                name="result_screen",
                                ltrb=(200, 200, 520, 700),
                                click_xy=(360, 650)  # Posição do botão jogar de novo
                            )
                            self.state.screen = result_screen
                except Exception as adv_error:
                    logger.warning(f"Advanced detector error: {adv_error}")
            
            # Só executa visualizer se não houver erro
            try:
                logger.debug("Running visualizer")
                self.visualizer.run(screenshot, self.state)
                logger.debug("Visualizer completed")
            except Exception as viz_error:
                logger.warning(f"Visualizer error (non-critical): {viz_error}")
            
            # Adiciona logs para diagnosticar
            if self.state:
                logger.debug(f"State detected - Screen: {self.state.screen}")
                if hasattr(self.state, 'cards'):
                    logger.debug(f"Cards detected: {len(self.state.cards) if self.state.cards else 0}")
                if hasattr(self.state, 'ready'):
                    logger.debug(f"Ready cards: {self.state.ready}")
            else:
                logger.warning("No state detected from screenshot")
        except Exception as e:
            logger.error(f"CRITICAL ERROR in set_state: {e}")
            import traceback
            logger.error(f"set_state traceback: {traceback.format_exc()}")
            # Não define state como None para evitar crashes
            # Mantém o estado anterior se disponível
            if not hasattr(self, 'state') or self.state is None:
                # Cria um estado dummy para evitar crashes
                logger.warning("Creating dummy state due to error")
                from clashroyalebuildabot.namespaces import State
                self.state = State([], [], [], [], False, Screens.UNKNOWN)

    def play_action(self, action):
        try:
            card_centre = self._get_card_centre(action.index)
            
            # Usar posicionamento inteligente se disponível
            optimal_tile = self._get_optimal_tile_position(action)
            if optimal_tile:
                tile_centre = self._get_tile_centre(optimal_tile[0], optimal_tile[1])
            else:
                tile_centre = self._get_tile_centre(action.tile_x, action.tile_y)
            
            self.emulator.click(*card_centre)
            self.emulator.click(*tile_centre)
        except Exception as e:
            logger.error(f"Error playing action {action}: {e}")
            # Não falha a execução, apenas loga o erro
    
    def _get_optimal_tile_position(self, action):
        """Determina a posição ótima para uma carta baseado na inteligência dinâmica"""
        if not hasattr(self.state, 'cards') or len(self.state.cards) <= action.index + 1:
            return None
        
        card_name = self.state.cards[action.index + 1].name
        if card_name == "unknown" or card_name == "blank":
            return None
        
        # Posicionamento específico para feitiços
        if card_name in ['fireball', 'zap', 'arrows']:
            return self._get_spell_position(card_name, action)
        
        # Posicionamento específico para unidades (deck real do usuário)
        if card_name in ['giant', 'knight', 'archers', 'musketeer', 'minipekka', 'minions', 'spear_goblins']:
            return self._get_unit_position(card_name, action)
        
        # Criar estado do jogo para análise dinâmica
        game_state = {
            "elixir": self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0,
            "enemy_elixir": self._estimate_enemy_elixir(),
            "under_pressure": self._is_under_pressure(),
            "advantage": self._has_advantage(),
            "tower_health": self._get_tower_health(),
            "game_time": self._get_game_time()
        }
        
        # Obter unidades inimigas e nossas
        enemy_units = self._get_enemy_units()
        our_units = self._get_our_units()
        
        # Obter posicionamento dinâmico
        dynamic_position = knowledge_base.get_dynamic_position(card_name, game_state, enemy_units, our_units)
        
        if dynamic_position and 'position' in dynamic_position:
            position = dynamic_position['position']
            if 'tile_x' in position and 'tile_y' in position:
                # Log da decisão de posicionamento
                logger.debug(f"Posicionamento dinâmico para {card_name}: {dynamic_position['reasoning']}")
                return (position['tile_x'], position['tile_y'])
        
        # Fallback para posicionamento original
        return None

    def _get_spell_position(self, spell_name, action):
        """Determina posição ótima para feitiços com validação rigorosa"""
        enemy_units = self._get_enemy_units()
        
        # CRÍTICO: Se não há inimigos, NÃO joga o feitiço
        if not enemy_units:
            logger.debug(f"No enemy units found, not playing {spell_name}")
            return None
        
        # Para Fireball, procura agrupamento de inimigos
        if spell_name == 'fireball':
            best_position = self._find_best_fireball_position(enemy_units)
            if best_position:
                # Validação extra: verifica se vale a pena jogar
                if self._validate_fireball_usage(best_position, enemy_units):
                    return best_position
                else:
                    logger.debug("Fireball usage not validated, skipping")
                    return None
        
        # Para Zap, procura inimigos próximos às torres
        elif spell_name == 'zap':
            best_position = self._find_best_zap_position(enemy_units)
            if best_position and self._validate_zap_usage(best_position, enemy_units):
                return best_position
        
        # Para Arrows, procura inimigos aéreos
        elif spell_name == 'arrows':
            best_position = self._find_best_arrows_position(enemy_units)
            if best_position and self._validate_arrows_usage(best_position, enemy_units):
                return best_position
        
        # Se chegou até aqui, não há posição válida
        logger.debug(f"No valid position found for {spell_name}")
        return None

    def _find_best_fireball_position(self, enemy_units):
        """Encontra a melhor posição para Fireball usando inteligência avançada"""
        try:
            # Obter construções inimigas (se disponível)
            enemy_buildings = self._get_enemy_buildings()
            
            # Usar sistema de inteligência da bola de fogo
            analysis = self.fireball_intelligence.analyze_fireball_targets(enemy_units, enemy_buildings)
            
            # Log da análise
            logger.info(f"🔥 FIREBALL INTELLIGENCE ANALYSIS:")
            for reason in analysis.get('reasoning', []):
                logger.info(f"   • {reason}")
            
            if analysis.get('should_cast', False):
                target_position = analysis.get('target_position')
                expected_value = analysis.get('expected_value', 0)
                best_target = analysis.get('best_target', {})
                
                # Log do timing de casting
                timing_instructions = analysis.get('timing_instructions', {})
                if timing_instructions.get('instructions'):
                    logger.info(f"⏱️ CASTING TIMING:")
                    for instruction in timing_instructions['instructions']:
                        logger.info(f"   • {instruction}")
                
                logger.info(f"🎯 FIREBALL TARGET: {best_target.get('name', 'unknown')} at {target_position}")
                logger.info(f"💰 EXPECTED VALUE: {expected_value} elixir")
                
                return target_position
            else:
                logger.info("🚫 No viable Fireball targets - holding spell")
                return None
                
        except Exception as e:
            logger.debug(f"Error in fireball intelligence: {e}")
            # Fallback para método antigo
            return self._find_best_fireball_position_fallback(enemy_units)
    
    def _find_best_fireball_position_fallback(self, enemy_units):
        """Método fallback para posicionamento da bola de fogo"""
        if not enemy_units:
            return None
        
        # REGRA CRÍTICA: NUNCA mirar na torre do rei (y > 14)
        valid_targets = []
        for unit in enemy_units:
            unit_x, unit_y = unit['position']
            
            # BLOQUEAR: Unidades muito próximas da nossa torre
            if unit_y > 14:
                logger.error(f"🚫 BLOCKING FIREBALL: {unit['name']} too close to our king tower (y={unit_y})")
                continue
            
            # BLOQUEAR: Unidades atrás da torre inimiga (y < 5)
            if unit_y < 5:
                logger.warning(f"⚠️ {unit['name']} behind enemy tower - not worth Fireball")
                continue
            
            valid_targets.append(unit)
        
        if not valid_targets:
            logger.warning("🚫 No valid Fireball targets found")
            return None
        
        best_score = 0
        best_position = None
        
        # Procura por agrupamentos de inimigos válidos
        for unit in valid_targets:
            nearby_enemies = 0
            total_value = 0
            
            for other_unit in valid_targets:
                if unit != other_unit:
                    distance = ((unit['position'][0] - other_unit['position'][0])**2 + 
                              (unit['position'][1] - other_unit['position'][1])**2)**0.5
                    if distance <= 3:  # Raio do Fireball
                        nearby_enemies += 1
                        total_value += self._estimate_card_cost(other_unit['name'])
            
            # Score baseado no número de inimigos próximos e valor
            if nearby_enemies >= 1 and total_value >= 4:  # Mínimo para valer a pena
                score = nearby_enemies * 2 + total_value
                
                # Bônus para alvos de alto valor
                if unit['name'] in ['musketeer', 'wizard', 'witch', 'archers']:
                    score += 3
                
                if score > best_score:
                    best_score = score
                    best_position = (unit['position'][0], unit['position'][1])
        
        if best_position:
            logger.info(f"🎯 Fireball targeting position {best_position} with score {best_score}")
        
        return best_position

    def _find_best_zap_position(self, enemy_units):
        """Encontra a melhor posição para Zap"""
        # Procura inimigos próximos às torres
        for unit in enemy_units:
            if unit['position'][1] > 14:  # Muito próximo às torres
                return (unit['position'][0], unit['position'][1])
        
        # Fallback: inimigo mais próximo
        return self._find_closest_enemy_to_tower(enemy_units)

    def _find_best_arrows_position(self, enemy_units):
        """Encontra a melhor posição para Arrows"""
        # Procura inimigos aéreos
        air_units = ['baby_dragon', 'minions', 'bats']
        for unit in enemy_units:
            if unit['name'] in air_units:
                return (unit['position'][0], unit['position'][1])
        
        # Fallback: inimigo mais próximo
        return self._find_closest_enemy_to_tower(enemy_units)

    def _find_closest_enemy_to_tower(self, enemy_units):
        """Encontra o inimigo mais próximo da torre"""
        if not enemy_units:
            return None
        
        closest_unit = min(enemy_units, key=lambda u: u['position'][1])
        return (closest_unit['position'][0], closest_unit['position'][1])
    
    def _validate_fireball_usage(self, position, enemy_units):
        """Valida se vale a pena jogar Fireball usando inteligência avançada"""
        try:
            if not position:
                return False
            
            target_x, target_y = position
            
            # REGRA FUNDAMENTAL: NUNCA jogar Fireball nas nossas torres
            if target_y > 14:
                logger.error(f"🚫 BLOCKING FIREBALL: Targeting our towers at {position}")
                return False
            
            # REGRA: NUNCA jogar Fireball para cycle
            if not enemy_units:
                logger.error(f"🚫 BLOCKING FIREBALL: No enemies - not for cycling!")
                return False
            
            # Usar sistema de inteligência da bola de fogo para validação
            enemy_buildings = self._get_enemy_buildings()
            analysis = self.fireball_intelligence.analyze_fireball_targets(enemy_units, enemy_buildings)
            
            if analysis.get('should_cast', False):
                # Registrar uso para aprendizado
                best_target = analysis.get('best_target', {})
                self.fireball_intelligence.record_fireball_usage(best_target, True, 0)  # Success será atualizado depois
                
                logger.info(f"✅ FIREBALL VALIDATED: {best_target.get('name', 'unknown')} - Expected value: {analysis.get('expected_value', 0)}")
                return True
            else:
                logger.info("🚫 FIREBALL REJECTED: No viable targets found")
                return False
                
        except Exception as e:
            logger.debug(f"Error in fireball validation: {e}")
            # Fallback para validação básica
            return self._validate_fireball_usage_fallback(position, enemy_units)
    
    def _validate_fireball_usage_fallback(self, position, enemy_units):
        """Validação fallback para bola de fogo"""
        if not position:
            return False
        
        target_x, target_y = position
        
        # REGRA FUNDAMENTAL: NUNCA jogar Fireball nas nossas torres
        if target_y > 14:
            logger.error(f"🚫 BLOCKING FIREBALL: Targeting our towers at {position}")
            return False
        
        # REGRA: NUNCA jogar Fireball para cycle
        if not enemy_units:
            logger.error(f"🚫 BLOCKING FIREBALL: No enemies - not for cycling!")
            return False
        
        # Calcula valor das tropas que serão atingidas
        total_value = 0
        units_hit = 0
        high_value_targets = []
        
        for unit in enemy_units:
            unit_x, unit_y = unit['position']
            unit_name = unit.get('name', '')
            distance = ((target_x - unit_x)**2 + (target_y - unit_y)**2)**0.5
            
            if distance <= 2.5:  # Raio do Fireball
                units_hit += 1
                unit_value = self._estimate_card_cost(unit_name)
                total_value += unit_value
                
                # Alvos de alto valor para Fireball
                if unit_name in ['musketeer', 'wizard', 'witch', 'archers']:
                    high_value_targets.append(unit_name)
        
        # VALIDAÇÃO PROFISSIONAL
        
        # 1. Deve atingir pelo menos 4 elixir de valor
        if total_value < 4:
            logger.debug(f"🚫 Fireball not worth: only {total_value} elixir value (need 4+)")
            return False
        
        # 2. OU deve atingir alvos de alto valor específicos
        if high_value_targets:
            logger.info(f"🎯 Fireball targeting high-value: {high_value_targets}")
            return True
        
        # 3. OU deve atingir múltiplas tropas (2+)
        if units_hit >= 2 and total_value >= 4:
            logger.info(f"💥 Fireball validated: {units_hit} units, {total_value} elixir value")
            return True
        
        # 4. Caso especial: Torre com HP baixo
        # TODO: Implementar detecção de HP da torre inimiga
        
        logger.debug(f"🚫 Fireball rejected: {units_hit} units, {total_value} elixir value, targets: {[u.get('name') for u in enemy_units if ((target_x - u['position'][0])**2 + (target_y - u['position'][1])**2)**0.5 <= 2.5]}")
        return False
    
    def _validate_zap_usage(self, position, enemy_units):
        """Valida se vale a pena jogar Zap"""
        if not position:
            return False
        
        # Zap é barato, mais flexível na validação
        target_x, target_y = position
        
        # Não joga Zap nas nossas torres
        if target_y > 14:
            return False
        
        # Verifica se há tropas pequenas para stunnar
        for unit in enemy_units:
            unit_x, unit_y = unit['position']
            distance = ((target_x - unit_x)**2 + (target_y - unit_y)**2)**0.5
            
            if distance <= 2.5:  # Raio do Zap
                return True
        
        return False
    
    def _validate_arrows_usage(self, position, enemy_units):
        """Valida se vale a pena jogar Arrows"""
        if not position:
            return False
        
        target_x, target_y = position
        
        # Não joga Arrows nas nossas torres
        if target_y > 14:
            return False
        
        # Procura por tropas aéreas ou swarms
        air_units = ['minions', 'bats', 'baby_dragon']
        swarm_units = ['skeleton_army', 'goblin_gang', 'minion_horde']
        
        for unit in enemy_units:
            if unit['name'] in air_units or unit['name'] in swarm_units:
                unit_x, unit_y = unit['position']
                distance = ((target_x - unit_x)**2 + (target_y - unit_y)**2)**0.5
                
                if distance <= 4:  # Raio do Arrows
                    return True
        
        return False

    def _get_unit_position(self, unit_name, action):
        """Determina posição ótima para unidades com análise tática avançada"""
        situation_analysis = self._analyze_game_situation()
        tower_analysis = self._analyze_tower_situation()
        enemy_units = self._get_enemy_units()
        our_units = self._get_our_units()
        
        # === ANÁLISE TÁTICA AVANÇADA ===
        
        # 1. Verificar se é posicionamento de suporte coordenado COM TIMING CORRETO
        try:
            our_units = self._get_our_units()
            coordination_analysis = self.tactical_analyzer.analyze_push_coordination(our_units, unit_name)
            
            if coordination_analysis['should_coordinate']:
                # Verificar timing antes de coordenar
                primary_unit = coordination_analysis.get('primary_unit')
                if primary_unit:
                    timing_check = self.combo_timing.should_wait_for_tank(
                        primary_unit['name'], unit_name, primary_unit['position']
                    )
                    
                    if timing_check['should_wait']:
                        wait_time = timing_check['wait_time']
                        logger.info(f"⏰ {unit_name} should wait {wait_time:.1f}s for {primary_unit['name']} to lead")
                        # Retornar None para não jogar agora, aguardar timing
                        return None
                    else:
                        coord_pos = coordination_analysis['support_positioning']['position']
                        logger.info(f"🤝 Coordinated support: {unit_name} supporting {coordination_analysis['coordination_type']}")
                        return self._apply_positioning_precision(coord_pos[0], coord_pos[1], unit_name)
                
        except Exception as e:
            logger.debug(f"Error in coordination analysis: {e}")
        
        # 2. Verificar se deve usar tática de luring
        try:
            if enemy_units:
                # Encontrar ameaça principal para luring
                main_threat = max(enemy_units, key=lambda u: self.attention_system._calculate_threat_level(u['name'], u['position'][1]))
                
                available_cards = [self.state.cards[i + 1].name for i in self.state.ready if i + 1 < len(self.state.cards)]
                our_elixir = self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0
                
                luring_strategy = self.tactical_analyzer.calculate_luring_strategy(main_threat, available_cards, our_elixir)
                
                if luring_strategy['should_lure'] and unit_name == luring_strategy['lure_card']:
                    lure_pos = luring_strategy['lure_position']
                    logger.info(f"🎣 Luring tactic: {unit_name} to distract {main_threat['name']}")
                    return self._apply_positioning_precision(lure_pos[0], lure_pos[1], unit_name)
                    
        except Exception as e:
            logger.debug(f"Error in luring analysis: {e}")
        
        # 3. Análise de formação tradicional
        try:
            if enemy_units and our_units:
                enemy_formation = self.attention_system.analyze_unit_formation(enemy_units)
                our_formation = self.attention_system.analyze_unit_formation(our_units)
                
                logger.debug(f"Enemy formation: {enemy_formation.get('formation_type', 'unknown')}")
                logger.debug(f"Our formation: {our_formation.get('formation_type', 'unknown')}")
                
                # Determina posicionamento baseado na formação inimiga
                strategic_position = self._calculate_strategic_position(unit_name, enemy_formation, our_formation, situation_analysis)
                if strategic_position:
                    logger.info(f"Strategic positioning for {unit_name}: {strategic_position} vs {enemy_formation['formation_type']}")
                    return strategic_position
            else:
                logger.debug("No units for formation analysis")
        except Exception as e:
            logger.debug(f"Error in strategic positioning: {e}")
            # Continua com posicionamento padrão
        
        # Adiciona variação aleatória pequena para não ser previsível
        variation_x = random.randint(-1, 1)  # Variação de -1 a +1 tile
        variation_y = random.randint(0, 1)   # Variação de 0 a +1 tile
        
        # Posicionamento para cycle
        if situation_analysis['should_cycle']:
            if unit_name == 'spear_goblins':
                base_x, base_y = 3, 8
                return self._apply_positioning_precision(base_x + variation_x, base_y, unit_name)
        
        # Posicionamento defensivo com variação
        if situation_analysis['should_defend']:
            if unit_name == 'knight':
                base_x, base_y = 8, 10
                return self._apply_positioning_precision(base_x + variation_x, base_y, unit_name)
            elif unit_name == 'archers':
                # Varia posição das arqueiras para não ser previsível
                positions = [(6, 9), (10, 9), (4, 8), (12, 8)]
                base_x, base_y = random.choice(positions)
                return self._apply_positioning_precision(base_x, base_y, unit_name)
            elif unit_name == 'musketeer':
                base_x, base_y = 9, 9
                return self._apply_positioning_precision(base_x + variation_x, base_y, unit_name)
            elif unit_name == 'minipekka':
                # Mini Pekka vai direto para onde há ameaça
                enemy_units = self._get_enemy_units()
                if enemy_units:
                    # Procura por tanks inimigos
                    tank_enemies = [u for u in enemy_units if u['name'] in ['giant', 'pekka', 'golem', 'royal_giant']]
                    if tank_enemies:
                        closest_tank = min(tank_enemies, key=lambda u: u['position'][1])
                        return self._apply_positioning_precision(closest_tank['position'][0], closest_tank['position'][1] + 1, unit_name)
                base_x, base_y = 8, 9
                return self._apply_positioning_precision(base_x + variation_x, base_y, unit_name)
            elif unit_name == 'spear_goblins':
                base_x, base_y = 8, 11
                return self._apply_positioning_precision(base_x + variation_x, base_y, unit_name)
            elif unit_name == 'minions':
                base_x, base_y = 7, 9
                return self._apply_positioning_precision(base_x + variation_x, base_y, unit_name)
        
        # Posicionamento ofensivo
        elif situation_analysis['should_attack']:
            if unit_name == 'giant':
                return (7, 5)  # Bridge push clássico
            elif unit_name == 'archers':
                return (5, 6)  # Suporte atrás do tank
            elif unit_name == 'musketeer':
                return (5, 6)  # Suporte de longo alcance
            elif unit_name == 'minions':
                return (8, 4)  # Ataque aéreo nas torres
            elif unit_name == 'spear_goblins':
                return (12, 8)  # Split push ou distração
        
        # Posicionamento de counter
        elif situation_analysis['should_counter']:
            enemy_units = self._get_enemy_units()
            if enemy_units:
                closest_enemy = min(enemy_units, key=lambda u: u['position'][1])
                enemy_x, enemy_y = closest_enemy['position']
                
                if unit_name == 'minipekka':
                    return (enemy_x, enemy_y + 1)  # Counter direto para tanks
                elif unit_name == 'knight':
                    return (enemy_x, enemy_y + 1)  # Counter para tropas únicas
                elif unit_name in ['archers', 'musketeer']:
                    return (enemy_x - 1, enemy_y + 2)  # Posição segura para counter
                elif unit_name == 'minions':
                    return (enemy_x, enemy_y)  # Counter aéreo
        
        # Fallback baseado no tipo de carta
        if unit_name == 'giant':
            return (7, 5)  # Bridge padrão
        elif unit_name in ['archers', 'musketeer']:
            return (6, 8)  # Posição de suporte
        elif unit_name in ['knight', 'minipekka']:
            return (8, 9)  # Posição defensiva
        elif unit_name == 'spear_goblins':
            return (3, 8)  # Posição segura
        elif unit_name == 'minions':
            return (7, 8)  # Posição aérea
        
        # Fallback final: posição original da ação
        return (action.tile_x, action.tile_y)
    
    def _apply_positioning_precision(self, tile_x, tile_y, unit_name):
        """Aplica precisão de posicionamento com validação de interações"""
        # Garante que as coordenadas estão dentro dos limites
        tile_x = max(0, min(17, tile_x))
        tile_y = max(0, min(17, tile_y))
        
        # === VALIDAÇÃO DE INTERAÇÕES CRÍTICAS ===
        
        # Verificar se posicionamento é seguro contra inimigos próximos
        enemy_units = self._get_enemy_units()
        for enemy in enemy_units:
            enemy_name = enemy.get('name', '')
            enemy_pos = enemy.get('position', (0, 0))
            
            if len(enemy_pos) < 2:
                continue
                
            enemy_x, enemy_y = enemy_pos
            distance = ((tile_x - enemy_x)**2 + (tile_y - enemy_y)**2)**0.5
            
            # REGRA CRÍTICA: Nunca colocar ranged em cima de melee
            if unit_name in ['musketeer', 'archers'] and enemy_name in ['minipekka', 'knight', 'pekka']:
                if distance < 3:  # Muito próximo
                    # Reposicionar para distância segura
                    safe_x = enemy_x + (4 if enemy_x < 9 else -4)  # 4 tiles de distância
                    safe_y = enemy_y + 2  # Mais atrás
                    tile_x, tile_y = safe_x, safe_y
                    logger.warning(f"⚠️ Repositioning {unit_name} away from {enemy_name} - avoiding melee contact")
            
            # REGRA: Minions devem ficar acima de tropas terrestres
            elif unit_name == 'minions' and enemy_name in ['giant', 'knight', 'pekka']:
                if distance < 2:
                    # Posição ligeiramente acima
                    tile_x = enemy_x
                    tile_y = enemy_y - 1
                    logger.info(f"✈️ Positioning {unit_name} above {enemy_name} for air advantage")
        
        # === AJUSTES BASEADOS NO CENTRO DO CAMPO ===
        
        center_x = 8.5
        
        # Se está muito próximo do centro, força para um lado específico
        if abs(tile_x - center_x) < 0.5:
            # Decide o lado baseado na situação
            tower_analysis = self._analyze_tower_situation()
            
            # Se uma torre inimiga foi destruída, prefere o lado aberto
            if tower_analysis['enemy_towers']['left']['destroyed']:
                tile_x = 3  # Lado esquerdo aberto
            elif tower_analysis['enemy_towers']['right']['destroyed']:
                tile_x = 14  # Lado direito aberto
            else:
                # Escolhe lado baseado na pressão
                lane_analysis = self._analyze_lanes(self._get_enemy_units(), self._get_our_units())
                if lane_analysis['left'] == 'clear':
                    tile_x = 7  # Ligeiramente à esquerda
                else:
                    tile_x = 10  # Ligeiramente à direita
        
        # === AJUSTES ESPECÍFICOS POR TIPO DE CARTA ===
        
        if unit_name in ['archers', 'musketeer']:
            # Tropas ranged ficam mais atrás para segurança
            tile_y = max(tile_y, 8)
        elif unit_name in ['giant']:
            # Tank vai mais à frente para liderar
            tile_y = min(tile_y, 6)
        elif unit_name in ['knight', 'minipekka']:
            # Tropas melee ficam no meio-frente
            tile_y = max(tile_y, 9)
        elif unit_name == 'minions':
            # Tropas aéreas podem ficar mais à frente
            tile_y = max(tile_y, 7)
        
        # Validação final - não colocar muito próximo das nossas torres
        if tile_y > 15:
            tile_y = 15
            logger.warning(f"⚠️ Adjusted {unit_name} position - too close to our towers")
        
        # === VALIDAÇÃO FINAL DE MATCHUP ===
        
        # Validar se posicionamento é taticamente correto
        try:
            enemy_units = self._get_enemy_units()
            validation = self.matchup_validator.validate_card_placement(unit_name, (tile_x, tile_y), enemy_units)
            
            if not validation['is_valid']:
                # Posicionamento é taticamente incorreto
                logger.error(f"🚫 INVALID POSITIONING: {unit_name} at ({tile_x}, {tile_y})")
                for warning in validation['warnings']:
                    logger.warning(warning)
                
                # Usar posição sugerida se disponível
                if 'suggested_position' in validation:
                    tile_x, tile_y = validation['suggested_position']
                    logger.info(f"✅ CORRECTED POSITIONING: {unit_name} at ({tile_x}, {tile_y}) - {validation['reasoning']}")
            
            elif validation['warnings']:
                # Posicionamento válido mas com avisos
                for warning in validation['warnings']:
                    logger.warning(warning)
                logger.info(f"⚠️ Positioning {unit_name} with caution: confidence {validation['confidence']:.1%}")
            
            else:
                logger.debug(f"✅ Positioning {unit_name} at validated location ({tile_x}, {tile_y})")
                
        except Exception as e:
            logger.debug(f"Error in matchup validation: {e}")
        
        return (tile_x, tile_y)
    
    def _estimate_enemy_elixir(self):
        """Estima o elixir do inimigo baseado em atividade recente"""
        # Implementação melhorada - considera cartas jogadas recentemente
        base_elixir = 5  # Estimativa base
        
        # Se há unidades inimigas no campo, provavelmente gastou elixir
        enemy_units = self._get_enemy_units()
        if enemy_units:
            recent_cost = sum(self._estimate_card_cost(unit['name']) for unit in enemy_units[-2:])  # Últimas 2 unidades
            estimated_elixir = max(0, 10 - recent_cost)
            return min(10, estimated_elixir + 1)  # +1 por regeneração
        
        return base_elixir
    
    def _estimate_card_cost(self, card_name):
        """Estima o custo de elixir de uma carta"""
        cost_map = {
            'giant': 5, 'knight': 3, 'archers': 3, 'musketeer': 4,
            'minions': 3, 'fireball': 4, 'spear_goblins': 2, 'minipekka': 4,
            'witch': 5, 'baby_dragon': 4, 'zap': 2, 'arrows': 3
        }
        return cost_map.get(card_name, 3)  # Padrão 3
    
    def _get_tower_health(self):
        """Obtém a saúde da torre"""
        if hasattr(self.state, 'ally_towers') and self.state.ally_towers:
            return sum(tower.health for tower in self.state.ally_towers if hasattr(tower, 'health'))
        return 100  # Valor padrão
    
    def _get_game_time(self):
        """Obtém o tempo de jogo"""
        # Implementação básica - pode ser melhorada
        return 0
    
    def _calculate_surviving_troops_elixir(self) -> float:
        """Calcula o valor de elixir das tropas sobreviventes"""
        try:
            our_units = self._get_our_units()
            total_elixir = 0
            
            for unit in our_units:
                unit_name = unit.get('name', 'unknown')
                if unit_name != 'unknown' and unit_name != 'blank':
                    elixir_cost = self._get_card_elixir_cost(unit_name)
                    total_elixir += elixir_cost
            
            return total_elixir
        except Exception as e:
            logger.debug(f"Error calculating surviving troops elixir: {e}")
            return 0  # Valor padrão
    
    def _get_enemy_units(self):
        """Obtém unidades inimigas no campo"""
        enemy_units = []
        if hasattr(self.state, 'enemies') and self.state.enemies:
            for unit in self.state.enemies:
                if hasattr(unit, 'unit') and hasattr(unit.unit, 'name'):
                    enemy_units.append({
                        "name": unit.unit.name,
                        "health": getattr(unit, 'health', 100),
                        "position": (unit.position.tile_x, unit.position.tile_y) if hasattr(unit, 'position') else (0, 0)
                    })
        return enemy_units
    
    def _get_our_units(self):
        """Obtém nossas unidades no campo"""
        our_units = []
        if hasattr(self.state, 'allies') and self.state.allies:
            for unit in self.state.allies:
                if hasattr(unit, 'unit') and hasattr(unit.unit, 'name'):
                    our_units.append({
                        "name": unit.unit.name,
                        "health": getattr(unit, 'health', 100),
                        "position": (unit.position.tile_x, unit.position.tile_y) if hasattr(unit, 'position') else (0, 0)
                    })
        return our_units

    def _analyze_game_situation(self):
        """Analisa a situação atual do jogo com detalhes avançados"""
        situation = {
            'priority': 'neutral',
            'should_defend': False,
            'should_attack': False,
            'should_counter': False,
            'should_cycle': False,
            'elixir_advantage': 0,
            'enemy_pressure': 0,
            'our_pressure': 0,
            'tower_threat': 0,
            'game_state': 'neutral',
            'recommended_spend': 0,
            'lane_analysis': {'left': 'clear', 'right': 'clear'}
        }
        
        # Analisa elixir
        our_elixir = self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0
        enemy_elixir = self._estimate_enemy_elixir()
        situation['elixir_advantage'] = our_elixir - enemy_elixir
        
        # Analisa pressão inimiga
        enemy_units = self._get_enemy_units()
        our_units = self._get_our_units()
        
        # Calcula pressão baseada em unidades no campo
        for unit in enemy_units:
            if unit['position'][1] > 10:  # Lado nosso do campo
                situation['enemy_pressure'] += 1
                if unit['position'][1] > 14:  # Próximo às torres
                    situation['tower_threat'] += 1
        
        for unit in our_units:
            if unit['position'][1] < 5:  # Lado inimigo do campo
                situation['our_pressure'] += 1
        
        # Análise avançada de lanes
        situation['lane_analysis'] = self._analyze_lanes(enemy_units, our_units)
        
        # Determina estado do jogo
        situation['game_state'] = self._determine_game_state(our_elixir, enemy_elixir, 
                                                           situation['enemy_pressure'], 
                                                           situation['our_pressure'])
        
        # Calcula gasto recomendado de elixir
        situation['recommended_spend'] = self._calculate_recommended_spend(our_elixir, 
                                                                         situation['elixir_advantage'],
                                                                         situation['game_state'])
        
        # === ESTADOS AVANÇADOS (reativados gradualmente) ===
        
        # Detecta se acabou de defender com sucesso (com tratamento robusto)
        try:
            recently_defended = self._recently_defended()
            logger.debug(f"Recently defended analysis: {recently_defended}")
        except Exception as e:
            logger.debug(f"Error in _recently_defended: {e}")
            recently_defended = False
        
        # Detecta se tem combo disponível (com tratamento robusto)
        try:
            combo_ready = self._check_combo_availability(our_elixir)
            logger.debug(f"Combo availability: {combo_ready}")
        except Exception as e:
            logger.debug(f"Error in _check_combo_availability: {e}")
            combo_ready = {'giant_combo': False, 'should_wait_for_giant': False, 'air_combo': False, 'spell_combo': False}
        
        # Detecta se inimigo gastou muito elixir (com tratamento robusto)
        try:
            enemy_overcommitted = self._detect_enemy_overcommit(enemy_units, enemy_elixir)
            logger.debug(f"Enemy overcommitted: {enemy_overcommitted}")
        except Exception as e:
            logger.debug(f"Error in _detect_enemy_overcommit: {e}")
            enemy_overcommitted = False
        
        # Determina prioridade com lógica avançada e estados
        if situation['tower_threat'] > 0:
            situation['priority'] = 'emergency_defend'
            situation['should_defend'] = True
        
        elif recently_defended and enemy_overcommitted and our_elixir >= 5:
            situation['priority'] = 'counter_attack_after_defense'
            situation['should_attack'] = True
            logger.info("⚔️ Counter-attack opportunity after successful defense!")
        
        elif combo_ready.get('giant_combo', False) and our_elixir >= 8:
            situation['priority'] = 'giant_combo_attack'
            situation['should_attack'] = True
            situation['combo_type'] = 'giant_push'
            logger.info("🏰 Giant combo ready - preparing big push!")
        
        elif combo_ready.get('should_wait_for_giant', False) and our_elixir >= 6:
            situation['priority'] = 'wait_for_giant_combo'
            situation['should_cycle'] = True
            logger.info("⏳ Waiting to build elixir for Giant combo")
        
        elif situation['enemy_pressure'] > 2 and our_elixir >= 4:
            situation['priority'] = 'defend'
            situation['should_defend'] = True
        
        elif situation['elixir_advantage'] >= 3 and our_elixir >= 6:
            situation['priority'] = 'aggressive_attack'
            situation['should_attack'] = True
        
        elif situation['elixir_advantage'] >= 1 and our_elixir >= 8:
            situation['priority'] = 'pressure_attack'
            situation['should_attack'] = True
        
        elif situation['enemy_pressure'] > 0 and our_elixir >= 3:
            situation['priority'] = 'counter_attack'
            situation['should_counter'] = True
        
        elif our_elixir <= 3 and situation['enemy_pressure'] == 0:
            situation['priority'] = 'cycle'
            situation['should_cycle'] = True
        
        elif our_elixir >= 9:
            situation['priority'] = 'elixir_dump'
            situation['should_attack'] = True
        
        else:
            situation['priority'] = 'neutral'
        
        # Adiciona informações de combo e estado
        situation['recently_defended'] = recently_defended
        situation['enemy_overcommitted'] = enemy_overcommitted
        situation['combo_ready'] = combo_ready
        
        return situation
    
    def _analyze_lanes(self, enemy_units, our_units):
        """Analisa a pressão em cada lane"""
        lanes = {'left': 'clear', 'right': 'clear'}
        
        # Analisa pressão inimiga por lane
        for unit in enemy_units:
            x_pos = unit['position'][0]
            y_pos = unit['position'][1]
            
            if x_pos < 9:  # Lane esquerda
                if y_pos > 10:
                    lanes['left'] = 'under_pressure'
                elif y_pos > 5:
                    lanes['left'] = 'incoming_threat'
            else:  # Lane direita
                if y_pos > 10:
                    lanes['right'] = 'under_pressure'
                elif y_pos > 5:
                    lanes['right'] = 'incoming_threat'
        
        return lanes
    
    def _determine_game_state(self, our_elixir, enemy_elixir, enemy_pressure, our_pressure):
        """Determina o estado geral do jogo"""
        elixir_diff = our_elixir - enemy_elixir
        
        if enemy_pressure > 2:
            return 'defending'
        elif our_pressure > 2:
            return 'attacking'
        elif elixir_diff >= 3:
            return 'elixir_advantage'
        elif elixir_diff <= -2:
            return 'elixir_disadvantage'
        elif our_elixir >= 8:
            return 'elixir_full'
        elif our_elixir <= 2:
            return 'elixir_low'
        else:
            return 'neutral'
    
    def _calculate_recommended_spend(self, our_elixir, elixir_advantage, game_state):
        """Calcula quanto elixir é recomendado gastar"""
        if game_state == 'defending':
            return min(our_elixir, 6)  # Gasta até 6 para defender
        elif game_state == 'attacking':
            return min(our_elixir, 8)  # Gasta quase tudo para atacar
        elif game_state == 'elixir_advantage':
            return min(our_elixir - 2, 6)  # Mantém reserva
        elif game_state == 'elixir_full':
            return our_elixir - 1  # Gasta quase tudo
        elif game_state == 'elixir_low':
            return min(our_elixir, 3)  # Gasta pouco
        else:
            return min(our_elixir, 4)  # Gasto moderado

    def _should_play_card(self, situation_analysis):
        """Decide se deve jogar uma carta baseado em pensamento estratégico e inteligência de combos"""
        try:
            our_elixir = self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0
            ready_cards = self.state.ready if hasattr(self.state, 'ready') else []
            
            # Se não há cartas prontas, não pode jogar
            if not ready_cards:
                return False
            
            # Verifica se há pelo menos uma carta que pode pagar
            can_afford_any = False
            cheapest_cost = float('inf')
            
            for card_index in ready_cards:
                if card_index + 1 < len(self.state.cards):
                    card_cost = self.state.cards[card_index + 1].cost
                    cheapest_cost = min(cheapest_cost, card_cost)
                    if our_elixir >= card_cost:
                        can_afford_any = True
                        break
            
            # Se não pode pagar nenhuma carta, aguarda
            if not can_afford_any:
                logger.debug(f"Cannot afford any card - Elixir: {our_elixir}, Cheapest: {cheapest_cost}")
                return False
            
            # === ANÁLISE DE INTELIGÊNCIA DE COMBOS ===
            
            # Obter cartas disponíveis
            available_cards = []
            for card_index in ready_cards:
                if card_index + 1 < len(self.state.cards):
                    card_name = self.state.cards[card_index + 1].name
                    available_cards.append(card_name)
            
            # Preparar dados do estado do jogo para análise de combos
            game_state = {
                'our_elixir': our_elixir,
                'enemy_elixir': self._estimate_enemy_elixir(),
                'enemy_last_card': self._get_enemy_last_card(),
                'enemy_has_heavy_tank': self._enemy_has_heavy_tank(),
                'situation': situation_analysis
            }
            
            # Analisar oportunidade de combo
            combo_analysis = self.combo_intelligence.analyze_combo_opportunity(game_state, available_cards)
            
            # Log da análise de combos
            logger.info(f"🎯 COMBO ANALYSIS:")
            for reason in combo_analysis.get('reasoning', []):
                logger.info(f"   • {reason}")
            
            # Se deve esperar para combo
            if combo_analysis.get('wait_for_elixir', False):
                logger.info(f"⏳ WAITING FOR COMBO: {combo_analysis.get('recommended_combo', 'unknown')}")
                return False
            
            # Se deve executar combo
            if combo_analysis.get('should_combo', False):
                recommended_combo = combo_analysis.get('recommended_combo')
                immediate_play = combo_analysis.get('immediate_play')
                
                if immediate_play and immediate_play in available_cards:
                    logger.info(f"🔥 EXECUTING COMBO: {recommended_combo} - Playing {immediate_play} first")
                    return True
            
            # === ANÁLISE ESTRATÉGICA DE TURNO ===
            
            # Obter recomendações de estratégia adaptativa
            strategy_recommendations = None
            if self.adaptive_strategy:
                strategy_recommendations = self.adaptive_strategy.get_strategy_recommendations(
                    game_state, available_cards
                )
                logger.debug(f"Strategy recommendations: {strategy_recommendations.get('strategy', 'unknown')} - Push: {strategy_recommendations.get('should_push', False)}, Defend: {strategy_recommendations.get('should_defend', False)}")
            
            # Preparar dados do estado do jogo
            game_state = {
                'our_elixir': our_elixir,
                'situation': situation_analysis,
                'enemy_units': self._get_enemy_units(),
                'our_units': self._get_our_units(),
                'tower_health': self._analyze_tower_situation(),
                'strategy_recommendations': strategy_recommendations
            }
            
            # Analisar cada carta pronta individualmente
            for card_index in ready_cards:
                if card_index + 1 < len(self.state.cards):
                    card_name = self.state.cards[card_index + 1].name
                    card_cost = self.state.cards[card_index + 1].cost
                    
                    # Verificar se tem elixir para esta carta específica
                    if our_elixir < card_cost:
                        continue
                    
                    # Proposta de ação
                    proposed_action = {
                        'type': self._get_action_type(card_name, situation_analysis),
                        'card': card_name,
                        'cost': card_cost,
                        'situation': situation_analysis.get('priority', 'neutral')
                    }
                    
                    # Analisar consequências da ação
                    turn_analysis = self.strategic_thinking.analyze_turn_consequences(proposed_action, game_state)
                    
                    # Log do raciocínio estratégico
                    logger.info(f"🧠 STRATEGIC ANALYSIS for {card_name}:")
                    for reason in turn_analysis.get('reasoning', []):
                        logger.info(f"   • {reason}")
                    
                    # Decisão baseada na recomendação estratégica
                    recommendation = turn_analysis.get('recommendation', 'proceed')
                    
                    if recommendation == 'avoid':
                        logger.warning(f"🚫 STRATEGIC BLOCK: {card_name} - Risk level: {turn_analysis.get('risk_level', 'unknown')}")
                        continue  # Tenta próxima carta
                    elif recommendation == 'consider':
                        logger.info(f"⚠️ STRATEGIC CONSIDERATION: {card_name} - Proceed with caution")
                        return True  # Permite com cuidado
                    else:  # proceed
                        logger.info(f"✅ STRATEGIC APPROVAL: {card_name} - Good tactical decision")
                        return True
            
            # Se chegou aqui, nenhuma carta foi aprovada estrategicamente
            logger.warning("🚫 No cards approved by strategic analysis")
            return False
            
        except Exception as e:
            logger.debug(f"Error in strategic _should_play_card: {e}")
            return False
    
    def _get_action_type(self, card_name, situation_analysis):
        """Determina o tipo de ação baseado na carta e situação"""
        priority = situation_analysis.get('priority', 'neutral')
        
        if priority in ['defend_tower', 'defend']:
            return 'defensive'
        elif priority in ['attack', 'counter']:
            return 'offensive'
        elif card_name in ['fireball', 'zap', 'arrows']:
            return 'spell'
        else:
            return 'neutral'
    
    def _estimate_enemy_elixir(self):
        """Estima o elixir do inimigo baseado em suas jogadas recentes"""
        try:
            # Implementação básica - pode ser expandida
            return 10  # Valor padrão
        except Exception as e:
            logger.debug(f"Error estimating enemy elixir: {e}")
            return 10
    
    def _get_enemy_last_card(self):
        """Obtém a última carta jogada pelo inimigo"""
        try:
            # Implementação básica - pode ser expandida com detecção
            return ""  # Valor padrão
        except Exception as e:
            logger.debug(f"Error getting enemy last card: {e}")
            return ""
    
    def _enemy_has_heavy_tank(self):
        """Verifica se o inimigo tem um tank pesado no campo"""
        try:
            enemy_units = self._get_enemy_units()
            heavy_tanks = ['giant', 'pekka', 'golem', 'royal_giant', 'electro_giant']
            
            for unit in enemy_units:
                if unit.get('name', '') in heavy_tanks:
                    return True
            
            return False
        except Exception as e:
            logger.debug(f"Error checking enemy heavy tank: {e}")
            return False
    
    def _get_enemy_buildings(self):
        """Obtém construções inimigas no campo"""
        try:
            # Implementação básica - pode ser expandida com detecção real
            # Por enquanto, retorna lista vazia
            return []
        except Exception as e:
            logger.debug(f"Error getting enemy buildings: {e}")
            return []

    def _get_card_elixir_cost(self, card_name: str) -> int:
        """Retorna o custo de elixir de uma carta"""
        try:
            elixir_costs = {
                'giant': 5,
                'knight': 3,
                'musketeer': 4,
                'archers': 3,
                'minipekka': 4,
                'minions': 3,
                'spear_goblins': 2,
                'fireball': 4,
                'zap': 2,
                'arrows': 3,
                'wizard': 5,
                'three_musketeers': 9,
                'skeletons': 1,
                'goblins': 2,
                'cannon': 3,
                'tesla': 4,
                'bomb_tower': 5,
                'inferno_tower': 5,
                'hog_rider': 4,
                'balloon': 5,
                'pekka': 7,
                'golem': 8,
                'valkyrie': 4,
                'ice_spirit': 1,
                'poison': 4
            }
            
            return elixir_costs.get(card_name.lower(), 3)
            
        except Exception as e:
            logger.debug(f"Error getting card elixir cost: {e}")
            return 3

    def _is_play_again_screen(self, screen) -> bool:
        """Detecta se está na tela de 'jogar de novo' (crowns/resultado)"""
        try:
            # Verificar se é uma tela de resultado (crowns)
            if hasattr(screen, 'name'):
                screen_name = screen.name.lower()
                # Palavras-chave que indicam tela de resultado
                result_keywords = ['crown', 'victory', 'defeat', 'draw', 'result', 'winner', 'result_screen']
                if any(keyword in screen_name for keyword in result_keywords):
                    logger.debug(f"Detected result screen by name: {screen_name}")
                    return True
            
            # Verificar se tem coordenadas de clique (botão "jogar de novo")
            if hasattr(screen, 'click_xy') and screen.click_xy:
                logger.debug(f"Detected result screen by click coordinates: {screen.click_xy}")
                return True
            
            # Verificar se é uma tela específica de resultado
            if hasattr(screen, 'result'):
                logger.debug(f"Detected result screen by result attribute: {screen.result}")
                return True
            
            # Usar detector avançado se disponível - MAS SER MAIS RIGOROSO
            if hasattr(self, 'advanced_screen_detector') and hasattr(self, 'state'):
                try:
                    # Pegar screenshot atual
                    screenshot = self.emulator.take_screenshot()
                    screen_info = self.advanced_screen_detector.get_screen_info(screenshot)
                    
                    # Exigir múltiplos indicadores para confirmar tela de resultado
                    indicators = []
                    
                    if screen_info.get('is_result_screen', False):
                        indicators.append('result_screen')
                        
                    if screen_info.get('has_crowns', False):
                        indicators.append('crowns')
                        
                    if screen_info.get('has_play_again', False):
                        indicators.append('play_again_button')
                        
                    if screen_info.get('has_post_game_buttons', False):
                        indicators.append('post_game_buttons')
                    
                    # Só retornar True se tiver pelo menos 2 indicadores
                    if len(indicators) >= 2:
                        logger.debug(f"Advanced detector confirmed result screen with indicators: {indicators}")
                        return True
                    else:
                        logger.debug(f"Advanced detector found insufficient indicators: {indicators}")
                        
                except Exception as adv_error:
                    logger.debug(f"Advanced detector error in play again detection: {adv_error}")
            
            return False
            
        except Exception as e:
            logger.debug(f"Error detecting play again screen: {e}")
            return False

    def _is_definitely_in_game(self) -> bool:
        """Verifica se o bot está definitivamente em jogo para evitar falsos positivos"""
        try:
            # Verificar se tem cartas disponíveis (indicador forte de estar em jogo)
            if hasattr(self.state, 'cards') and self.state.cards:
                if len(self.state.cards) > 0:
                    logger.debug("Definitely in game - cards available")
                    return True
            
            # Verificar se tem elixir (indicador forte de estar em jogo)
            if hasattr(self.state, 'numbers') and hasattr(self.state.numbers, 'elixir'):
                if hasattr(self.state.numbers.elixir, 'number'):
                    elixir = self.state.numbers.elixir.number
                    if elixir is not None and elixir >= 0:
                        logger.debug(f"Definitely in game - elixir: {elixir}")
                        return True
            
            # Verificar se tem unidades inimigas (indicador de estar em jogo)
            enemy_units = self._get_enemy_units()
            if enemy_units and len(enemy_units) > 0:
                logger.debug("Definitely in game - enemy units detected")
                return True
            
            # Verificar se tem unidades aliadas (indicador de estar em jogo)
            if hasattr(self.state, 'units') and self.state.units:
                if len(self.state.units) > 0:
                    logger.debug("Definitely in game - friendly units detected")
                    return True
            
            # Verificar se a tela atual é IN_GAME
            if hasattr(self.state, 'screen') and self.state.screen:
                if hasattr(self.state.screen, 'name'):
                    if self.state.screen.name == 'in_game':
                        logger.debug("Definitely in game - screen detected as in_game")
                        return True
            
            # Se chegou até aqui, provavelmente não está em jogo
            logger.debug("Not definitely in game - no strong indicators found")
            return False
            
        except Exception as e:
            logger.debug(f"Error checking if definitely in game: {e}")
            return False

    def _handle_play_again_screen(self):
        """Lida com a tela de 'jogar de novo'"""
        try:
            logger.info("🔄 Processando tela de 'Jogar de Novo'")
            
            # Aguardar um pouco para a tela carregar completamente
            time.sleep(2)
            
            # Tentar clicar no botão "jogar de novo"
            if hasattr(self.state.screen, 'click_xy') and self.state.screen.click_xy:
                logger.info(f"🎯 Clicando no botão 'Jogar de Novo' em {self.state.screen.click_xy}")
                self.emulator.click(*self.state.screen.click_xy)
                self._log_and_wait("Clicked play again button", 3)
            else:
                # Se não tem coordenadas específicas, tentar posições comuns
                logger.info("🎯 Tentando posições comuns do botão 'Jogar de Novo'")
                common_positions = [
                    (640, 600),  # Centro inferior da tela
                    (640, 550),  # Ligeiramente acima
                    (640, 650),  # Ligeiramente abaixo
                    (540, 600),  # Esquerda
                    (740, 600),  # Direita
                ]
                
                for pos in common_positions:
                    try:
                        logger.debug(f"Tentando clicar em {pos}")
                        self.emulator.click(*pos)
                        time.sleep(1)
                        
                        # Verificar se mudou de tela
                        self.set_state()
                        if self.state.screen != self.state.screen:  # Se mudou
                            logger.info(f"✅ Sucesso ao clicar em {pos}")
                            break
                    except Exception as e:
                        logger.debug(f"Falha ao clicar em {pos}: {e}")
                        continue
            
            # Aguardar transição para lobby
            logger.info("⏳ Aguardando transição para lobby...")
            time.sleep(3)
            
            # Verificar se chegou no lobby
            self.set_state()
            if hasattr(self.state.screen, 'name') and 'lobby' in self.state.screen.name.lower():
                logger.info("✅ Chegou no lobby, pronto para próxima partida!")
                # Resetar flags para nova partida
                self.end_of_game_clicked = False
                self.game_start_time = None
            else:
                logger.warning("⚠️ Não conseguiu chegar no lobby, tentando novamente...")
                # Tentar novamente após um delay
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"Error handling play again screen: {e}")
            import traceback
            logger.error(f"Play again screen traceback: {traceback.format_exc()}")

    def _filter_actions_by_situation(self, actions, situation_analysis):
        """Filtra ações baseado na situação atual com lógica avançada e adaptação"""
        filtered_actions = []
        our_elixir = self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0
        enemy_units = self._get_enemy_units()
        
        # Criar contexto para adaptação de papéis (com tratamento de erro)
        try:
            context = {
                'emergency': situation_analysis['priority'] == 'emergency_defend',
                'air_threat': any(unit['name'] in ['baby_dragon', 'minions', 'balloon'] for unit in enemy_units),
                'counter_push': situation_analysis['priority'] == 'counter_attack_after_defense',
                'support_tank': situation_analysis.get('combo_type') == 'giant_push'
            }
        except Exception as e:
            logger.debug(f"Error creating context: {e}")
            context = {'emergency': False, 'air_threat': False, 'counter_push': False, 'support_tank': False}
        
        for action in actions:
            card_name = self.state.cards[action.index + 1].name if hasattr(self.state, 'cards') and len(self.state.cards) > action.index + 1 else "unknown"
            card_cost = self._estimate_card_cost(card_name)
            
            # === FILTROS ESPECIAIS PARA ESTADOS AVANÇADOS ===
            
            # PRIORIDADE MÁXIMA: Ameaças táticas específicas (Giant atrás da torre, etc.)
            tactical_threat = situation_analysis.get('tactical_threat', {})
            if tactical_threat.get('threat_level', 0) >= 8:
                threat_type = tactical_threat.get('threat_type', 'unknown')
                recommended_response = tactical_threat.get('recommended_response', 'prepare_defense')
                
                logger.warning(f"🚨 TACTICAL THREAT: {threat_type} - Response: {recommended_response}")
                
                # Decisões específicas baseadas na ameaça
                if threat_type == 'giant_behind_king':
                    if recommended_response == 'quick_opposite_attack' and self._is_offensive_card(card_name, context):
                        filtered_actions.append(action)
                        logger.info(f"💨 Quick opposite attack: {card_name}")
                        continue
                    elif recommended_response in ['prepare_defense', 'prepare_solid_defense'] and self._is_defensive_card(card_name, context):
                        filtered_actions.append(action)
                        logger.info(f"🛡️ Preparing defense: {card_name}")
                        continue
                    elif recommended_response == 'cycle_and_defend' and (self._is_cycle_card(card_name) or card_cost <= 2):
                        filtered_actions.append(action)
                        logger.info(f"🔄 Cycling for defense: {card_name}")
                        continue
            
            # PRIORIDADE ALTA: Ameaças imediatas
            immediate_threats = situation_analysis.get('immediate_threats', {})
            if immediate_threats.get('requires_immediate_action', False):
                # Se há ameaça crítica, só aceita cartas que podem defender
                if len(immediate_threats.get('critical_threats', [])) > 0:
                    if self._is_defensive_card(card_name, context) or self._is_counter_card(card_name):
                        filtered_actions.append(action)
                        logger.info(f"Emergency response: {card_name} to critical threat")
                    continue
            
            # PRIORIDADE ALTA: Oportunidades de counter-push coordenado
            counter_push = situation_analysis.get('counter_push', {})
            if counter_push.get('has_opportunity', False):
                push_type = counter_push.get('push_type', 'unknown')
                recommended_cards = counter_push.get('recommended_cards', [])
                
                if card_name in recommended_cards:
                    filtered_actions.append(action)
                    logger.info(f"🤝 Coordinated counter-push: {card_name} for {push_type}")
                    continue
            
            # Verificação de concentração de lane
            lane_concentration = situation_analysis.get('lane_concentration', {})
            if lane_concentration.get('should_focus_defense', False):
                main_lane = lane_concentration.get('main_pressure_lane', 'none')
                
                # Se há concentração em uma lane, só joga cartas nessa lane
                if main_lane in ['left_lane', 'right_lane']:
                    lane_x_range = (0, 6) if main_lane == 'left_lane' else (11, 17)
                    if not (lane_x_range[0] <= action.tile_x <= lane_x_range[1]):
                        continue  # Pula carta se não está na lane correta
            
            # Estado: Preparação para Giant Combo
            if situation_analysis['priority'] == 'wait_for_giant_combo':
                if self._is_cycle_card(card_name) or card_cost <= 2:
                    filtered_actions.append(action)
                continue
            
            # Estado: Execução de Giant Combo (com timing correto)
            elif situation_analysis['priority'] == 'giant_combo_attack':
                if card_name == 'giant':
                    # Giant sempre pode ser jogado primeiro
                    filtered_actions.append(action)
                    logger.info(f"🏰 Playing Giant for combo - tank leads the push")
                elif card_name in ['musketeer', 'archers', 'minions'] and our_elixir >= 8:
                    # Verificar se há Giant no campo para suportar
                    our_units = self._get_our_units()
                    giant_on_field = any(unit.get('name') == 'giant' for unit in our_units)
                    
                    if giant_on_field:
                        # Verificar timing do suporte
                        giant_unit = next((unit for unit in our_units if unit.get('name') == 'giant'), None)
                        if giant_unit:
                            timing_check = self.combo_timing.should_wait_for_tank('giant', card_name, giant_unit['position'])
                            
                            if not timing_check['should_wait']:
                                filtered_actions.append(action)
                                logger.info(f"🤝 Adding {card_name} support to Giant combo")
                            else:
                                logger.info(f"⏰ {card_name} waiting for Giant to advance ({timing_check['wait_time']:.1f}s)")
                    else:
                        # Sem Giant no campo, aguardar
                        logger.debug(f"No Giant on field for {card_name} support")
                continue
            
            # Estado: Counter-ataque após defesa
            elif situation_analysis['priority'] == 'counter_attack_after_defense':
                # Prioriza cartas que podem fazer counter-push
                if self._is_offensive_card(card_name, context) or self._is_counter_card(card_name):
                    filtered_actions.append(action)
                continue
            
            # === FILTROS ADAPTATIVOS NORMAIS ===
            
            # Filtro por custo de elixir
            if card_cost > situation_analysis.get('recommended_spend', 4):
                continue
            
            # Se deve ciclar, prioriza cartas baratas
            if situation_analysis['should_cycle']:
                if self._is_cycle_card(card_name) or card_cost <= 2:
                    filtered_actions.append(action)
            
            # Se está defendendo, usa adaptação de papel
            elif situation_analysis['should_defend']:
                # Encontra ameaça específica para counter adaptativo (com tratamento de erro)
                try:
                    main_threat = self._identify_main_threat(enemy_units)
                except Exception as e:
                    logger.debug(f"Error identifying main threat: {e}")
                    main_threat = None
                
                try:
                    is_defensive = self._is_defensive_card(card_name, context)
                    is_counter = self._is_counter_card(card_name, main_threat)
                    
                    if is_defensive or is_counter:
                        filtered_actions.append(action)
                    elif situation_analysis['priority'] == 'emergency_defend':
                        filtered_actions.append(action)  # Em emergência, aceita qualquer carta
                except Exception as e:
                    logger.debug(f"Error in defensive card check: {e}")
                    filtered_actions.append(action)  # Fallback: aceita a carta
            
            # Se está atacando, usa adaptação de papel
            elif situation_analysis['should_attack']:
                try:
                    if self._is_offensive_card(card_name, context):
                        filtered_actions.append(action)
                    elif situation_analysis['priority'] == 'elixir_dump':
                        filtered_actions.append(action)
                except Exception as e:
                    logger.debug(f"Error in offensive card check: {e}")
                    filtered_actions.append(action)  # Fallback: aceita a carta
            
            # Se está fazendo counter, usa counter específico
            elif situation_analysis['should_counter']:
                try:
                    main_threat = self._identify_main_threat(enemy_units)
                    if self._is_counter_card(card_name, main_threat):
                        filtered_actions.append(action)
                except Exception as e:
                    logger.debug(f"Error in counter card check: {e}")
                    filtered_actions.append(action)  # Fallback: aceita a carta
            
            # Situação neutra, aceita todas as cartas (com filtro de custo)
            else:
                if card_cost <= min(our_elixir, 5):
                    filtered_actions.append(action)
        
        # Se não encontrou nenhuma ação adequada, retorna as originais (para não travar)
        return filtered_actions if filtered_actions else actions
    
    def _identify_main_threat(self, enemy_units):
        """Identifica a principal ameaça inimiga"""
        if not enemy_units:
            return None
        
        # Prioriza ameaças por proximidade e tipo
        threats_priority = {
            'giant': 10, 'pekka': 10, 'golem': 10,
            'balloon': 9, 'hog_rider': 8,
            'musketeer': 6, 'wizard': 6, 'witch': 6,
            'knight': 5, 'archers': 4,
            'minions': 3, 'skeleton_army': 3
        }
        
        # Encontra a ameaça de maior prioridade mais próxima
        main_threat = None
        highest_priority = 0
        
        for unit in enemy_units:
            unit_priority = threats_priority.get(unit['name'], 1)
            # Bônus por proximidade (quanto mais próximo, maior prioridade)
            proximity_bonus = max(0, 15 - unit['position'][1]) / 15 * 5
            total_priority = unit_priority + proximity_bonus
            
            if total_priority > highest_priority:
                highest_priority = total_priority
                main_threat = unit['name']
        
        return main_threat
    
    def _detect_immediate_threats(self, enemy_units: List[Dict]) -> Dict:
        """Detecta ameaças imediatas que precisam de resposta urgente"""
        threats = {
            'critical_threats': [],      # Ameaças críticas (próximas da torre)
            'advancing_threats': [],     # Ameaças avançando
            'support_threats': [],       # Tropas de suporte perigosas
            'total_threat_level': 0,
            'requires_immediate_action': False
        }
        
        try:
            for unit in enemy_units:
                unit_name = unit.get('name', 'unknown')
                unit_pos = unit.get('position', (0, 0))
                
                if len(unit_pos) < 2:
                    continue
                
                unit_x, unit_y = unit_pos
                threat_level = 0
                
                # Ameaças críticas (muito próximas das torres)
                if unit_y > 14:
                    threats['critical_threats'].append(unit)
                    threat_level += 10
                    threats['requires_immediate_action'] = True
                
                # Ameaças avançando (no nosso lado do campo)
                elif unit_y > 10:
                    threats['advancing_threats'].append(unit)
                    threat_level += 5
                
                # Tropas de suporte perigosas
                elif unit_name in ['musketeer', 'wizard', 'witch', 'archers'] and unit_y > 8:
                    threats['support_threats'].append(unit)
                    threat_level += 3
                
                threats['total_threat_level'] += threat_level
            
            # Determina se requer ação imediata
            if threats['total_threat_level'] > 15 or len(threats['critical_threats']) > 0:
                threats['requires_immediate_action'] = True
                
        except Exception as e:
            logger.debug(f"Error detecting immediate threats: {e}")
        
        return threats
    
    def _analyze_lane_concentration(self, enemy_units: List[Dict]) -> Dict:
        """Analisa concentração de tropas por lane"""
        concentration = {
            'left_lane': {'count': 0, 'threat_level': 0, 'units': []},
            'right_lane': {'count': 0, 'threat_level': 0, 'units': []},
            'center': {'count': 0, 'threat_level': 0, 'units': []},
            'main_pressure_lane': 'none',
            'should_focus_defense': False
        }
        
        try:
            for unit in enemy_units:
                unit_pos = unit.get('position', (0, 0))
                if len(unit_pos) < 2:
                    continue
                    
                unit_x, unit_y = unit_pos
                unit_name = unit.get('name', 'unknown')
                
                # Calcula ameaça da unidade
                threat_value = self.attention_system._calculate_threat_level(unit_name, unit_y)
                
                # Classifica por lane
                if unit_x < 6:  # Lane esquerda
                    concentration['left_lane']['count'] += 1
                    concentration['left_lane']['threat_level'] += threat_value
                    concentration['left_lane']['units'].append(unit)
                elif unit_x > 11:  # Lane direita
                    concentration['right_lane']['count'] += 1
                    concentration['right_lane']['threat_level'] += threat_value
                    concentration['right_lane']['units'].append(unit)
                else:  # Centro
                    concentration['center']['count'] += 1
                    concentration['center']['threat_level'] += threat_value
                    concentration['center']['units'].append(unit)
            
            # Determina lane de maior pressão
            max_threat = 0
            for lane_name, lane_data in concentration.items():
                if isinstance(lane_data, dict) and lane_data.get('threat_level', 0) > max_threat:
                    max_threat = lane_data['threat_level']
                    concentration['main_pressure_lane'] = lane_name
            
            # Determina se deve focar defesa em uma lane específica
            if max_threat > 10 and concentration[concentration['main_pressure_lane']]['count'] >= 2:
                concentration['should_focus_defense'] = True
                logger.info(f"High concentration detected in {concentration['main_pressure_lane']} - focusing defense")
                
        except Exception as e:
            logger.debug(f"Error analyzing lane concentration: {e}")
        
        return concentration

    def _is_defensive_card(self, card_name, context=None):
        """Verifica se uma carta é defensiva (com adaptação de papel)"""
        # Cartas tradicionalmente defensivas
        always_defensive = ['spear_goblins']
        if card_name in always_defensive:
            return True
        
        # Cartas que podem ser defensivas dependendo do contexto
        context_defensive = {
            'knight': True,  # Sempre pode defender
            'archers': True,  # Sempre pode defender
            'musketeer': True,  # Sempre pode defender
            'minipekka': True,  # Sempre pode defender
            'minions': False,  # Geralmente ofensiva, mas pode defender ar
            'giant': False,  # Raramente defensivo
            'fireball': False  # Spell não é defensiva
        }
        
        if context and card_name in context_defensive:
            # Adaptação baseada no contexto
            if context.get('emergency') and card_name == 'minions':
                return True  # Minions pode defender em emergência
            if context.get('air_threat') and card_name in ['archers', 'musketeer', 'minions']:
                return True  # Anti-aéreo
        
        return context_defensive.get(card_name, False)

    def _is_offensive_card(self, card_name, context=None):
        """Verifica se uma carta é ofensiva (com adaptação de papel)"""
        # Cartas tradicionalmente ofensivas
        always_offensive = ['giant']
        if card_name in always_offensive:
            return True
        
        # Cartas que podem ser ofensivas dependendo do contexto
        context_offensive = {
            'minions': True,  # Geralmente ofensiva
            'archers': False,  # Geralmente defensiva, mas pode atacar
            'musketeer': False,  # Geralmente defensiva, mas pode atacar
            'knight': False,  # Pode ser ofensivo em counter-push
            'minipekka': False,  # Pode ser ofensivo em counter-push
            'fireball': True,  # Spell ofensiva
            'spear_goblins': False  # Geralmente defensiva
        }
        
        if context and card_name in context_offensive:
            # Adaptação baseada no contexto
            if context.get('counter_push') and card_name in ['knight', 'minipekka']:
                return True  # Counter-push após defesa
            if context.get('support_tank') and card_name in ['archers', 'musketeer']:
                return True  # Suporte em push
        
        return context_offensive.get(card_name, False)

    def _is_counter_card(self, card_name, enemy_threat=None):
        """Verifica se uma carta é boa para counter (adaptativo)"""
        if not enemy_threat:
            # Lista padrão sem contexto específico
            counter_cards = ['fireball', 'knight', 'minipekka', 'archers', 'musketeer']
            return card_name in counter_cards
        
        # Counter específico baseado na ameaça
        specific_counters = {
            'giant': ['minipekka', 'knight'],
            'pekka': ['minipekka', 'knight'],
            'musketeer': ['fireball', 'knight'],
            'wizard': ['fireball', 'knight'],
            'baby_dragon': ['archers', 'musketeer'],
            'minions': ['archers', 'musketeer', 'fireball'],
            'skeleton_army': ['fireball'],
            'barbarians': ['fireball']
        }
        
        return card_name in specific_counters.get(enemy_threat, [])

    def _is_cycle_card(self, card_name):
        """Verifica se uma carta é boa para ciclar"""
        # IMPORTANTE: Fireball NUNCA é carta de cycle!
        cycle_cards = ['spear_goblins']  # Apenas a carta mais barata
        
        # Cartas que NUNCA devem ser usadas para cycle
        never_cycle = ['fireball', 'giant', 'minipekka', 'musketeer']
        
        if card_name in never_cycle:
            return False
            
        return card_name in cycle_cards
    
    def _can_counter(self, our_card, enemy_card):
        """Verifica se nossa carta pode counter a carta inimiga (baseado em táticas profissionais)"""
        # Matriz de counters baseada em conhecimento profissional
        counter_matrix = {
            'minipekka': {
                'strong_against': ['giant', 'pekka', 'golem', 'royal_giant', 'electro_giant'],
                'weak_against': ['skeleton_army', 'barbarians', 'minion_horde', 'swarm'],
                'positioning_required': 'direct_on_tank_path'
            },
            'knight': {
                'strong_against': ['musketeer', 'archers', 'wizard', 'witch'],
                'weak_against': ['minipekka', 'pekka', 'swarm_units'],
                'positioning_required': 'close_combat'
            },
            'archers': {
                'strong_against': ['baby_dragon', 'minions', 'bats'],
                'weak_against': ['fireball', 'arrows', 'knight_in_melee'],
                'positioning_required': 'safe_distance_3plus_tiles'
            },
            'musketeer': {
                'strong_against': ['baby_dragon', 'minions', 'balloon', 'air_units'],
                'weak_against': ['fireball', 'lightning', 'minipekka_in_melee'],
                'positioning_required': 'safe_distance_3plus_tiles'
            },
            'minions': {
                'strong_against': ['musketeer', 'wizard', 'ground_only_troops'],
                'weak_against': ['archers', 'baby_dragon', 'arrows', 'fireball'],
                'positioning_required': 'above_enemy_troops'
            },
            'fireball': {
                'strong_against': ['grouped_troops_4plus_elixir', 'barbarians', 'witch', 'musketeer'],
                'weak_against': ['single_targets', 'tanks'],
                'positioning_required': 'center_of_group'
            },
            'spear_goblins': {
                'strong_against': ['none_really'],  # Principalmente para cycle
                'weak_against': ['everything'],
                'positioning_required': 'safe_distance_or_distraction'
            },
            'giant': {
                'strong_against': ['none'],  # Giant é tank, não counter
                'weak_against': ['minipekka', 'pekka', 'inferno'],
                'positioning_required': 'front_line_tank'
            }
        }
        
        # Verificar se pode counter
        our_card_data = counter_matrix.get(our_card, {})
        strong_against = our_card_data.get('strong_against', [])
        
        # Verificação especial para grupos
        if 'grouped_troops_4plus_elixir' in strong_against:
            # Fireball só vale contra grupos valiosos
            return enemy_card in ['musketeer', 'wizard', 'witch', 'barbarians']
        
        return enemy_card in strong_against
    
    def _recently_defended(self):
        """Detecta se acabamos de defender com sucesso"""
        try:
            # Verifica se há nossas unidades que acabaram de counter inimigos
            our_units = self._get_our_units()
            enemy_units = self._get_enemy_units()
            
            if not our_units or not isinstance(our_units, list):
                return False
            
            # Se temos unidades defensivas no campo e poucos inimigos, provavelmente defendemos
            defensive_units = [u for u in our_units if u.get('name') in ['knight', 'minipekka', 'archers', 'musketeer']]
            
            if len(defensive_units) > 0 and len(enemy_units) <= 1:
                # Verifica se unidades defensivas estão no nosso lado (defendendo)
                for unit in defensive_units:
                    if unit.get('position') and len(unit['position']) >= 2 and unit['position'][1] > 8:
                        return True
            
            return False
        except Exception as e:
            logger.debug(f"Error in _recently_defended: {e}")
            return False
    
    def _check_combo_availability(self, our_elixir):
        """Verifica se combos estão disponíveis"""
        combo_status = {
            'giant_combo': False,
            'should_wait_for_giant': False,
            'air_combo': False,
            'spell_combo': False
        }
        
        try:
            # Obter próximas cartas do nosso deck
            deck_analysis = self.deck_memory.get_deck_analysis()
            our_next_cards = deck_analysis.get('our_deck', {}).get('next_cards', [])
            
            if not our_next_cards or not isinstance(our_next_cards, list):
                return combo_status
            
            # Combo Giant + Suporte
            if 'giant' in our_next_cards[:2]:  # Giant nas próximas 2 cartas
                support_cards = ['musketeer', 'archers', 'minions']
                has_support = any(card in our_next_cards[:4] for card in support_cards)
                
                if has_support and our_elixir >= 8:
                    combo_status['giant_combo'] = True
                elif has_support and our_elixir >= 5:
                    combo_status['should_wait_for_giant'] = True
            
            # Combo Aéreo
            if 'minions' in our_next_cards[:2] and our_elixir >= 6:
                combo_status['air_combo'] = True
            
            # Combo de Spell
            if 'fireball' in our_next_cards[:2] and our_elixir >= 4:
                combo_status['spell_combo'] = True
                
        except Exception as e:
            logger.debug(f"Error checking combo availability: {e}")
        
        return combo_status
    
    def _detect_enemy_overcommit(self, enemy_units, enemy_elixir):
        """Detecta se inimigo gastou muito elixir"""
        try:
            if not enemy_units or not isinstance(enemy_units, list):
                return False
            
            # Calcula elixir gasto pelo inimigo baseado em unidades no campo
            enemy_elixir_spent = 0
            for unit in enemy_units:
                if unit.get('name'):
                    enemy_elixir_spent += self._estimate_card_cost(unit['name'])
            
            # Se gastou mais de 6 elixir e tem poucas unidades restantes
            if enemy_elixir_spent >= 6 and enemy_elixir <= 3:
                return True
            
            # Se tem muitas unidades caras no campo
            expensive_units = [u for u in enemy_units if u.get('name') and self._estimate_card_cost(u['name']) >= 4]
            if len(expensive_units) >= 2:
                return True
            
            return False
        except Exception as e:
            logger.debug(f"Error detecting enemy overcommit: {e}")
            return False
    
    def _calculate_strategic_position(self, unit_name: str, enemy_formation: Dict, 
                                    our_formation: Dict, situation_analysis: Dict) -> Optional[Tuple[int, int]]:
        """Calcula posicionamento estratégico baseado nas formações"""
        try:
            enemy_units = self._get_enemy_units()
            
            # Se não há inimigos, usa posicionamento padrão
            if not enemy_units:
                return None
            
            # === ANÁLISE ESPECÍFICA POR SITUAÇÃO ===
            
            # Contra formação Tank + Support (ex: Giant + Archers)
            if enemy_formation['formation_type'] == 'tank_push':
                return self._counter_tank_push_formation(unit_name, enemy_formation, situation_analysis)
            
            # Contra tropas isoladas
            elif enemy_formation['formation_type'] == 'scattered':
                return self._counter_scattered_formation(unit_name, enemy_units, situation_analysis)
            
            # Contra apenas tank
            elif enemy_formation['formation_type'] == 'tank_only':
                return self._counter_tank_only_formation(unit_name, enemy_formation, situation_analysis)
            
            # Contra apenas suporte
            elif enemy_formation['formation_type'] == 'support_only':
                return self._counter_support_only_formation(unit_name, enemy_formation, situation_analysis)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error calculating strategic position: {e}")
            return None
    
    def _counter_tank_push_formation(self, unit_name: str, enemy_formation: Dict, situation_analysis: Dict) -> Optional[Tuple[int, int]]:
        """Posicionamento contra formação Tank + Support"""
        try:
            front_line = enemy_formation.get('front_line', [])
            back_line = enemy_formation.get('back_line', [])
            
            if not front_line or not back_line:
                return None
            
            # Identifica tank e suporte
            tank_unit = front_line[0]  # Primeiro da linha de frente
            support_units = back_line
            
            tank_x, tank_y = tank_unit['position']
            
            # Estratégias específicas por carta
            if unit_name == 'minipekka':
                # Mini Pekka vai direto para o tank, ignorando suporte
                return self._apply_positioning_precision(tank_x, tank_y + 1, unit_name)
            
            elif unit_name == 'knight':
                # Knight tankar o tank, posicionado para interceptar
                return self._apply_positioning_precision(tank_x, tank_y + 2, unit_name)
            
            elif unit_name in ['archers', 'musketeer']:
                # Tropas de longo alcance ficam em diagonal para focar suporte
                support_unit = support_units[0] if support_units else tank_unit
                support_x, support_y = support_unit['position']
                
                # Posição diagonal para focar suporte sem entrar no range do tank
                diagonal_x = support_x + (-2 if support_x > 9 else 2)  # Lado oposto
                diagonal_y = support_y + 3  # Mais atrás para segurança
                
                return self._apply_positioning_precision(diagonal_x, diagonal_y, unit_name)
            
            elif unit_name == 'minions':
                # Minions ataca suporte por cima do tank
                if support_units:
                    support_unit = support_units[0]
                    support_x, support_y = support_unit['position']
                    return self._apply_positioning_precision(support_x, support_y + 1, unit_name)
            
            elif unit_name == 'fireball':
                # Fireball tenta atingir tank + suporte se estão próximos
                if len(support_units) > 0:
                    # Calcula centro entre tank e suporte
                    support_x, support_y = support_units[0]['position']
                    center_x = (tank_x + support_x) / 2
                    center_y = (tank_y + support_y) / 2
                    return (int(center_x), int(center_y))
            
            return None
        except Exception as e:
            logger.debug(f"Error in _counter_tank_push_formation: {e}")
            return None
    
    def _counter_scattered_formation(self, unit_name: str, enemy_units: List[Dict], situation_analysis: Dict) -> Optional[Tuple[int, int]]:
        """Posicionamento contra tropas espalhadas"""
        try:
            if not enemy_units:
                return None
            
            # Encontra a tropa mais ameaçadora (mais próxima + maior prioridade)
            main_threat = None
            highest_threat = 0
            
            for unit in enemy_units:
                threat_level = self.attention_system._calculate_threat_level(unit['name'], unit['position'][1])
                if threat_level > highest_threat:
                    highest_threat = threat_level
                    main_threat = unit
            
            if main_threat:
                threat_x, threat_y = main_threat['position']
                
                # Posicionamento específico contra ameaça principal
                if unit_name in ['knight', 'minipekka']:
                    # Vai direto para a ameaça
                    return self._apply_positioning_precision(threat_x, threat_y + 1, unit_name)
                
                elif unit_name in ['archers', 'musketeer']:
                    # Fica em posição segura para atacar
                    safe_x = threat_x + (-2 if threat_x > 9 else 2)
                    safe_y = threat_y + 2
                    return self._apply_positioning_precision(safe_x, safe_y, unit_name)
            
            return None
        except Exception as e:
            logger.debug(f"Error in _counter_scattered_formation: {e}")
            return None
    
    def _counter_tank_only_formation(self, unit_name: str, enemy_formation: Dict, situation_analysis: Dict) -> Optional[Tuple[int, int]]:
        """Posicionamento contra apenas tank"""
        try:
            front_line = enemy_formation.get('front_line', [])
            if not front_line:
                return None
            
            tank_unit = front_line[0]
            tank_x, tank_y = tank_unit['position']
            
            # Counter direto para tanks isolados
            if unit_name in ['minipekka', 'knight']:
                return self._apply_positioning_precision(tank_x, tank_y + 1, unit_name)
            
            elif unit_name in ['archers', 'musketeer']:
                # Suporte para ajudar no counter
                return self._apply_positioning_precision(tank_x - 1, tank_y + 2, unit_name)
            
            return None
        except Exception as e:
            logger.debug(f"Error in _counter_tank_only_formation: {e}")
            return None
    
    def _counter_support_only_formation(self, unit_name: str, enemy_formation: Dict, situation_analysis: Dict) -> Optional[Tuple[int, int]]:
        """Posicionamento contra apenas tropas de suporte"""
        try:
            back_line = enemy_formation.get('back_line', [])
            if not back_line:
                return None
            
            # Prioriza eliminar suporte rapidamente
            if unit_name == 'fireball':
                # Fireball no centro do grupo de suporte
                center_x = sum(u['position'][0] for u in back_line) / len(back_line)
                center_y = sum(u['position'][1] for u in back_line) / len(back_line)
                return (int(center_x), int(center_y))
            
            elif unit_name in ['knight', 'minipekka']:
                # Vai para a tropa de suporte mais próxima
                closest_support = min(back_line, key=lambda u: u['position'][1])
                support_x, support_y = closest_support['position']
                return self._apply_positioning_precision(support_x, support_y + 1, unit_name)
            
            return None
        except Exception as e:
            logger.debug(f"Error in _counter_support_only_formation: {e}")
            return None

    def _calculate_situation_bonus(self, action, situation_analysis):
        """Calcula bônus baseado na situação atual"""
        card_name = self.state.cards[action.index + 1].name if hasattr(self.state, 'cards') and len(self.state.cards) > action.index + 1 else "unknown"
        bonus = 0
        
        # Bônus para cartas apropriadas à situação
        if situation_analysis['should_defend'] and self._is_defensive_card(card_name):
            bonus += 0.3
        elif situation_analysis['should_attack'] and self._is_offensive_card(card_name):
            bonus += 0.3
        elif situation_analysis['should_counter'] and self._is_counter_card(card_name):
            bonus += 0.3
        
        # Penalidade para cartas inadequadas
        if situation_analysis['should_defend'] and self._is_offensive_card(card_name):
            bonus -= 0.2
        elif situation_analysis['should_attack'] and self._is_defensive_card(card_name):
            bonus -= 0.2
        
        return bonus

    def _handle_play_pause_in_step(self):
        if not pause_event.is_set():
            if not Bot.is_paused_logged:
                logger.info("Bot paused.")
                Bot.is_paused_logged = True
            time.sleep(0.1)
            return
        if not Bot.is_resumed_logged:
            logger.info("Bot resumed.")
            Bot.is_resumed_logged = True

    def step(self):
        try:
            logger.debug("Step starting - handling play/pause")
            self._handle_play_pause_in_step()
            
            logger.debug("Getting old screen state")
            old_screen = self.state.screen if self.state else None
            
            logger.debug("Setting new state")
            self.set_state()
            
            logger.debug("Getting new screen state")
            new_screen = self.state.screen if self.state else None
            
            if new_screen and new_screen != old_screen:
                logger.info(f"New screen state: {new_screen}")
            elif not new_screen:
                logger.warning("No screen detected, skipping step")
                time.sleep(1)
                return
                
            logger.debug(f"Screen state obtained: {new_screen}")
        except Exception as e:
            logger.error(f"CRITICAL ERROR in bot step: {e}")
            import traceback
            logger.error(f"Step traceback: {traceback.format_exc()}")
            # Não retorna, continua tentando
            time.sleep(1)
            return

        if new_screen == Screens.UNKNOWN:
            # Tenta novamente após um breve delay
            logger.warning("Unknown screen detected, retrying...")
            time.sleep(1)
            self.set_state()
            new_screen = self.state.screen if self.state else Screens.UNKNOWN
            
            if new_screen == Screens.UNKNOWN:
                logger.warning("Still unknown screen, waiting...")
                self._log_and_wait("Unknown screen", 2)
                return
            else:
                logger.info(f"Screen detected after retry: {new_screen}")

        if new_screen == Screens.END_OF_GAME:
            logger.info(f"🎯 End of game detected - Screen: {new_screen}")
            logger.info(f"   • Screen name: {new_screen.name}")
            logger.info(f"   • Click coordinates: {new_screen.click_xy}")
            logger.info(f"   • Detection region: {new_screen.ltrb}")
            
            # Debug: verificar se é detecção avançada
            if hasattr(self, 'advanced_screen_detector'):
                try:
                    screenshot = self.emulator.take_screenshot()
                    screen_info = self.advanced_screen_detector.get_screen_info(screenshot)
                    logger.info(f"   • Advanced detector info: {screen_info}")
                except Exception as e:
                    logger.debug(f"Could not get advanced detector info: {e}")
            if not self.end_of_game_clicked:
                # Determina o resultado do jogo
                result = "unknown"
                if hasattr(self.state.screen, 'result'):
                    result = self.state.screen.result
                elif hasattr(self.state, 'game_result'):
                    result = self.state.game_result
                
                # Incrementa contador de partidas
                self.games_played += 1
                logger.info(f"🎮 Partida #{self.games_played} finalizada - Resultado: {result}")
                
                # Finaliza o jogo para ML
                if self.enable_ml:
                    self.end_game(result)
                    if self.deck_analyzer:
                        self.deck_analyzer.end_game(result)
                
                try:
                    click_coords = self.state.screen.click_xy
                    logger.info(f"🎯 Tentando clicar no END_OF_GAME em: {click_coords}")
                    self.emulator.click(*click_coords)
                    self.end_of_game_clicked = True
                    self.end_of_game_click_time = time.time()
                    self._log_and_wait("Clicked END_OF_GAME screen", 2)
                    logger.info("✅ Clique no END_OF_GAME realizado com sucesso!")
                except Exception as e:
                    logger.error(f"Error clicking END_OF_GAME: {e}")
                    # Tentar posições alternativas se a primeira falhar
                    logger.info("🔄 Tentando posições alternativas para END_OF_GAME...")
                    alternative_positions = [
                        (250, 1140),  # Posição original
                        (360, 650),   # Posição central
                        (250, 1100),  # Ligeiramente acima
                        (250, 1180),  # Ligeiramente abaixo
                        (200, 1140),  # Ligeiramente à esquerda
                        (300, 1140),  # Ligeiramente à direita
                    ]
                    
                    for alt_pos in alternative_positions:
                        try:
                            logger.info(f"🔄 Tentando posição alternativa: {alt_pos}")
                            self.emulator.click(*alt_pos)
                            self.end_of_game_clicked = True
                            self.end_of_game_click_time = time.time()
                            self._log_and_wait(f"Clicked END_OF_GAME at alternative position {alt_pos}", 2)
                            logger.info(f"✅ Clique alternativo realizado com sucesso em {alt_pos}!")
                            break
                        except Exception as alt_e:
                            logger.debug(f"Failed alternative position {alt_pos}: {alt_e}")
                            continue
            else:
                logger.info("🔄 END_OF_GAME já foi clicado, aguardando transição...")
                
                # Se já clicou mas ainda está na tela de fim de jogo, aguardar um pouco mais
                self._log_and_wait("Waiting for screen transition after END_OF_GAME click", 3)
                
                # Verificar se passou tempo suficiente para tentar novamente (5 segundos)
                if not hasattr(self, 'end_of_game_click_time'):
                    self.end_of_game_click_time = time.time()
                elif time.time() - self.end_of_game_click_time > 5:  # Tentar novamente após 5 segundos
                    logger.info("🔄 Passou tempo suficiente, tentando clicar novamente no END_OF_GAME...")
                    try:
                        click_coords = self.state.screen.click_xy
                        logger.info(f"🔄 Tentando clicar novamente no END_OF_GAME em: {click_coords}")
                        self.emulator.click(*click_coords)
                        self.end_of_game_clicked = True
                        self.end_of_game_click_time = time.time()
                        self._log_and_wait("Clicked END_OF_GAME screen again", 2)
                        logger.info("✅ Clique adicional no END_OF_GAME realizado!")
                    except Exception as e:
                        logger.error(f"Error clicking END_OF_GAME again: {e}")
                        # Tentar posições alternativas novamente
                        logger.info("🔄 Tentando posições alternativas novamente...")
                        alternative_positions = [
                            (250, 1140),  # Posição original
                            (360, 650),   # Posição central
                            (250, 1100),  # Ligeiramente acima
                            (250, 1180),  # Ligeiramente abaixo
                            (200, 1140),  # Ligeiramente à esquerda
                            (300, 1140),  # Ligeiramente à direita
                        ]
                        
                        for alt_pos in alternative_positions:
                            try:
                                logger.info(f"🔄 Tentando posição alternativa: {alt_pos}")
                                self.emulator.click(*alt_pos)
                                self.end_of_game_clicked = True
                                self.end_of_game_click_time = time.time()
                                self._log_and_wait(f"Clicked END_OF_GAME at alternative position {alt_pos}", 2)
                                logger.info(f"✅ Clique alternativo realizado com sucesso em {alt_pos}!")
                                break
                            except Exception as alt_e:
                                logger.debug(f"Failed alternative position {alt_pos}: {alt_e}")
                                continue
                elif time.time() - self.end_of_game_click_time > 15:  # Timeout após 15 segundos
                    logger.warning("⚠️ Timeout na tela de fim de jogo - resetando flag para tentar novamente")
                    self.end_of_game_clicked = False
                    self.end_of_game_click_time = time.time()
            return

        # Detectar tela de "jogar de novo" (crowns/resultado)
        # Adicionar delay para evitar falsos positivos logo após iniciar partida
        if hasattr(self, 'game_start_time') and self.game_start_time is not None:
            time_since_start = time.time() - self.game_start_time
            if time_since_start < 60:  # Aumentar para 60 segundos para evitar falsos positivos
                logger.debug(f"Game started recently ({time_since_start:.1f}s ago), skipping play again detection")
            elif self._is_play_again_screen(new_screen):
                # Verificação adicional: se detectou "jogar de novo" mas está no jogo, ignorar
                if self._is_definitely_in_game():
                    logger.debug("Ignoring false positive - definitely in game")
                else:
                    logger.info("🎯 Tela de 'Jogar de Novo' detectada")
                    if self.auto_restart:
                        self._handle_play_again_screen()
                    else:
                        logger.info("Auto-restart desabilitado, aguardando ação manual")
                    return
            else:
                logger.debug(f"Play again screen not detected - time since start: {time_since_start:.1f}s")
        else:
            # Se não tem game_start_time, usar detecção normal mas com verificação adicional
            if self._is_play_again_screen(new_screen):
                # Verificação adicional: se detectou "jogar de novo" mas está no jogo, ignorar
                if self._is_definitely_in_game():
                    logger.debug("Ignoring false positive - definitely in game")
                else:
                    logger.info("🎯 Tela de 'Jogar de Novo' detectada")
                    if self.auto_restart:
                        self._handle_play_again_screen()
                    else:
                        logger.info("Auto-restart desabilitado, aguardando ação manual")
                    return

        self.end_of_game_clicked = False

        if self.auto_start and new_screen == Screens.LOBBY:
            logger.info("Lobby detected, auto-starting game")
            try:
                # Resetar end_of_game_clicked quando inicia uma nova partida
                if self.end_of_game_clicked:
                    self.end_of_game_clicked = False
                    logger.info("Reset end_of_game_clicked for new game")
                
                self.emulator.click(*self.state.screen.click_xy)
                self._log_and_wait("Starting game", 2)
                # Registrar início da partida
                self.game_start_time = time.time()
            except Exception as e:
                logger.error(f"Error clicking battle button: {e}")
            return

        # Se chegou até aqui, está no jogo
        logger.debug("Processing game step")
        
        # Garantir que game_start_time está inicializado
        if not hasattr(self, 'game_start_time') or self.game_start_time is None:
            self.game_start_time = time.time()
            logger.info("Game start time initialized")
        

        
        try:
            self._handle_game_step()
        except Exception as e:
            logger.error(f"Error in game step: {e}")
            import traceback
            logger.error(f"Game step traceback: {traceback.format_exc()}")
            # Continua executando em vez de fechar
            time.sleep(1)

    def _handle_game_step(self):
        try:
            actions = self.get_actions()
            if not actions:
                # Analisa por que não há ações disponíveis
                elixir = self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0
                ready_cards = self.state.ready if hasattr(self.state, 'ready') else []
                
                logger.debug(f"No actions available - Elixir: {elixir}, Ready cards: {ready_cards}")
                
                # Se não há cartas prontas, aguarda elixir regenerar
                if not ready_cards:
                    logger.info(f"Waiting for cards to be ready (Elixir: {elixir})")
                    self._log_and_wait("Waiting for cards to be ready", max(1.0, self.play_action_delay))
                    return
                
                # Se há cartas prontas mas são muito caras, aguarda elixir
                if ready_cards and elixir < 2:
                    cheapest_card_cost = min([self.state.cards[i + 1].cost for i in ready_cards])
                    logger.info(f"Waiting for elixir - Need {cheapest_card_cost}, have {elixir}")
                    self._log_and_wait(f"Waiting for elixir ({elixir}/{cheapest_card_cost})", max(1.0, self.play_action_delay))
                    return
                
                # Caso geral - aguarda
                logger.debug(f"No valid actions - Cards: {len(self.state.cards) if self.state.cards else 0}, Ready: {ready_cards}")
                self._log_and_wait("No valid actions available", self.play_action_delay)
                return
        except Exception as e:
            logger.error(f"Error in _handle_game_step: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._log_and_wait("Error in game step", self.play_action_delay)
            return

        # Iniciar coleta de dados se ML estiver ativado
        if self.enable_ml and not self.game_started:
            self.data_collector.start_new_game()
            self.deck_analyzer.start_new_game()
            self.game_started = True
            
            # Resetar end_of_game_clicked quando uma nova partida realmente começa
            if self.end_of_game_clicked:
                self.end_of_game_clicked = False
                logger.info("Reset end_of_game_clicked for new game (game started)")
        
        # Iniciar sistema de memória se não foi iniciado
        if not hasattr(self, 'memory_started') or not self.memory_started:
            self.deck_memory.reset_for_new_game()
            self.memory_started = True
            logger.info("Deck memory system started for new game")

        # Detectar cartas do inimigo e registrar na memória
        if self.enable_ml and self.enemy_detector:
            self.enemy_detector.detect_enemy_cards(self.state)
        
        # Registrar cartas inimigas vistas na memória
        enemy_units = self._get_enemy_units()
        for unit in enemy_units:
            if unit['name'] != 'unknown' and unit['name'] != 'blank':
                self.deck_memory.record_enemy_card_seen(unit['name'])
                
                # Registrar ação do oponente para análise de padrões
                if self.pattern_analyzer:
                    opponent_action = {
                        'card_name': unit['name'],
                        'elixir_cost': self._get_card_elixir_cost(unit['name']),
                        'tile_x': unit.get('x', 0),
                        'tile_y': unit.get('y', 0)
                    }
                    game_state = {
                        'elixir': self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0,
                        'ally_tower_health': [self.state.numbers.ally_left_tower.number, self.state.numbers.ally_right_tower.number] if hasattr(self.state.numbers, 'ally_left_tower') else [1.0, 1.0],
                        'enemy_tower_health': [self.state.numbers.enemy_left_tower.number, self.state.numbers.enemy_right_tower.number] if hasattr(self.state.numbers, 'enemy_left_tower') else [1.0, 1.0],
                        'game_time': time.time() - self.game_start_time if hasattr(self, 'game_start_time') and self.game_start_time is not None else 0
                    }
                    self.pattern_analyzer.record_opponent_action(opponent_action, game_state)
        
        # Obter análise do inimigo
        enemy_analysis = None
        if self.enable_ml and self.enemy_detector:
            enemy_analysis = self.enemy_detector.get_enemy_analysis()
        
        # Obter análise da memória de deck
        deck_analysis = self.deck_memory.get_deck_analysis()
        
        # Integrar informações da memória na análise do inimigo
        if not enemy_analysis:
            enemy_analysis = {}
        
        enemy_analysis['deck_memory'] = deck_analysis['enemy_deck']
        enemy_analysis['strategic_insights'] = deck_analysis['strategic_insights']
        
        # === ANÁLISE DE PADRÕES E ADAPTAÇÃO ===
        
        # Obter perfil do oponente baseado em padrões
        opponent_profile = None
        if self.pattern_analyzer:
            opponent_profile = self.pattern_analyzer.get_opponent_profile()
            logger.debug(f"Opponent profile: {opponent_profile.get('playstyle', 'unknown')} (confidence: {opponent_profile.get('confidence', 0.0):.2f})")
        
        # Adaptar estratégia baseado no perfil do oponente
        strategy_adaptation = None
        if self.adaptive_strategy and opponent_profile:
            game_state = {
                'elixir': self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0,
                'ally_tower_health': [self.state.numbers.ally_left_tower.number, self.state.numbers.ally_right_tower.number] if hasattr(self.state.numbers, 'ally_left_tower') else [1.0, 1.0],
                'enemy_tower_health': [self.state.numbers.enemy_left_tower.number, self.state.numbers.enemy_right_tower.number] if hasattr(self.state.numbers, 'enemy_left_tower') else [1.0, 1.0],
                'enemy_units': enemy_units
            }
            strategy_adaptation = self.adaptive_strategy.analyze_opponent_and_adapt(opponent_profile, game_state)
            logger.info(f"🎯 Strategy adapted: {strategy_adaptation.get('strategy', 'balanced')} - {strategy_adaptation.get('reason', 'unknown')}")
        
        # Análise estratégica da situação com detecção de ameaças
        situation_analysis = self._analyze_game_situation()
        
        # === ESTRATÉGIAS BASEADAS NA FASE DO JOGO ===
        
        # Determinar fase atual do jogo
        game_time = time.time() - self.game_start_time if hasattr(self, 'game_start_time') and self.game_start_time is not None else 0
        current_phase = "opening" if game_time < 60 else "mid_game" if game_time < 180 else "late_game"
        
        # Obter estratégias recomendadas para a fase atual
        phase_strategies = {}
        if hasattr(self, 'strategic_thinking'):
            phase_strategies = self.strategic_thinking.get_strategy_for_current_phase({
                'game_time': game_time,
                'elixir': self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0,
                'under_pressure': self._is_under_pressure(),
                'advantage': self._has_advantage()
            })
            
            # Obter movimentos recomendados para a fase
            recommended_moves = self.strategic_thinking.get_recommended_moves_for_phase({
                'game_time': game_time,
                'elixir': self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0,
                'under_pressure': self._is_under_pressure(),
                'advantage': self._has_advantage()
            })
            
            if recommended_moves:
                logger.info(f"📋 Phase {current_phase} strategies: {len(recommended_moves)} recommended moves")
                for move in recommended_moves[:3]:  # Log dos 3 primeiros movimentos
                    logger.debug(f"  • {move.get('move', 'unknown')}: {move.get('reasoning', 'unknown')}")
        
        # Inferir estado do jogo usando regras do banco de dados
        inferred_state = "unknown"
        if hasattr(self, 'strategic_thinking'):
            inferred_state = self.strategic_thinking.infer_game_state_from_database({
                'game_time': game_time,
                'elixir': self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0,
                'enemy_elixir': self._estimate_enemy_elixir(),
                'tower_hp': min(self.state.numbers.ally_left_tower.number, self.state.numbers.ally_right_tower.number) if hasattr(self.state.numbers, 'ally_left_tower') else 1000,
                'surviving_troops_elixir': self._calculate_surviving_troops_elixir()
            })
            
            if inferred_state != "unknown":
                logger.info(f"🎯 Inferred game state: {inferred_state}")
        
        # Integrar estratégias de fase na análise de situação
        situation_analysis['game_phase'] = current_phase
        situation_analysis['phase_strategies'] = phase_strategies
        situation_analysis['inferred_state'] = inferred_state
        
        # === ANÁLISE TÁTICA PROFUNDA ===
        
        # Análise de ameaças específicas (Giant atrás da torre, etc.)
        try:
            our_elixir = self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0
            enemy_elixir = self._estimate_enemy_elixir()
            
            threat_analysis = self.tactical_analyzer.analyze_threat_situation(
                enemy_units, our_elixir, enemy_elixir
            )
            situation_analysis['tactical_threat'] = threat_analysis
            
            if threat_analysis['threat_level'] >= 8:
                logger.warning(f"🚨 HIGH THREAT: {threat_analysis['threat_type']} - {threat_analysis.get('recommended_response', 'unknown')}")
                
        except Exception as e:
            logger.debug(f"Error in tactical threat analysis: {e}")
            situation_analysis['tactical_threat'] = {'threat_type': 'none', 'threat_level': 0}
        
        # Análise de oportunidade de counter-push
        try:
            our_units = self._get_our_units()
            counter_push_analysis = self.tactical_analyzer.analyze_counter_push_opportunity(our_units, enemy_units)
            situation_analysis['counter_push'] = counter_push_analysis
            
            if counter_push_analysis['has_opportunity']:
                logger.info(f"⚔️ Counter-push opportunity: {counter_push_analysis['push_type']}")
                
        except Exception as e:
            logger.debug(f"Error in counter-push analysis: {e}")
            situation_analysis['counter_push'] = {'has_opportunity': False}
        
        # Análise de ameaças (reativada com tratamento robusto)
        try:
            immediate_threats = self._detect_immediate_threats(enemy_units)
            situation_analysis['immediate_threats'] = immediate_threats
            logger.debug(f"Immediate threats detected: {immediate_threats.get('total_threat_level', 0)}")
        except Exception as e:
            logger.debug(f"Error detecting immediate threats: {e}")
            situation_analysis['immediate_threats'] = {'requires_immediate_action': False}
        
        # Análise de concentração de lane (reativada com tratamento robusto)
        try:
            lane_concentration = self._analyze_lane_concentration(enemy_units)
            situation_analysis['lane_concentration'] = lane_concentration
            logger.debug(f"Lane concentration: {lane_concentration.get('main_pressure_lane', 'none')}")
        except Exception as e:
            logger.debug(f"Error analyzing lane concentration: {e}")
            situation_analysis['lane_concentration'] = {'should_focus_defense': False}
        
        # === ANÁLISE TÁTICA FINAL E AJUSTES DE PRIORIDADE ===
        
        # Verificar se ameaça tática deve sobrescrever prioridade
        tactical_threat = situation_analysis.get('tactical_threat', {})
        if tactical_threat.get('threat_level', 0) >= 8:
            threat_type = tactical_threat.get('threat_type', 'unknown')
            recommended_response = tactical_threat.get('recommended_response', 'prepare_defense')
            
            # Sobrescrever prioridade se ameaça tática é crítica
            old_priority = situation_analysis.get('priority', 'neutral')
            situation_analysis['priority'] = f'tactical_response_{threat_type}'
            
            if recommended_response == 'quick_opposite_attack':
                situation_analysis['should_attack'] = True
                situation_analysis['should_defend'] = False
                logger.info(f"🚨 Tactical override: Quick opposite attack vs {threat_type} (was {old_priority})")
            elif 'defense' in recommended_response:
                situation_analysis['should_defend'] = True
                situation_analysis['should_attack'] = False
                logger.info(f"🛡️ Tactical override: Prepare defense vs {threat_type} (was {old_priority})")
            elif 'cycle' in recommended_response:
                situation_analysis['should_cycle'] = True
                situation_analysis['should_attack'] = False
                situation_analysis['should_defend'] = False
                logger.info(f"🔄 Tactical override: Cycle and defend vs {threat_type} (was {old_priority})")
        
        # Decidir se deve jogar uma carta ou esperar
        should_play = self._should_play_card(situation_analysis)
        
        if not should_play:
            elixir = self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0
            logger.info(f"Waiting for better opportunity. Situation: {situation_analysis['priority']}, Elixir: {elixir}")
            
            # Aguarda mais tempo se elixir muito baixo
            wait_time = self.play_action_delay
            if elixir <= 2:
                wait_time = max(2.0, self.play_action_delay)
            elif elixir <= 4:
                wait_time = max(1.5, self.play_action_delay)
            
            self._log_and_wait(f"Waiting for better opportunity (Elixir: {elixir})", wait_time)
            return
        
        # Filtrar ações baseado na situação
        filtered_actions = self._filter_actions_by_situation(actions, situation_analysis)
        
        if not filtered_actions:
            elixir = self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0
            logger.info(f"No suitable actions for current situation. Elixir: {elixir}, Total actions: {len(actions)}")
            
            # Se há ações mas foram filtradas, aguarda menos tempo
            if actions:
                self._log_and_wait(f"No suitable actions (have {len(actions)} total)", max(1.0, self.play_action_delay))
            else:
                self._log_and_wait("No actions available", self.play_action_delay)
            return
        
        # Usar ML e inteligência de cartas para escolher a melhor ação
        best_action = None
        best_score = -float('inf')

        for action in filtered_actions:
            # Obter nome da carta
            card_name = self.state.cards[action.index + 1].name if hasattr(self.state, 'cards') and len(self.state.cards) > action.index + 1 else "unknown"
            
            # Score original do bot
            original_score = action.calculate_score(self.state)
            
            # Garante que o score é um número
            if isinstance(original_score, list):
                original_score = original_score[0] if original_score else 0
            original_score = float(original_score)
            
            # Bônus de posicionamento inteligente
            positioning_bonus = 0
            if hasattr(action, 'should_use_intelligent_positioning') and action.should_use_intelligent_positioning(self.state):
                situation = action.get_situation_based_positioning(self.state)
                optimal_pos = action.get_optimal_positioning(self.state, situation)
                
                if optimal_pos and optimal_pos.get("tile_x") == action.tile_x and optimal_pos.get("tile_y") == action.tile_y:
                    positioning_bonus = 0.2  # Bônus para posicionamento ótimo
                    logger.debug(f"🎯 Posicionamento ótimo para {card_name}: {optimal_pos.get('description', '')}")
                else:
                    # Penalidade menor para posicionamento não ótimo
                    positioning_bonus = -0.1
            
            # Score do ML (se treinado)
            ml_score = 0.5  # Score neutro padrão
            if self.enable_ml and self.ml_bot and self.ml_bot.trained:
                ml_score = self.ml_bot.predict_action_score(self.state, action, enemy_analysis)
            
            # Bônus baseado na análise do inimigo
            enemy_bonus = 0
            if enemy_analysis:
                enemy_bonus = self.calculate_enemy_based_bonus(action, enemy_analysis)
            
            # Análise de inteligência de cartas
            card_intelligence_bonus = 0
            if card_name != "unknown" and card_name != "blank":
                # Criar estado do jogo para análise
                game_state = {
                    "elixir": self.state.numbers.elixir.number if hasattr(self.state.numbers, 'elixir') else 0,
                    "under_pressure": self._is_under_pressure(),
                    "advantage": self._has_advantage(),
                    "enemy_elixir_state": self._get_enemy_elixir_state(),
                    "has_tank": self._has_tank_on_field(),
                    "need_air_defense": self._needs_air_defense()
                }
                
                # Análise de decisão da carta
                card_decision = knowledge_base.analyze_card_decision(card_name, game_state, enemy_analysis)
                
                # Aplicar bônus baseado na decisão
                if card_decision["decision"] == "use":
                    card_intelligence_bonus = 0.3
                elif card_decision["decision"] == "wait":
                    card_intelligence_bonus = 0.1
                elif card_decision["decision"] == "avoid":
                    card_intelligence_bonus = -0.5  # Penalidade forte
            
            # Bônus baseado na situação atual
            situation_bonus = self._calculate_situation_bonus(action, situation_analysis)
            
            # Combina os scores com pesos ajustados
            if self.enable_ml and self.ml_bot and self.ml_bot.trained:
                combined_score = 0.35 * ml_score + 0.2 * (original_score / 100) + 0.15 * enemy_bonus + 0.1 * card_intelligence_bonus + 0.1 * positioning_bonus + 0.1 * situation_bonus
            else:
                combined_score = original_score / 100 + enemy_bonus * 0.25 + card_intelligence_bonus * 0.15 + positioning_bonus * 0.15 + situation_bonus * 0.15
            
            if combined_score > best_score:
                best_score = combined_score
                best_action = action

        if best_action:
            # Obter nome da carta antes de jogar
            card_name = self.state.cards[best_action.index + 1].name if hasattr(self.state, 'cards') and len(self.state.cards) > best_action.index + 1 else "unknown"
            
            # Registrar na memória que jogamos esta carta
            if card_name != "unknown" and card_name != "blank":
                self.deck_memory.record_our_card_played(card_name)
            
            # Executa a ação
            self.play_action(best_action)
            
            # Calcula recompensa e registra para ML
            if self.enable_ml:
                reward = self._calculate_reward(best_action)
                self.data_collector.record_action(best_action, self.state, reward)
            
            # Log da ação com informações da memória
            deck_analysis = self.deck_memory.get_deck_analysis()
            our_next_cards = deck_analysis['our_deck'].get('next_cards', [])
            logger.info(f"Playing {card_name} at ({best_action.tile_x}, {best_action.tile_y}) - Score: {best_score:.2f} - Situation: {situation_analysis['priority']} - Next: {our_next_cards[:2]}")
            
            self._log_and_wait(
                f"Playing {best_action} with score {best_score:.2f}",
                self.play_action_delay,
            )
        else:
            self._log_and_wait(
                "No good actions available", self.play_action_delay
            )

    def _calculate_reward(self, action):
        """Calcula recompensa avançada baseada em múltiplos fatores"""
        reward = 0
        card_name = self.state.cards[action.index + 1].name
        card_cost = self.state.cards[action.index + 1].cost
        our_elixir = self.state.numbers.elixir.number
        
        # Recompensa base da ação
        action_score = action.calculate_score(self.state)
        if isinstance(action_score, list):
            action_score = action_score[0] if action_score else 0
        reward += float(action_score) / 100
        
        # === RECOMPENSAS ESTRATÉGICAS ===
        
        # Bônus por eficiência de elixir (com tratamento de erro)
        try:
            enemy_units = self._get_enemy_units()
            if enemy_units:
                # Calcula valor das tropas que pode counter
                countered_value = sum(self._estimate_card_cost(unit['name']) for unit in enemy_units 
                                    if self._can_counter(card_name, unit['name']))
                if countered_value > card_cost:
                    reward += 0.4  # Excelente trade de elixir
                elif countered_value == card_cost:
                    reward += 0.2  # Trade neutro
        except Exception as e:
            logger.debug(f"Error calculating elixir efficiency: {e}")
        
        # Bônus por timing correto (com tratamento de erro)
        try:
            situation = self._analyze_game_situation()
            if situation['priority'] == 'emergency_defend' and self._is_defensive_card(card_name):
                reward += 0.5  # Defesa no momento certo
            elif situation['priority'] in ['aggressive_attack', 'pressure_attack'] and self._is_offensive_card(card_name):
                reward += 0.4  # Ataque no momento certo
            elif situation['should_cycle'] and self._is_cycle_card(card_name):
                reward += 0.3  # Cycle no momento certo
        except Exception as e:
            logger.debug(f"Error calculating timing bonus: {e}")
        
        # Bônus por combo/sinergia (com tratamento de erro)
        try:
            our_units = self._get_our_units()
            if card_name == 'giant' and any(unit['name'] in ['musketeer', 'archers'] for unit in our_units):
                reward += 0.3  # Giant com suporte
            elif card_name in ['musketeer', 'archers'] and any(unit['name'] == 'giant' for unit in our_units):
                reward += 0.3  # Suporte atrás do tank
        except Exception as e:
            logger.debug(f"Error calculating combo bonus: {e}")
        
        # === PENALIDADES ===
        
        # Penalidade por desperdício de elixir
        if our_elixir < 2 and card_cost > 3:
            reward -= 0.4  # Gastou muito com pouco elixir
        
        # Penalidade por má escolha de timing
        if situation['should_defend'] and self._is_offensive_card(card_name) and situation['enemy_pressure'] > 1:
            reward -= 0.3  # Atacou quando deveria defender
        
        # Penalidade por posicionamento ruim
        if action.tile_y > 14:  # Muito próximo das nossas torres
            reward -= 0.2
        
        # === RECOMPENSAS DE LONGO PRAZO ===
        
        # Bônus por preparar combo futuro
        if card_name == 'giant' and our_elixir >= 7:
            reward += 0.2  # Giant com elixir para suporte
        
        # === RECOMPENSAS POR POSICIONAMENTO ESTRATÉGICO ===
        
        # Bônus por não causar dano desnecessário à torre
        if action.tile_y < 12:  # Longe das nossas torres
            reward += 0.1
        
        # Bônus por posicionamento que evita range de atenção perigoso
        try:
            enemy_units = self._get_enemy_units()
            attention_analysis = self.attention_system.calculate_attention_from_position(
                (action.tile_x, action.tile_y), enemy_units, card_name
            )
            
            if attention_analysis['safe_placement']:
                reward += 0.2  # Posicionamento seguro
            elif attention_analysis['attention_score'] > 8:
                reward -= 0.3  # Posicionamento perigoso
                
        except Exception as e:
            logger.debug(f"Error calculating attention reward: {e}")
        
        # Bônus por resposta rápida a ameaças
        if hasattr(situation, 'immediate_threats') and situation['immediate_threats']['requires_immediate_action']:
            if self._is_defensive_card(card_name) or self._is_counter_card(card_name):
                reward += 0.4  # Resposta rápida a ameaça
        
        # Bônus por não jogar carta aleatória quando há concentração inimiga
        if hasattr(situation, 'lane_concentration') and situation['lane_concentration']['should_focus_defense']:
            main_lane = situation['lane_concentration']['main_pressure_lane']
            
            # Verifica se a carta está sendo jogada na lane correta
            if main_lane in ['left_lane', 'right_lane']:
                lane_x_range = (0, 6) if main_lane == 'left_lane' else (11, 17)
                if lane_x_range[0] <= action.tile_x <= lane_x_range[1]:
                    reward += 0.3  # Jogou na lane correta
                else:
                    reward -= 0.4  # Jogou na lane errada, desperdiçando carta
        
        # Bônus por counter preventivo (com tratamento de erro)
        try:
            deck_analysis = self.deck_memory.get_deck_analysis()
            enemy_next = deck_analysis['enemy_deck'].get('predicted_next', [])
            for prediction in enemy_next:
                if prediction.get('probability', 0) > 0.7:
                    enemy_card = prediction['card']
                    if self._can_counter(card_name, enemy_card):
                        reward += 0.3 * prediction['probability']  # Counter preventivo
        except Exception as e:
            logger.debug(f"Error calculating preventive counter bonus: {e}")
        
        # Limita recompensa entre -1 e +1
        return max(-1.0, min(1.0, reward))
    
    def calculate_enemy_based_bonus(self, action, enemy_analysis):
        """Calcula bônus baseado na análise do inimigo usando base de conhecimento"""
        bonus = 0
        card_name = self.state.cards[action.index + 1].name
        
        # Obtém nosso deck atual
        our_deck = [card.name for card in self.state.cards if card.name != 'blank']
        
        # Bônus por contra-jogada usando base de conhecimento
        if enemy_analysis.get('weaknesses'):
            weaknesses = enemy_analysis['weaknesses']
            
            # Consulta base de conhecimento para counters
            for weakness in weaknesses:
                if weakness == "no_air_troops":
                    counters = knowledge_base.get_counter_suggestions("baby_dragon", our_deck)
                    if card_name in counters:
                        bonus += 0.3
                
                elif weakness == "giant_no_spells":
                    counters = knowledge_base.get_counter_suggestions("giant", our_deck)
                    if card_name in counters:
                        bonus += 0.2
                
                elif weakness == "few_spells":
                    counters = knowledge_base.get_counter_suggestions("archers", our_deck)
                    if card_name in counters:
                        bonus += 0.2
        
        # Bônus por estratégia sugerida
        if enemy_analysis.get('strategies'):
            strategies = enemy_analysis['strategies']
            
            for strategy in strategies:
                if strategy == "use_air_units":
                    counters = knowledge_base.get_counter_suggestions("baby_dragon", our_deck)
                    if card_name in counters:
                        bonus += 0.2
                
                elif strategy == "counter_giant_with_swarm":
                    counters = knowledge_base.get_counter_suggestions("giant", our_deck)
                    if card_name in counters:
                        bonus += 0.2
        
        # Bônus por contra carta específica esperada
        expected_cards = enemy_analysis.get('next_expected', [])
        for expected in expected_cards:
            enemy_card = expected['card']
            probability = expected['probability']
            
            # Usa base de conhecimento para counters
            counters = knowledge_base.get_counter_suggestions(enemy_card, our_deck)
            if card_name in counters:
                bonus += 0.1 * probability
        
        # Bônus por posicionamento otimizado
        positioning_guide = knowledge_base.get_positioning_guide(card_name, "defensive")
        if positioning_guide:
            # Bônus se a posição está otimizada
            if action.tile_y < 10:  # Lado defensivo
                bonus += 0.1
        
        # Bônus por eficiência de elixir
        if enemy_analysis.get('deck_prediction'):
            deck_prediction = enemy_analysis['deck_prediction']
            if deck_prediction.get('avg_elixir', 4.0) > 3.8:  # Deck pesado
                # Prefere cartas baratas contra decks pesados
                card_cost = self.state.cards[action.index + 1].cost
                if card_cost <= 3:
                    bonus += 0.1
        
        return min(bonus, 0.5)  # Limita o bônus máximo
    
    def _is_under_pressure(self):
        """Verifica se estamos sob pressão"""
        if not hasattr(self.state, 'enemy_towers') or not self.state.enemy_towers:
            return False
        
        # Verifica se alguma torre inimiga está atacando
        for tower in self.state.enemy_towers:
            if hasattr(tower, 'health') and tower.health > 0:
                return True
        
        return False
    
    def _has_advantage(self):
        """Verifica se temos vantagem"""
        if not hasattr(self.state, 'elixir'):
            return False
        
        # Vantagem de elixir
        if self.state.elixir >= 7:
            return True
        
        # Vantagem de torres (se disponível)
        if hasattr(self.state, 'ally_towers') and hasattr(self.state, 'enemy_towers'):
            ally_health = sum(tower.health for tower in self.state.ally_towers if hasattr(tower, 'health'))
            enemy_health = sum(tower.health for tower in self.state.enemy_towers if hasattr(tower, 'health'))
            if ally_health > enemy_health * 1.2:  # 20% mais vida
                return True
        
        return False
    
    def _get_enemy_elixir_state(self):
        """Estima o estado do elixir inimigo"""
        # Implementação básica - pode ser melhorada com análise mais sofisticada
        return "medium_elixir"  # Padrão
    
    def _has_tank_on_field(self):
        """Verifica se temos um tank no campo"""
        if not hasattr(self.state, 'ally_units') or not self.state.ally_units:
            return False
        
        tank_cards = ["giant", "pekka", "golem", "royal_giant", "electro_giant"]
        for unit in self.state.ally_units:
            if hasattr(unit, 'name') and unit.name in tank_cards:
                return True
        
        return False
    
    def _needs_air_defense(self):
        """Verifica se precisamos de defesa aérea"""
        if not hasattr(self.state, 'enemy_units') or not self.state.enemy_units:
            return False
        
        air_cards = ["baby_dragon", "minions", "bats", "balloon", "lava_hound"]
        for unit in self.state.enemy_units:
            if hasattr(unit, 'name') and unit.name in air_cards:
                return True
        
        return False
    
    def end_game(self, result):
        """Chamado quando a partida termina"""
        if self.enable_ml and self.data_collector:
            self.data_collector.end_game(result)
            self.game_started = False
            
            # Treina o modelo com os dados coletados
            if self.ml_bot:
                self.ml_bot.train(self.data_collector.get_training_data())
            
            # Mostra estatísticas
            stats = self.data_collector.get_stats()
            logger.info(f"Game ended: {result}. "
                       f"Total games: {stats['total_games']}, "
                       f"Win rate: {stats['win_rate']:.2%}")
            
            # Sistema de evolução ML
            if self.ml_bot and self.generation_manager:
                try:
                    # Preparar métricas de performance
                    performance_metrics = {
                        'win_rate': stats['win_rate'],
                        'games_played': stats['total_games'],
                        'avg_score': stats.get('avg_score', 0),
                        'best_score': stats.get('best_score', 0),
                        'last_result': result
                    }
                    
                    logger.info(f"🔬 ML Evolution Check:")
                    logger.info(f"   • Win rate: {stats['win_rate']:.2%}")
                    logger.info(f"   • Games played: {stats['total_games']}")
                    logger.info(f"   • Performance metrics: {performance_metrics}")
                    
                    # Verificar se deve evoluir
                    should_evolve = self.generation_manager.should_evolve(performance_metrics, stats['total_games'])
                    logger.info(f"   • Should evolve: {should_evolve}")
                    
                    if should_evolve:
                        evolved = self.ml_bot.evolve_if_needed(performance_metrics, stats['total_games'])
                        logger.info(f"   • Evolution attempted: {evolved}")
                        
                        if evolved:
                            logger.info("🎯 EVOLUTION COMPLETED!")
                            
                            # Mostrar informações das gerações
                            gen_info = self.ml_bot.get_generation_info()
                            if gen_info.get('generations_enabled'):
                                stats_info = gen_info.get('statistics', {})
                                logger.info(f"📊 Generation Statistics:")
                                logger.info(f"   • Total generations: {stats_info.get('total_generations', 0)}")
                                logger.info(f"   • Current generation: {stats_info.get('current_generation', 0)}")
                                
                                # Mostrar performance de cada geração
                                for gen_id, gen_data in stats_info.get('generations', {}).items():
                                    win_rate = gen_data.get('win_rate', 0)
                                    games = gen_data.get('games_played', 0)
                                    logger.info(f"   • Generation {gen_id}: {win_rate:.2%} win rate ({games} games)")
                    else:
                        logger.info(f"   • Evolution not needed - current performance is acceptable")
                    
                except Exception as e:
                    logger.error(f"Error in ML evolution: {e}")
                    import traceback
                    logger.error(f"Evolution traceback: {traceback.format_exc()}")
            else:
                logger.info(f"🔬 ML Evolution: {'ML Bot' if self.ml_bot else 'No ML Bot'} + {'Generation Manager' if self.generation_manager else 'No Generation Manager'}")
        
        # Finalizar análise de padrões
        if self.pattern_analyzer:
            try:
                self.pattern_analyzer.end_game(result)
                
                # Mostrar resumo da análise
                analysis_summary = self.pattern_analyzer.get_analysis_summary()
                logger.info(f"📊 Pattern Analysis Summary:")
                logger.info(f"   • Patterns identified: {analysis_summary.get('current_patterns', 0)}")
                logger.info(f"   • Analysis confidence: {analysis_summary.get('analysis_confidence', 0.0):.2f}")
                
                # Mostrar perfil do oponente
                opponent_profile = self.pattern_analyzer.get_opponent_profile()
                logger.info(f"🎯 Opponent Profile:")
                logger.info(f"   • Playstyle: {opponent_profile.get('playstyle', 'unknown')}")
                logger.info(f"   • Confidence: {opponent_profile.get('confidence', 0.0):.2f}")
                logger.info(f"   • Weaknesses: {opponent_profile.get('weaknesses', [])}")
                
            except Exception as e:
                logger.error(f"Error in pattern analysis end game: {e}")
        
        # Finalizar estratégia adaptativa
        if self.adaptive_strategy:
            try:
                # Mostrar resumo das adaptações
                adaptation_summary = self.adaptive_strategy.get_adaptation_summary()
                logger.info(f"🔄 Strategy Adaptation Summary:")
                logger.info(f"   • Current strategy: {adaptation_summary.get('current_strategy', 'unknown')}")
                logger.info(f"   • Adaptations made: {adaptation_summary.get('adaptation_count', 0)}")
                
                # Resetar estratégia para próxima partida
                self.adaptive_strategy.reset_strategy()
                
            except Exception as e:
                logger.error(f"Error in adaptive strategy end game: {e}")
        
        # Mostrar estatísticas gerais
        logger.info(f"📊 ESTATÍSTICAS GERAIS:")
        logger.info(f"   • Total de partidas jogadas: {self.games_played}")
        if self.game_start_time is not None:
            game_duration = time.time() - self.game_start_time
            logger.info(f"   • Duração da partida: {game_duration:.1f} segundos")
        
        # Mostrar resumo se auto-restart está ativo
        if self.auto_restart:
            logger.info(f"🔄 Auto-restart ativo - Próxima partida será iniciada automaticamente")
        else:
            logger.info(f"⏸️ Auto-restart desabilitado - Aguardando ação manual")
    
    def run(self):
        try:
            logger.info("Bot run loop started")
            step_count = 0
            
            # Log inicial para debug
            logger.info(f"Initial state - should_run: {self.should_run}, pause_event: {pause_event.is_set()}")
            
            while self.should_run:
                step_count += 1
                
                # Log mais frequente no início para debug
                if step_count <= 5 or step_count % 10 == 0:
                    logger.info(f"Bot loop iteration {step_count}, should_run: {self.should_run}")
                
                if not pause_event.is_set():
                    logger.debug("Bot paused, waiting...")
                    time.sleep(0.1)
                    continue

                try:
                    logger.debug(f"About to call step() - iteration {step_count}")
                    
                    # Debug detalhado para primeira iteração
                    if step_count == 1:
                        logger.info("FIRST STEP - detailed debugging")
                        logger.info(f"Bot state before step: should_run={self.should_run}")
                        logger.info(f"Bot components: emulator={hasattr(self, 'emulator')}, detector={hasattr(self, 'detector')}")
                    
                    self.step()
                    logger.debug(f"Step {step_count} completed successfully")
                except Exception as step_error:
                    logger.error(f"CRITICAL ERROR in step {step_count}: {step_error}")
                    import traceback
                    logger.error(f"Step traceback: {traceback.format_exc()}")
                    
                    # Se for a primeira iteração, é crítico
                    if step_count == 1:
                        logger.error("FIRST STEP FAILED - this is critical!")
                        raise  # Re-raise para captura pela GUI
                    
                    # Para outras iterações, continua
                    time.sleep(1)
                    continue
                
                # Verifica se should_run foi alterado inesperadamente
                if not self.should_run:
                    logger.warning(f"should_run became False at step {step_count}")
                    break
                    
            logger.info(f"Bot run loop ended after {step_count} steps - should_run is {self.should_run}")
        except KeyboardInterrupt:
            logger.info("Bot interrupted by user")
        except Exception as run_error:
            logger.error(f"CRITICAL ERROR in bot run loop: {run_error}")
            import traceback
            logger.error(f"Run loop traceback: {traceback.format_exc()}")
            # Re-raise para que a GUI possa capturar
            raise
        finally:
            logger.info("Thanks for using CRBAB, see you next time!")

    def stop(self):
        self.should_run = False

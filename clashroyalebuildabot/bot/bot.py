import random
import threading
import time

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
from clashroyalebuildabot.knowledge_base import knowledge_base
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
        self.auto_start = config["bot"]["auto_start_game"]
        self.end_of_game_clicked = False
        self.should_run = True

        cards = [action.CARD for action in actions]
        if len(cards) != 8:
            raise WikifiedError(
                "005", f"Must provide 8 cards but {len(cards)} was given"
            )
        self.cards_to_actions = dict(zip(cards, actions))

        self.visualizer = Visualizer(**config["visuals"])
        self.emulator = Emulator(**config["adb"])
        self.detector = Detector(cards=cards)
        self.state = None
        self.play_action_delay = config.get("ingame", {}).get("play_action", 1)

        # Machine Learning components
        self.enable_ml = config.get("ml", {}).get("enabled", True)
        if self.enable_ml:
            self.data_collector = GameDataCollector(
                config.get("ml", {}).get("data_path", "game_data.json")
            )
            self.ml_bot = MLBot(
                config.get("ml", {}).get("model_path", "ml_model.pkl")
            )
            
            # Deck analysis system
            self.deck_analyzer = DeckAnalyzer(
                config.get("ml", {}).get("deck_memory_path", "deck_memory.json")
            )
            self.enemy_detector = EnemyDetector(self.deck_analyzer)
            
            self.game_started = False
            logger.info("Machine Learning and Deck Analysis system initialized")
        else:
            self.data_collector = None
            self.ml_bot = None
            self.deck_analyzer = None
            self.enemy_detector = None
            logger.info("Machine Learning disabled")

        keyboard_thread = threading.Thread(
            target=self._handle_keyboard_shortcut, daemon=True
        )
        keyboard_thread.start()

        if config["bot"]["load_deck"]:
            self.emulator.load_deck(cards)

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
        if self.state.numbers.left_enemy_princess_hp.number == 0:
            tiles += LEFT_PRINCESS_TILES
        if self.state.numbers.right_enemy_princess_hp.number == 0:
            tiles += RIGHT_PRINCESS_TILES
        return tiles

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
        screenshot = self.emulator.take_screenshot()
        self.state = self.detector.run(screenshot)
        self.visualizer.run(screenshot, self.state)
        
        # Adiciona logs para diagnosticar
        if self.state:
            logger.debug(f"State detected - Screen: {self.state.screen}")
            if hasattr(self.state, 'cards'):
                logger.debug(f"Cards detected: {len(self.state.cards) if self.state.cards else 0}")
            if hasattr(self.state, 'ready'):
                logger.debug(f"Ready cards: {self.state.ready}")
        else:
            logger.warning("No state detected from screenshot")

    def play_action(self, action):
        card_centre = self._get_card_centre(action.index)
        tile_centre = self._get_tile_centre(action.tile_x, action.tile_y)
        self.emulator.click(*card_centre)
        self.emulator.click(*tile_centre)

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
        self._handle_play_pause_in_step()
        old_screen = self.state.screen if self.state else None
        self.set_state()
        new_screen = self.state.screen
        if new_screen != old_screen:
            logger.info(f"New screen state: {new_screen}")

        if new_screen == Screens.UNKNOWN:
            self._log_and_wait("Unknown screen", 2)
            return

        if new_screen == Screens.END_OF_GAME:
            if not self.end_of_game_clicked:
                # Determina o resultado do jogo
                result = "unknown"
                if hasattr(self.state.screen, 'result'):
                    result = self.state.screen.result
                elif hasattr(self.state, 'game_result'):
                    result = self.state.game_result
                
                # Finaliza o jogo para ML
                if self.enable_ml:
                    self.end_game(result)
                    if self.deck_analyzer:
                        self.deck_analyzer.end_game(result)
                
                self.emulator.click(*self.state.screen.click_xy)
                self.end_of_game_clicked = True
                self._log_and_wait("Clicked END_OF_GAME screen", 2)
            return

        self.end_of_game_clicked = False

        if self.auto_start and new_screen == Screens.LOBBY:
            self.emulator.click(*self.state.screen.click_xy)
            self.end_of_game_clicked = False
            self._log_and_wait("Starting game", 2)
            return

        self._handle_game_step()

    def _handle_game_step(self):
        actions = self.get_actions()
        if not actions:
            # Adiciona logs para diagnosticar o problema
            logger.warning(f"No actions available. State: {self.state}")
            if hasattr(self.state, 'cards'):
                logger.warning(f"Cards detected: {len(self.state.cards) if self.state.cards else 0}")
            if hasattr(self.state, 'ready'):
                logger.warning(f"Ready cards: {self.state.ready}")
            self._log_and_wait("No actions available", self.play_action_delay)
            return

        # Iniciar coleta de dados se ML estiver ativado
        if self.enable_ml and not self.game_started:
            self.data_collector.start_new_game()
            self.deck_analyzer.start_new_game()
            self.game_started = True

        # Detectar cartas do inimigo
        if self.enable_ml and self.enemy_detector:
            self.enemy_detector.detect_enemy_cards(self.state)
        
        # Obter análise do inimigo
        enemy_analysis = None
        if self.enable_ml and self.enemy_detector:
            enemy_analysis = self.enemy_detector.get_enemy_analysis()
        
        # Usar ML para escolher a melhor ação
        best_action = None
        best_score = -float('inf')

        for action in actions:
            # Score original do bot
            original_score = action.calculate_score(self.state)
            
            # Garante que o score é um número
            if isinstance(original_score, list):
                original_score = original_score[0] if original_score else 0
            original_score = float(original_score)
            
            # Score do ML (se treinado)
            ml_score = 0.5  # Score neutro padrão
            if self.enable_ml and self.ml_bot and self.ml_bot.trained:
                ml_score = self.ml_bot.predict_action_score(self.state, action, enemy_analysis)
            
            # Bônus baseado na análise do inimigo
            enemy_bonus = 0
            if enemy_analysis:
                enemy_bonus = self.calculate_enemy_based_bonus(action, enemy_analysis)
            
            # Combina os scores (60% ML, 30% original, 10% análise inimigo se ML treinado)
            if self.enable_ml and self.ml_bot and self.ml_bot.trained:
                combined_score = 0.6 * ml_score + 0.3 * (original_score / 100) + 0.1 * enemy_bonus
            else:
                combined_score = original_score / 100 + enemy_bonus * 0.3
            
            if combined_score > best_score:
                best_score = combined_score
                best_action = action

        if best_action:
            # Executa a ação
            self.play_action(best_action)
            
            # Calcula recompensa e registra para ML
            if self.enable_ml:
                reward = self._calculate_reward(best_action)
                self.data_collector.record_action(best_action, self.state, reward)
            
            # Log da ação
            if self.enable_ml and self.ml_bot and self.ml_bot.trained:
                self._log_and_wait(
                    f"Playing {best_action} with ML score {best_score:.2f}",
                    self.play_action_delay,
                )
            else:
                self._log_and_wait(
                    f"Playing {best_action} with score {best_score:.2f}",
                    self.play_action_delay,
                )
        else:
            self._log_and_wait(
                "No good actions available", self.play_action_delay
            )

    def _calculate_reward(self, action):
        """Calcula recompensa baseada no resultado da ação"""
        reward = 0
        
        # Recompensa base da ação
        action_score = action.calculate_score(self.state)
        # Garante que o score é um número
        if isinstance(action_score, list):
            action_score = action_score[0] if action_score else 0
        action_score = float(action_score)
        reward += action_score / 100
        
        # Penalidade por usar muito elixir
        if self.state.numbers.elixir.number < 2:
            reward -= 0.3
        
        # Bônus por posicionamento defensivo
        if action.tile_y < 10:  # Lado defensivo
            reward += 0.1
        
        # Bônus por usar cartas de baixo custo quando elixir baixo
        card_cost = self.state.cards[action.index + 1].cost
        if self.state.numbers.elixir.number <= 3 and card_cost <= 3:
            reward += 0.2
        
        # Penalidade por usar cartas caras quando elixir baixo
        if self.state.numbers.elixir.number <= 2 and card_cost >= 5:
            reward -= 0.3
        
        return reward
    
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
    
    def run(self):
        try:
            while self.should_run:
                if not pause_event.is_set():
                    time.sleep(0.1)
                    continue

                self.step()
            logger.info("Thanks for using CRBAB, see you next time!")
        except KeyboardInterrupt:
            logger.info("Thanks for using CRBAB, see you next time!")

    def stop(self):
        self.should_run = False

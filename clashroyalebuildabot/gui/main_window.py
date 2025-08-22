from threading import Thread

from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget

from clashroyalebuildabot import Bot
from clashroyalebuildabot.bot.bot import pause_event
from clashroyalebuildabot.gui.animations import start_play_button_animation
from clashroyalebuildabot.gui.layout_setup import setup_tabs
from clashroyalebuildabot.gui.layout_setup import setup_top_bar
from clashroyalebuildabot.gui.styles import set_styles
from clashroyalebuildabot.utils.logger import colorize_log
from clashroyalebuildabot.utils.logger import setup_logger
from error_handling import WikifiedError


class MainWindow(QMainWindow):
    def __init__(self, config, actions):
        try:
            super().__init__()
            self.config = config
            self.actions = actions
            self.bot = None
            self.bot_thread = None
            self.is_running = False

            self.setWindowTitle(" ")
            self.setGeometry(100, 100, 900, 600)

            transparent_pixmap = QPixmap(1, 1)
            transparent_pixmap.fill(Qt.GlobalColor.transparent)
            self.setWindowIcon(QIcon(transparent_pixmap))

            main_widget = QWidget(self)
            self.setCentralWidget(main_widget)
            main_layout = QVBoxLayout(main_widget)

            top_bar = setup_top_bar(self)
            tab_widget = setup_tabs(self)

            main_layout.addWidget(top_bar)
            main_layout.addWidget(tab_widget)

            set_styles(self)
            start_play_button_animation(self)
        except Exception as e:
            raise WikifiedError("004", "Error in GUI initialization.") from e

    def log_handler_function(self, message):
        formatted_message = colorize_log(message)
        self.log_display.append(formatted_message)
        QApplication.processEvents()
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )

    def toggle_start_stop(self):
        if self.is_running:
            self.stop_bot()
            self.glow_animation.start()
        else:
            self.start_bot()
            self.glow_animation.stop()

    def toggle_pause_resume_and_display(self):
        if not self.bot:
            return
        if pause_event.is_set():
            self.play_pause_button.setText("▶")
        else:
            self.play_pause_button.setText("⏸️")
        self.bot.pause_or_resume()

    def start_bot(self):
        if self.is_running:
            return
        self.update_config()
        self.is_running = True
        self.bot_thread = Thread(target=self.bot_task)
        self.bot_thread.daemon = False  # Mudado para False para evitar terminação prematura
        self.bot_thread.start()
        logger.debug(f"Bot thread started - daemon: {self.bot_thread.daemon}, alive: {self.bot_thread.is_alive()}")
        self.start_stop_button.setText("■")
        self.play_pause_button.show()
        self.server_id_label.setText("Status - Running")
        logger.info("Starting bot")
        
        # Inicia monitoramento do thread
        self._start_thread_monitor()

    def stop_bot(self):
        logger.info("Stopping bot...")
        if self.bot:
            self.bot.stop()
            logger.debug("Bot.stop() called")
        
        self.is_running = False
        
        # Aguarda thread terminar se ainda está vivo
        if self.bot_thread and self.bot_thread.is_alive():
            logger.debug("Waiting for bot thread to finish...")
            self.bot_thread.join(timeout=5)  # Aguarda até 5 segundos
            if self.bot_thread.is_alive():
                logger.warning("Bot thread still alive after timeout")
            else:
                logger.debug("Bot thread finished successfully")
        
        self.start_stop_button.setText("▶")
        self.play_pause_button.hide()
        self.server_id_label.setText("Status - Stopped")
        logger.info("Bot stopped")

    def restart_bot(self):
        if self.is_running:
            self.stop_bot()
        self.update_config()
        self.start_bot()

    def update_config(self) -> dict:
        self.config["visuals"][
            "save_labels"
        ] = self.save_labels_checkbox.isChecked()
        self.config["visuals"][
            "save_images"
        ] = self.save_images_checkbox.isChecked()
        self.config["visuals"][
            "show_images"
        ] = self.show_images_checkbox.isChecked()
        self.visualize_tab.update_active_state(
            self.config["visuals"]["show_images"]
        )
        self.config["bot"]["load_deck"] = self.load_deck_checkbox.isChecked()
        self.config["bot"][
            "auto_start_game"
        ] = self.auto_start_game_checkbox.isChecked()
        log_level_changed = (
            self.config["bot"]["log_level"]
            != self.log_level_dropdown.currentText()
        )
        self.config["bot"]["log_level"] = self.log_level_dropdown.currentText()
        if log_level_changed:
            setup_logger(self, self.config)
        self.config["ingame"]["play_action"] = round(
            float(self.play_action_delay_input.value()), 2
        )
        self.config["adb"]["ip"] = self.adb_ip_input.text()
        self.config["adb"]["device_serial"] = self.device_serial_input.text()
        return self.config

    def bot_task(self):
        try:
            logger.info("Bot task starting - creating Bot instance")
            self.bot = Bot(actions=self.actions, config=self.config)
            logger.info("Bot instance created successfully")
            
            # Conectar visualizer com tratamento de erro
            try:
                if hasattr(self.bot.visualizer, 'frame_ready'):
                    self.bot.visualizer.frame_ready.connect(
                        self.visualize_tab.update_frame
                    )
                    logger.debug("Visualizer connected successfully")
            except Exception as viz_error:
                logger.warning(f"Visualizer connection failed: {viz_error}")
                # Continua sem visualizer
            
            logger.info("Starting bot.run() in GUI thread")
            
            # Verificar se bot ainda deve executar antes de iniciar
            if not self.bot.should_run:
                logger.warning("Bot should_run is False before starting run()")
                return
            
            # Executar com captura detalhada de erros
            try:
                logger.debug("About to call bot.run()")
                self.bot.run()
                logger.info("Bot.run() completed normally")
            except Exception as run_error:
                logger.error(f"CRITICAL: bot.run() failed: {run_error}")
                import traceback
                logger.error(f"bot.run() traceback: {traceback.format_exc()}")
                raise  # Re-raise para tratamento externo
            
            logger.info("Stopping bot after normal completion")
            self.stop_bot()
        except WikifiedError as we:
            logger.error(f"WikifiedError in bot task: {we}")
            self.stop_bot()
            raise
        except Exception as e:
            logger.error(f"Error in bot task: {e}")
            import traceback
            logger.error(f"Bot task traceback: {traceback.format_exc()}")
            # Não re-levanta a exceção, apenas para o bot
            self.stop_bot()
            # Log da mensagem de erro na interface
            self.append_log(f"❌ Bot error: {str(e)}")
            self.append_log("🔄 Bot stopped due to error. You can restart it.")

    def _start_thread_monitor(self):
        """Monitora o thread do bot para detectar quando ele termina"""
        def monitor():
            import time
            start_time = time.time()
            last_check = time.time()
            
            while self.is_running and self.bot_thread:
                current_time = time.time()
                elapsed = current_time - start_time
                
                if not self.bot_thread.is_alive():
                    logger.warning(f"Bot thread died after {elapsed:.1f} seconds!")
                    self.append_log(f"⚠️ Bot thread terminated after {elapsed:.1f}s")
                    
                    # Verificar se o bot ainda existe e qual é o estado
                    if hasattr(self, 'bot') and self.bot:
                        logger.debug(f"Bot should_run: {self.bot.should_run}")
                    
                    self.stop_bot()
                    break
                
                # Log periódico para monitoramento
                if current_time - last_check > 10:  # A cada 10 segundos
                    logger.debug(f"Thread monitor: Bot running for {elapsed:.1f}s, thread alive: {self.bot_thread.is_alive()}")
                    last_check = current_time
                
                time.sleep(2)
        
        monitor_thread = Thread(target=monitor, daemon=True)
        monitor_thread.start()
        logger.debug("Enhanced thread monitor started")

    def append_log(self, message):
        self.log_display.append(message)

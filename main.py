from error_handling import WikifiedError

try:
    import signal
    import sys

    from loguru import logger
    from PyQt6.QtWidgets import QApplication

    from clashroyalebuildabot.actions import ArchersAction
    from clashroyalebuildabot.actions import FireballAction
    from clashroyalebuildabot.actions import GiantAction
    from clashroyalebuildabot.actions import KnightAction
    from clashroyalebuildabot.actions import MinionsAction
    from clashroyalebuildabot.actions import MinipekkaAction
    from clashroyalebuildabot.actions import MusketeerAction
    from clashroyalebuildabot.actions import SpearGoblinsAction
    from clashroyalebuildabot.gui.main_window import MainWindow
    from clashroyalebuildabot.gui.utils import load_config
    from clashroyalebuildabot.utils.git_utils import check_and_pull_updates
except Exception as e:
    raise WikifiedError("001", "Missing imports.") from e


def main():
    try:
        check_and_pull_updates()
        logger.debug("Git updates checked")
    except Exception as git_error:
        logger.warning(f"Git update check failed: {git_error}")
        # Continua sem updates
    
    actions = [
        # Deck real do usuário
        ArchersAction,        # Arqueira - Defesa aérea
        KnightAction,         # Cavaleiro - Defesa terrestre
        MinipekkaAction,      # Mini Pekka - Dano terrestre
        MusketeerAction,      # Mosqueteira - Dano aéreo
        MinionsAction,        # Servos - Ataque aéreo
        FireballAction,       # Bola de Fogo - Feitiço de dano
        SpearGoblinsAction,   # Goblins Lanceiros - Defesa barata
        GiantAction,          # Gigante - Tanque principal
    ]
    try:
        config = load_config()

        app = QApplication([])
        logger.info("QApplication created")
        
        window = MainWindow(config, actions)
        logger.info("MainWindow created")
        
        # Configurar logger igual ao main_stable.py que funciona
        logger.remove()
        logger.add(sys.stderr, level="INFO", 
                  format="{time:HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}")
        
        logger.info("Using stable logger configuration")

        window.show()
        logger.info("Window shown, starting Qt event loop")
        
        exit_code = app.exec()
        logger.info(f"Qt event loop ended with code: {exit_code}")
        sys.exit(exit_code)
    except WikifiedError as we:
        logger.error(f"WikifiedError occurred: {we}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred in main loop: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

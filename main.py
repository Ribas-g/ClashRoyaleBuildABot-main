from error_handling import WikifiedError

try:
    import signal
    import sys

    from loguru import logger
    from PyQt6.QtWidgets import QApplication

    from clashroyalebuildabot.actions import ArchersAction
    from clashroyalebuildabot.actions import BabyDragonAction
    from clashroyalebuildabot.actions import FireballAction
    from clashroyalebuildabot.actions import GiantAction
    from clashroyalebuildabot.actions import KnightAction
    from clashroyalebuildabot.actions import MusketeerAction
    from clashroyalebuildabot.actions import WitchAction
    from clashroyalebuildabot.actions import ZapAction
    from clashroyalebuildabot.gui.main_window import MainWindow
    from clashroyalebuildabot.gui.utils import load_config
    from clashroyalebuildabot.utils.git_utils import check_and_pull_updates
    from clashroyalebuildabot.utils.logger import setup_logger
except Exception as e:
    raise WikifiedError("001", "Missing imports.") from e


def main():
    check_and_pull_updates()
    actions = [
        # Deck otimizado para melhor desempenho
        GiantAction,          # Tanque principal
        MusketeerAction,      # Dano aéreo
        WitchAction,          # Suporte e defesa
        BabyDragonAction,     # Ataque aéreo
        KnightAction,         # Defesa terrestre
        ArchersAction,        # Defesa aérea
        FireballAction,       # Feitiço de dano
        ZapAction,            # Feitiço rápido
    ]
    try:
        config = load_config()

        app = QApplication([])
        window = MainWindow(config, actions)
        setup_logger(window, config)

        window.show()
        sys.exit(app.exec())
    except WikifiedError:
        raise
    except Exception as e:
        logger.error(f"An error occurred in main loop: {e}")
        sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

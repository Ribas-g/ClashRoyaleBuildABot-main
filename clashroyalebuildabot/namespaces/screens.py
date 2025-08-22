from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Screen:
    name: str
    ltrb: Optional[Tuple[float, float, float, float]]
    click_xy: Optional[Tuple[int, int]]


# coords are scaled to 720x1280
@dataclass(frozen=True)
class _ScreensNamespace:
    UNKNOWN: Screen = Screen("unknown", None, None)
    IN_GAME: Screen = Screen("in_game", (148, 1254, 163, 1274), None)
    LOBBY: Screen = Screen(
        "lobby",
        (424, 126, 506, 181),
        (360, 990),
    )
    END_OF_GAME: Screen = Screen(
        "end_of_game",
        (200, 300, 520, 800),    # Região ampla para capturar coroas, banners e botões
        (250, 1140),             # Coordenada correta do botão "Jogar de NOVO"
    )


Screens = _ScreensNamespace()

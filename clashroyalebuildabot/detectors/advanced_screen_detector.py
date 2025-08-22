#!/usr/bin/env python3
"""
Advanced Screen Detector
Baseado nos projetos py-clash-bot e bot_Clash_Royale
Implementa detecção robusta de telas usando múltiplas técnicas
"""
import os
import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple, Dict, List
from loguru import logger

from clashroyalebuildabot.constants import IMAGES_DIR
from clashroyalebuildabot.namespaces import Screens
from clashroyalebuildabot.namespaces.screens import Screen


class AdvancedScreenDetector:
    def __init__(self, hash_size=8, threshold=30):
        self.hash_size = hash_size
        self.threshold = threshold
        self.screen_hashes = self._calculate_screen_hashes()
        
        # Configurações para detecção de cores específicas
        self.color_ranges = {
            'crown_gold': {
                'lower': np.array([20, 100, 100]),   # Dourado das coroas
                'upper': np.array([30, 255, 255])
            },
            'victory_blue': {
                'lower': np.array([100, 100, 100]),  # Azul do banner inferior
                'upper': np.array([130, 255, 255])
            },
            'defeat_red': {
                'lower': np.array([0, 100, 100]),    # Vermelho do banner superior
                'upper': np.array([10, 255, 255])
            },
            'button_yellow': {
                'lower': np.array([15, 100, 100]),   # Amarelo/Laranja do botão "Jogar de NOVO"
                'upper': np.array([35, 255, 255])
            },
            'button_blue': {
                'lower': np.array([100, 100, 100]),  # Azul do botão "OK"
                'upper': np.array([130, 255, 255])
            }
        }
        
        # Regiões de interesse para detecção
        self.roi_regions = {
            'crown_area': (250, 350, 470, 450),      # Área das coroas (mais centralizada)
            'result_text': (200, 250, 520, 350),     # Área do texto "Vencedor!" 
            'play_again_button': (150, 600, 350, 700), # Área do botão "Jogar de NOVO" (esquerda)
            'ok_button': (370, 600, 570, 700),       # Área do botão "OK" (direita)
            'battle_button': (300, 750, 420, 850),   # Área do botão de batalha
        }
        
        # Padrões de texto para OCR (simplificado)
        self.text_patterns = {
            'victory': ['victory', 'win', 'won', 'vitória'],
            'defeat': ['defeat', 'lose', 'lost', 'derrota'],
            'draw': ['draw', 'tie', 'empate'],
            'play_again': ['play again', 'jogar de novo', 'battle', 'batalha']
        }

    def _image_hash(self, image):
        """Calcula hash da imagem para comparação"""
        try:
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            
            crop = image.resize(
                (self.hash_size, self.hash_size), Image.Resampling.BILINEAR
            )
            hash_ = np.array(crop, dtype=np.float32).flatten()
            return hash_
        except Exception as e:
            logger.debug(f"Error calculating image hash: {e}")
            return None

    def _calculate_screen_hashes(self):
        """Calcula hashes das telas de referência"""
        screen_hashes = {}
        try:
            for screen in Screens.__dict__.values():
                if screen.ltrb is None:
                    continue
                path = os.path.join(IMAGES_DIR, "screen", f"{screen.name}.jpg")
                if os.path.exists(path):
                    image = Image.open(path)
                    screen_hashes[screen] = self._image_hash(image)
        except Exception as e:
            logger.warning(f"Error loading screen hashes: {e}")
        return screen_hashes

    def _detect_colors(self, image: np.ndarray) -> Dict[str, float]:
        """Detecta cores específicas na imagem"""
        try:
            # Converter para HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            color_scores = {}
            for color_name, color_range in self.color_ranges.items():
                # Criar máscara para a cor
                mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
                
                # Calcular porcentagem da cor na imagem
                total_pixels = mask.shape[0] * mask.shape[1]
                colored_pixels = cv2.countNonZero(mask)
                percentage = colored_pixels / total_pixels
                
                color_scores[color_name] = percentage
            
            return color_scores
        except Exception as e:
            logger.debug(f"Error detecting colors: {e}")
            return {}

    def _detect_text_patterns(self, image: np.ndarray) -> Dict[str, float]:
        """Detecta padrões de texto usando template matching simplificado"""
        try:
            # Converter para escala de cinza
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            text_scores = {}
            
            # Verificar regiões de interesse
            for region_name, (x1, y1, x2, y2) in self.roi_regions.items():
                roi = gray[y1:y2, x1:x2]
                
                # Detectar bordas (simula detecção de texto)
                edges = cv2.Canny(roi, 50, 150)
                edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
                
                text_scores[region_name] = edge_density
            
            return text_scores
        except Exception as e:
            logger.debug(f"Error detecting text patterns: {e}")
            return {}

    def _detect_play_again_button(self, image: np.ndarray) -> bool:
        """Detecta especificamente o botão 'jogar de novo'"""
        try:
            # Região do botão jogar de novo
            x1, y1, x2, y2 = self.roi_regions['play_again_button']
            button_roi = image[y1:y2, x1:x2]
            
            # Detectar cores características do botão
            hsv = cv2.cvtColor(button_roi, cv2.COLOR_RGB2HSV)
            
            # Amarelo/Laranja do botão "Jogar de NOVO"
            yellow_lower = np.array([15, 100, 100])
            yellow_upper = np.array([35, 255, 255])
            yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
            
            # Verde do botão (fallback)
            green_lower = np.array([40, 100, 100])
            green_upper = np.array([80, 255, 255])
            green_mask = cv2.inRange(hsv, green_lower, green_upper)
            
            # Azul do botão (fallback)
            blue_lower = np.array([100, 100, 100])
            blue_upper = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
            
            # Calcular porcentagem de pixels coloridos
            total_pixels = yellow_mask.shape[0] * yellow_mask.shape[1]
            yellow_pixels = cv2.countNonZero(yellow_mask)
            green_pixels = cv2.countNonZero(green_mask)
            blue_pixels = cv2.countNonZero(blue_mask)
            
            yellow_percentage = yellow_pixels / total_pixels
            green_percentage = green_pixels / total_pixels
            blue_percentage = blue_pixels / total_pixels
            
            # Se há uma porcentagem significativa de amarelo, verde ou azul, é provavelmente um botão
            # Reduzir threshold para amarelo (botão "Jogar de NOVO")
            return yellow_percentage > 0.15 or green_percentage > 0.25 or blue_percentage > 0.25
            
        except Exception as e:
            logger.debug(f"Error detecting play again button: {e}")
            return False

    def _detect_crowns(self, image: np.ndarray) -> bool:
        """Detecta coroas na tela de resultado"""
        try:
            # Região das coroas
            x1, y1, x2, y2 = self.roi_regions['crown_area']
            crown_roi = image[y1:y2, x1:x2]
            
            # Detectar cor dourada das coroas
            hsv = cv2.cvtColor(crown_roi, cv2.COLOR_RGB2HSV)
            gold_mask = cv2.inRange(hsv, self.color_ranges['crown_gold']['lower'], 
                                  self.color_ranges['crown_gold']['upper'])
            
            # Calcular porcentagem de pixels dourados
            total_pixels = gold_mask.shape[0] * gold_mask.shape[1]
            gold_pixels = cv2.countNonZero(gold_mask)
            gold_percentage = gold_pixels / total_pixels
            
            return gold_percentage > 0.10  # 10% de pixels dourados indica coroas (mais flexível)
            
        except Exception as e:
            logger.debug(f"Error detecting crowns: {e}")
            return False

    def _detect_post_game_buttons(self, image: np.ndarray) -> bool:
        """Detecta botões específicos da tela de pós-jogo"""
        try:
            # Verificar botão "Jogar de NOVO" (amarelo)
            x1, y1, x2, y2 = self.roi_regions['play_again_button']
            play_again_roi = image[y1:y2, x1:x2]
            
            # Verificar botão "OK" (azul)
            x1_ok, y1_ok, x2_ok, y2_ok = self.roi_regions['ok_button']
            ok_roi = image[y1_ok:y2_ok, x1_ok:x2_ok]
            
            # Detectar cores
            hsv_play = cv2.cvtColor(play_again_roi, cv2.COLOR_RGB2HSV)
            hsv_ok = cv2.cvtColor(ok_roi, cv2.COLOR_RGB2HSV)
            
            # Máscaras para amarelo e azul
            yellow_mask = cv2.inRange(hsv_play, self.color_ranges['button_yellow']['lower'], 
                                    self.color_ranges['button_yellow']['upper'])
            blue_mask = cv2.inRange(hsv_ok, self.color_ranges['button_blue']['lower'], 
                                  self.color_ranges['button_blue']['upper'])
            
            # Calcular porcentagens
            total_play = yellow_mask.shape[0] * yellow_mask.shape[1]
            total_ok = blue_mask.shape[0] * blue_mask.shape[1]
            
            yellow_percentage = cv2.countNonZero(yellow_mask) / total_play
            blue_percentage = cv2.countNonZero(blue_mask) / total_ok
            
            # Se ambos os botões estão presentes, é definitivamente tela de pós-jogo
            return yellow_percentage > 0.10 and blue_percentage > 0.10
            
        except Exception as e:
            logger.debug(f"Error detecting post-game buttons: {e}")
            return False

    def _is_result_screen(self, image: np.ndarray) -> bool:
        """Determina se é uma tela de resultado"""
        try:
            # Verificar se há coroas
            has_crowns = self._detect_crowns(image)
            
            # Verificar se há botão jogar de novo
            has_play_again = self._detect_play_again_button(image)
            
            # Verificar se há botões específicos da tela de pós-jogo
            has_post_game_buttons = self._detect_post_game_buttons(image)
            
            # Verificar cores de resultado
            color_scores = self._detect_colors(image)
            has_result_colors = (
                color_scores.get('crown_gold', 0) > 0.08 or
                color_scores.get('victory_blue', 0) > 0.08 or
                color_scores.get('defeat_red', 0) > 0.08 or
                color_scores.get('button_yellow', 0) > 0.05 or
                color_scores.get('button_blue', 0) > 0.05
            )
            
            # Verificar se há indicadores de jogo ativo (para evitar falsos positivos)
            has_game_indicators = self._has_game_indicators(image)
            
            # Se tem indicadores de jogo, ser mais rigoroso
            if has_game_indicators:
                logger.debug("Game indicators detected, requiring stronger result screen evidence")
                # Exigir pelo menos 3 indicadores quando há sinais de jogo
                indicators = [has_crowns, has_play_again, has_post_game_buttons, has_result_colors]
                return sum(indicators) >= 3
            else:
                # Se não há indicadores de jogo, pode ser mais flexível
                indicators = [has_crowns, has_play_again, has_post_game_buttons, has_result_colors]
                return sum(indicators) >= 2
            
        except Exception as e:
            logger.debug(f"Error detecting result screen: {e}")
            return False

    def _has_game_indicators(self, image: np.ndarray) -> bool:
        """Verifica se há indicadores de que está em jogo ativo"""
        try:
            # Verificar área de elixir (parte inferior da tela)
            elixir_area = image[1200:1280, 300:420]  # Área aproximada do elixir
            hsv_elixir = cv2.cvtColor(elixir_area, cv2.COLOR_RGB2HSV)
            
            # Detectar cor azul do elixir
            blue_lower = np.array([100, 100, 100])
            blue_upper = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv_elixir, blue_lower, blue_upper)
            
            blue_percentage = cv2.countNonZero(blue_mask) / (blue_mask.shape[0] * blue_mask.shape[1])
            
            # Se há elixir visível, provavelmente está em jogo
            if blue_percentage > 0.03:  # 3% de azul indica elixir
                logger.debug(f"Game indicator: elixir detected ({blue_percentage:.3f})")
                return True
            
            # Verificar área de cartas (parte inferior da tela)
            cards_area = image[1100:1280, 50:670]  # Área aproximada das cartas
            hsv_cards = cv2.cvtColor(cards_area, cv2.COLOR_RGB2HSV)
            
            # Detectar cores características das cartas (tons de marrom/cinza)
            brown_lower = np.array([10, 50, 50])
            brown_upper = np.array([20, 200, 200])
            brown_mask = cv2.inRange(hsv_cards, brown_lower, brown_upper)
            
            brown_percentage = cv2.countNonZero(brown_mask) / (brown_mask.shape[0] * brown_mask.shape[1])
            
            # Se há muitas áreas marrons/cinzas, provavelmente são cartas
            if brown_percentage > 0.1:  # 10% de marrom indica cartas
                logger.debug(f"Game indicator: cards detected ({brown_percentage:.3f})")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking game indicators: {e}")
            return False

    def run(self, image: Image) -> Screen:
        """Detecta a tela atual usando múltiplas técnicas"""
        try:
            # Converter PIL para numpy array
            if isinstance(image, Image.Image):
                image_array = np.array(image)
            else:
                image_array = image
            
            # Primeiro, tentar detecção tradicional por hash
            current_screen = self._detect_by_hash(image)
            
            # Se não conseguiu detectar, usar técnicas avançadas
            if current_screen.name == 'unknown':
                current_screen = self._detect_advanced(image_array)
            
            return current_screen
            
        except Exception as e:
            logger.error(f"Error in advanced screen detection: {e}")
            return Screens.UNKNOWN

    def _detect_by_hash(self, image: Image) -> Screen:
        """Detecção tradicional por hash"""
        try:
            current_screen = Screens.UNKNOWN
            best_diff = self.threshold

            for screen in Screens.__dict__.values():
                if screen.ltrb is None or screen not in self.screen_hashes:
                    continue
                
                # Escalar coordenadas para o tamanho da imagem
                treated_ltrb = (
                    int(screen.ltrb[0] * image.size[0] / 720),
                    int(screen.ltrb[1] * image.size[1] / 1280),
                    int(screen.ltrb[2] * image.size[0] / 720),
                    int(screen.ltrb[3] * image.size[1] / 1280),
                )
                
                try:
                    hash_ = self._image_hash(image.crop(treated_ltrb))
                    target_hash = self.screen_hashes[screen]
                    
                    if hash_ is not None and target_hash is not None:
                        diff = np.mean(np.abs(hash_ - target_hash))
                        if diff < best_diff:
                            best_diff = diff
                            current_screen = screen
                except Exception as e:
                    logger.debug(f"Error comparing hash for {screen.name}: {e}")
                    continue

            return current_screen
            
        except Exception as e:
            logger.debug(f"Error in hash detection: {e}")
            return Screens.UNKNOWN

    def _detect_advanced(self, image: np.ndarray) -> Screen:
        """Detecção avançada usando múltiplas técnicas"""
        try:
            # Verificar se é uma tela de resultado
            if self._is_result_screen(image):
                # Criar uma tela de resultado personalizada
                return Screen(
                    name="end_of_game",
                    ltrb=(200, 300, 520, 800),
                    click_xy=(250, 1140)  # Coordenada correta do botão "Jogar de NOVO"
                )
            
            # Verificar se é lobby (botão de batalha)
            x1, y1, x2, y2 = self.roi_regions['battle_button']
            battle_roi = image[y1:y2, x1:x2]
            
            # Detectar botão verde de batalha
            hsv = cv2.cvtColor(battle_roi, cv2.COLOR_RGB2HSV)
            green_lower = np.array([40, 100, 100])
            green_upper = np.array([80, 255, 255])
            green_mask = cv2.inRange(hsv, green_lower, green_upper)
            
            green_percentage = cv2.countNonZero(green_mask) / (green_mask.shape[0] * green_mask.shape[1])
            
            if green_percentage > 0.1:  # 10% de verde indica botão de batalha
                return Screens.LOBBY
            
            # Verificar se está no jogo (área de elixir)
            elixir_area = image[1200:1280, 300:420]  # Área aproximada do elixir
            hsv_elixir = cv2.cvtColor(elixir_area, cv2.COLOR_RGB2HSV)
            
            # Detectar cor azul do elixir
            blue_lower = np.array([100, 100, 100])
            blue_upper = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv_elixir, blue_lower, blue_upper)
            
            blue_percentage = cv2.countNonZero(blue_mask) / (blue_mask.shape[0] * blue_mask.shape[1])
            
            if blue_percentage > 0.05:  # 5% de azul indica área de elixir
                return Screens.IN_GAME
            
            return Screens.UNKNOWN
            
        except Exception as e:
            logger.debug(f"Error in advanced detection: {e}")
            return Screens.UNKNOWN

    def get_screen_info(self, image: Image) -> Dict:
        """Retorna informações detalhadas sobre a detecção"""
        try:
            image_array = np.array(image) if isinstance(image, Image.Image) else image
            
            info = {
                'hash_detection': self._detect_by_hash(image).name,
                'advanced_detection': self._detect_advanced(image_array).name,
                'has_crowns': self._detect_crowns(image_array),
                'has_play_again': self._detect_play_again_button(image_array),
                'has_post_game_buttons': self._detect_post_game_buttons(image_array),
                'is_result_screen': self._is_result_screen(image_array),
                'color_scores': self._detect_colors(image_array),
                'text_scores': self._detect_text_patterns(image_array)
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting screen info: {e}")
            return {'error': str(e)}

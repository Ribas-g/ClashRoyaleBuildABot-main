"""
Sistema de Detecção Avançada
Baseado em técnicas do py-clash-bot para detecção robusta
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from loguru import logger
import os


class AdvancedDetector:
    def __init__(self):
        self.templates = {}
        self.unit_templates = {}
        self.building_templates = {}
        self.card_templates = {}
        
        # Configurações de detecção
        self.confidence_threshold = 0.7
        self.max_detections = 10
        
        # Carregar templates
        self._load_templates()
    
    def _load_templates(self):
        """Carrega templates de detecção"""
        try:
            # Diretórios de templates
            template_dirs = {
                'units': 'templates/units',
                'buildings': 'templates/buildings', 
                'cards': 'templates/cards',
                'ui': 'templates/ui'
            }
            
            for category, dir_path in template_dirs.items():
                if os.path.exists(dir_path):
                    for file in os.listdir(dir_path):
                        if file.endswith(('.png', '.jpg')):
                            template_name = file.split('.')[0]
                            template_path = os.path.join(dir_path, file)
                            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                            
                            if template is not None:
                                if category == 'units':
                                    self.unit_templates[template_name] = template
                                elif category == 'buildings':
                                    self.building_templates[template_name] = template
                                elif category == 'cards':
                                    self.card_templates[template_name] = template
                                else:
                                    self.templates[template_name] = template
                                    
            logger.info(f"Loaded {len(self.unit_templates)} unit templates, {len(self.building_templates)} building templates")
            
        except Exception as e:
            logger.warning(f"Could not load templates: {e}")
    
    def detect_units_on_field(self, frame: np.ndarray) -> List[Dict]:
        """Detecta unidades no campo de batalha"""
        detections = []
        
        try:
            # Converter para HSV para melhor detecção
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Detectar por cor (diferentes para aliados e inimigos)
            ally_detections = self._detect_by_color(hsv, 'ally')
            enemy_detections = self._detect_by_color(hsv, 'enemy')
            
            # Detectar por template matching
            template_detections = self._detect_by_templates(frame)
            
            # Combinar detecções
            all_detections = ally_detections + enemy_detections + template_detections
            
            # Filtrar duplicatas e baixa confiança
            filtered_detections = self._filter_detections(all_detections)
            
            # Classificar unidades
            for detection in filtered_detections:
                unit_type = self._classify_unit(frame, detection)
                detection['unit_type'] = unit_type
                detections.append(detection)
            
            logger.debug(f"Detected {len(detections)} units on field")
            
        except Exception as e:
            logger.error(f"Error detecting units: {e}")
        
        return detections
    
    def _detect_by_color(self, hsv: np.ndarray, team: str) -> List[Dict]:
        """Detecta unidades por cor (azul para aliados, vermelho para inimigos)"""
        detections = []
        
        try:
            if team == 'ally':
                # Azul para aliados
                lower = np.array([100, 50, 50])
                upper = np.array([130, 255, 255])
            else:
                # Vermelho para inimigos
                lower1 = np.array([0, 50, 50])
                upper1 = np.array([10, 255, 255])
                lower2 = np.array([170, 50, 50])
                upper2 = np.array([180, 255, 255])
                
                mask1 = cv2.inRange(hsv, lower1, upper1)
                mask2 = cv2.inRange(hsv, lower2, upper2)
                mask = mask1 + mask2
                
                # Encontrar contornos
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 100:  # Filtrar ruído
                        x, y, w, h = cv2.boundingRect(contour)
                        detections.append({
                            'x': x + w//2,
                            'y': y + h//2,
                            'width': w,
                            'height': h,
                            'confidence': 0.8,
                            'team': team,
                            'area': area
                        })
                
                return detections
            
            # Para aliados (azul)
            mask = cv2.inRange(hsv, lower, upper)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:
                    x, y, w, h = cv2.boundingRect(contour)
                    detections.append({
                        'x': x + w//2,
                        'y': y + h//2,
                        'width': w,
                        'height': h,
                        'confidence': 0.8,
                        'team': team,
                        'area': area
                    })
            
        except Exception as e:
            logger.error(f"Error in color detection: {e}")
        
        return detections
    
    def _detect_by_templates(self, frame: np.ndarray) -> List[Dict]:
        """Detecta unidades usando template matching"""
        detections = []
        
        try:
            for unit_name, template in self.unit_templates.items():
                # Template matching
                result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= self.confidence_threshold)
                
                for pt in zip(*locations[::-1]):
                    h, w = template.shape[:2]
                    detections.append({
                        'x': pt[0] + w//2,
                        'y': pt[1] + h//2,
                        'width': w,
                        'height': h,
                        'confidence': result[pt[1], pt[0]],
                        'unit_name': unit_name,
                        'detection_method': 'template'
                    })
            
        except Exception as e:
            logger.error(f"Error in template detection: {e}")
        
        return detections
    
    def _filter_detections(self, detections: List[Dict]) -> List[Dict]:
        """Filtra detecções duplicadas e de baixa confiança"""
        filtered = []
        
        try:
            # Ordenar por confiança
            detections.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            for detection in detections:
                # Verificar se já existe detecção próxima
                is_duplicate = False
                for existing in filtered:
                    distance = np.sqrt(
                        (detection['x'] - existing['x'])**2 + 
                        (detection['y'] - existing['y'])**2
                    )
                    if distance < 30:  # 30 pixels de tolerância
                        is_duplicate = True
                        break
                
                if not is_duplicate and detection.get('confidence', 0) >= self.confidence_threshold:
                    filtered.append(detection)
                
                if len(filtered) >= self.max_detections:
                    break
            
        except Exception as e:
            logger.error(f"Error filtering detections: {e}")
        
        return filtered
    
    def _classify_unit(self, frame: np.ndarray, detection: Dict) -> str:
        """Classifica o tipo de unidade baseado em características"""
        try:
            x, y = detection['x'], detection['y']
            w, h = detection['width'], detection['height']
            
            # Extrair região da unidade
            unit_region = frame[max(0, y-h//2):min(frame.shape[0], y+h//2),
                               max(0, x-w//2):min(frame.shape[1], x+w//2)]
            
            if unit_region.size == 0:
                return 'unknown'
            
            # Análise de características
            area = w * h
            aspect_ratio = w / h if h > 0 else 1
            
            # Classificação baseada em tamanho e proporção
            if area > 2000:
                if aspect_ratio > 1.5:
                    return 'giant'  # Unidades grandes e largas
                else:
                    return 'tank'   # Unidades grandes e quadradas
            elif area > 1000:
                if aspect_ratio < 0.8:
                    return 'ranged'  # Unidades médias e altas
                else:
                    return 'melee'   # Unidades médias e largas
            else:
                return 'small'       # Unidades pequenas
            
        except Exception as e:
            logger.error(f"Error classifying unit: {e}")
            return 'unknown'
    
    def detect_buildings(self, frame: np.ndarray) -> List[Dict]:
        """Detecta construções no campo"""
        detections = []
        
        try:
            # Detectar por templates de construções
            for building_name, template in self.building_templates.items():
                result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= self.confidence_threshold)
                
                for pt in zip(*locations[::-1]):
                    h, w = template.shape[:2]
                    detections.append({
                        'x': pt[0] + w//2,
                        'y': pt[1] + h//2,
                        'width': w,
                        'height': h,
                        'confidence': result[pt[1], pt[0]],
                        'building_type': building_name
                    })
            
            logger.debug(f"Detected {len(detections)} buildings")
            
        except Exception as e:
            logger.error(f"Error detecting buildings: {e}")
        
        return detections
    
    def detect_cards_in_hand(self, frame: np.ndarray) -> List[Dict]:
        """Detecta cartas na mão do jogador"""
        detections = []
        
        try:
            # Região da mão (parte inferior da tela)
            hand_region = frame[frame.shape[0]//2:, :]
            
            # Detectar por templates de cartas
            for card_name, template in self.card_templates.items():
                result = cv2.matchTemplate(hand_region, template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= self.confidence_threshold)
                
                for pt in zip(*locations[::-1]):
                    h, w = template.shape[:2]
                    # Ajustar coordenadas para a tela completa
                    screen_x = pt[0] + w//2
                    screen_y = pt[1] + h//2 + frame.shape[0]//2
                    
                    detections.append({
                        'x': screen_x,
                        'y': screen_y,
                        'width': w,
                        'height': h,
                        'confidence': result[pt[1], pt[0]],
                        'card_name': card_name,
                        'slot_index': self._get_card_slot_index(screen_x)
                    })
            
            logger.debug(f"Detected {len(detections)} cards in hand")
            
        except Exception as e:
            logger.error(f"Error detecting cards: {e}")
        
        return detections
    
    def _get_card_slot_index(self, x: int) -> int:
        """Determina o índice do slot da carta baseado na posição X"""
        # Assumindo 4 slots de cartas
        slot_width = 200  # Largura aproximada de cada slot
        return min(3, max(0, int(x // slot_width)))
    
    def detect_elixir(self, frame: np.ndarray) -> float:
        """Detecta o nível de elixir atual"""
        try:
            # Região do elixir (canto superior esquerdo)
            elixir_region = frame[50:100, 50:150]
            
            # Converter para HSV
            hsv = cv2.cvtColor(elixir_region, cv2.COLOR_BGR2HSV)
            
            # Detectar cor do elixir (roxo/rosa)
            lower_purple = np.array([130, 50, 50])
            upper_purple = np.array([170, 255, 255])
            
            mask = cv2.inRange(hsv, lower_purple, upper_purple)
            
            # Contar pixels do elixir
            elixir_pixels = cv2.countNonZero(mask)
            total_pixels = mask.shape[0] * mask.shape[1]
            
            # Calcular porcentagem de elixir
            elixir_percentage = elixir_pixels / total_pixels
            
            # Converter para valor de elixir (0-10)
            elixir_value = min(10.0, elixir_percentage * 20)  # Ajustar multiplicador conforme necessário
            
            return elixir_value
            
        except Exception as e:
            logger.error(f"Error detecting elixir: {e}")
            return 0.0
    
    def detect_tower_health(self, frame: np.ndarray) -> Dict[str, float]:
        """Detecta a vida das torres"""
        try:
            health_values = {}
            
            # Regiões das torres
            tower_regions = {
                'ally_left': frame[100:200, 50:150],
                'ally_right': frame[100:200, frame.shape[1]-150:frame.shape[1]-50],
                'enemy_left': frame[frame.shape[0]-200:frame.shape[0]-100, 50:150],
                'enemy_right': frame[frame.shape[0]-200:frame.shape[0]-100, frame.shape[1]-150:frame.shape[1]-50]
            }
            
            for tower_name, region in tower_regions.items():
                # Detectar barra de vida (vermelha)
                hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
                lower_red = np.array([0, 50, 50])
                upper_red = np.array([10, 255, 255])
                
                mask = cv2.inRange(hsv, lower_red, upper_red)
                health_pixels = cv2.countNonZero(mask)
                total_pixels = mask.shape[0] * mask.shape[1]
                
                health_percentage = health_pixels / total_pixels if total_pixels > 0 else 0
                health_values[tower_name] = min(1.0, health_percentage * 5)  # Ajustar multiplicador
            
            return health_values
            
        except Exception as e:
            logger.error(f"Error detecting tower health: {e}")
            return {'ally_left': 1.0, 'ally_right': 1.0, 'enemy_left': 1.0, 'enemy_right': 1.0}
    
    def get_game_state(self, frame: np.ndarray) -> Dict:
        """Obtém o estado completo do jogo"""
        try:
            state = {
                'units': self.detect_units_on_field(frame),
                'buildings': self.detect_buildings(frame),
                'cards': self.detect_cards_in_hand(frame),
                'elixir': self.detect_elixir(frame),
                'tower_health': self.detect_tower_health(frame)
            }
            
            return state
            
        except Exception as e:
            logger.error(f"Error getting game state: {e}")
            return {}

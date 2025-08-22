import os

import numpy as np
from PIL import Image
from scipy.optimize import linear_sum_assignment

from clashroyalebuildabot.constants import CARD_CONFIG
from clashroyalebuildabot.constants import IMAGES_DIR
from clashroyalebuildabot.namespaces.cards import Cards
from error_handling import WikifiedError


class CardDetector:
    HAND_SIZE = 5
    MULTI_HASH_SCALE = 0.355
    MULTI_HASH_INTERCEPT = 163

    def __init__(self, cards, hash_size=8, grey_std_threshold=5):
        self.cards = cards
        self.hash_size = hash_size
        self.grey_std_threshold = grey_std_threshold

        self.cards.extend([Cards.BLANK for _ in range(5)])
        self.card_hashes = self._calculate_card_hashes()
        
        # Mapeamento de cartas similares para melhorar detecção
        self.similar_cards = {
            'minipekka': ['musketeer', 'knight'],
            'musketeer': ['minipekka', 'archers'],
            'archers': ['musketeer', 'minipekka'],
            'arrows': ['zap', 'fireball'],
            'zap': ['arrows', 'fireball'],
            'fireball': ['arrows', 'zap']
        }

    def _calculate_multi_hash(self, image):
        gray_image = self._calculate_hash(image)
        light_image = (
            self.MULTI_HASH_SCALE * gray_image + self.MULTI_HASH_INTERCEPT
        )
        dark_image = (
            gray_image - self.MULTI_HASH_INTERCEPT
        ) / self.MULTI_HASH_SCALE
        multi_hash = np.vstack([gray_image, light_image, dark_image]).astype(
            np.float32
        )
        return multi_hash

    def _calculate_hash(self, image):
        return np.array(
            image.resize(
                (self.hash_size, self.hash_size), Image.Resampling.BILINEAR
            ).convert("L"),
            dtype=np.float32,
        ).ravel()

    def _calculate_card_hashes(self):
        card_hashes = np.zeros(
            (
                len(self.cards),
                3,
                self.hash_size * self.hash_size,
                self.HAND_SIZE,
            ),
            dtype=np.float32,
        )
        try:
            for i, card in enumerate(self.cards):
                path = os.path.join(IMAGES_DIR, "cards", f"{card.name}.jpg")
                pil_image = Image.open(path)

                multi_hash = self._calculate_multi_hash(pil_image)
                card_hashes[i] = np.tile(
                    np.expand_dims(multi_hash, axis=2), (1, 1, self.HAND_SIZE)
                )
        except Exception as e:
            raise WikifiedError(
                "005", "Can't load cards and their images."
            ) from e
        return card_hashes

    def _detect_cards(self, image):
        crops = [image.crop(position) for position in CARD_CONFIG]
        crop_hashes = np.array(
            [self._calculate_hash(crop) for crop in crops]
        ).T
        hash_diffs = np.mean(
            np.amin(np.abs(crop_hashes - self.card_hashes), axis=1), axis=1
        ).T
        _, idx = linear_sum_assignment(hash_diffs)
        cards = [self.cards[i] for i in idx]

        # Pós-processamento para melhorar detecção
        cards = self._post_process_detection(cards, hash_diffs)
        
        return cards, crops

    def _post_process_detection(self, cards, hash_diffs):
        """Pós-processa a detecção para reduzir erros comuns"""
        improved_cards = []
        
        for i, card in enumerate(cards):
            card_name = card.name
            
            # Se detectou como "blank", tenta melhorar
            if card_name == "blank":
                # Procura por cartas similares que podem ter sido confundidas
                best_alternative = self._find_best_alternative(i, hash_diffs)
                if best_alternative:
                    improved_cards.append(best_alternative)
                else:
                    improved_cards.append(card)
            
            # Melhora detecção de cartas similares
            elif card_name in self.similar_cards:
                # Verifica se há uma carta similar com score melhor
                better_card = self._check_similar_cards(i, card_name, hash_diffs)
                if better_card:
                    improved_cards.append(better_card)
                else:
                    improved_cards.append(card)
            
            else:
                improved_cards.append(card)
        
        return improved_cards

    def _find_best_alternative(self, card_index, hash_diffs):
        """Encontra a melhor alternativa para uma carta detectada como blank"""
        # Procura por cartas com scores baixos (melhor match)
        best_score = float('inf')
        best_card = None
        
        for i, card in enumerate(self.cards):
            if card.name != "blank":
                score = hash_diffs[card_index, i]
                if score < best_score:
                    best_score = score
                    best_card = card
        
        # Só usa alternativa se o score for bom o suficiente
        if best_score < 50:  # Threshold ajustável
            return best_card
        return None

    def _check_similar_cards(self, card_index, detected_name, hash_diffs):
        """Verifica se há uma carta similar com score melhor"""
        similar_names = self.similar_cards.get(detected_name, [])
        current_score = hash_diffs[card_index, self.cards.index(self._get_card_by_name(detected_name))]
        
        best_card = self._get_card_by_name(detected_name)
        best_score = current_score
        
        for similar_name in similar_names:
            similar_card = self._get_card_by_name(similar_name)
            if similar_card:
                similar_index = self.cards.index(similar_card)
                similar_score = hash_diffs[card_index, similar_index]
                
                if similar_score < best_score:
                    best_score = similar_score
                    best_card = similar_card
        
        return best_card

    def _get_card_by_name(self, name):
        """Obtém uma carta pelo nome"""
        for card in self.cards:
            if card.name == name:
                return card
        return None

    def _detect_if_ready(self, crops):
        ready = []
        for i, crop in enumerate(crops[1:]):
            std = np.mean(np.std(np.array(crop), axis=2))
            if std > self.grey_std_threshold:
                ready.append(i)
        return ready

    def run(self, image):
        cards, crops = self._detect_cards(image)
        ready = self._detect_if_ready(crops)
        return cards, ready

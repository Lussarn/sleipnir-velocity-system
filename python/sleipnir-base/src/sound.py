import pygame
import logging
from PySide2.QtCore import QTimer

logger = logging.getLogger(__name__)

class Sound:
    sounds = {}

    def __init__(self):
        logger.info("Initialize pygame")
        pygame.init()
        pygame.mixer.init()
        logger.info("Preloading sounds...")
        self.sounds['gate-1'] = pygame.mixer.Sound('assets/sounds/gate-1.ogg')
        self.sounds['gate-2'] = pygame.mixer.Sound('assets/sounds/gate-2.ogg')
        self.sounds['error'] = pygame.mixer.Sound('assets/sounds/error.ogg')
        for i in range (0, 500):
            self.sounds['number-' + str(i)] = pygame.mixer.Sound('assets/sounds/numbers/' + str(i) + '.ogg')
        logger.info("All sounds loaded")

    def play_gate_1(self, wait=0):
        QTimer.singleShot(wait, self.sounds['gate-1'].play)

    def play_gate_2(self, wait=0):
        QTimer.singleShot(wait, self.sounds['gate-2'].play)

    def play_error(self, wait=0):
        QTimer.singleShot(wait, self.sounds['error'].play)

    def play_number(self, number: int, wait=0):
        QTimer.singleShot(wait, self.sounds['number-' + str(number)].play)
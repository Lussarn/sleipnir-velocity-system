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
        self.sounds['beep'] = pygame.mixer.Sound('assets/sounds/beep.ogg')
        self.sounds['beep-beep'] = pygame.mixer.Sound('assets/sounds/beep-beep.ogg')
        self.sounds['error'] = pygame.mixer.Sound('assets/sounds/error.ogg')
        self.sounds['gate-1'] = pygame.mixer.Sound('assets/sounds/gate-1.ogg')
        self.sounds['gate-2'] = pygame.mixer.Sound('assets/sounds/gate-2.ogg')
        self.sounds['left'] = pygame.mixer.Sound('assets/sounds/left.ogg')
        self.sounds['right'] = pygame.mixer.Sound('assets/sounds/right.ogg')
        self.sounds['crossed-the-finish-line'] = pygame.mixer.Sound('assets/sounds/crossed-the-finish-line.ogg')
        for i in range (0, 500):
            self.sounds['number-' + str(i)] = pygame.mixer.Sound('assets/sounds/numbers/' + str(i) + '.ogg')
        logger.info("All sounds loaded")

    def play_beep(self, wait=0):
        QTimer.singleShot(wait, self.sounds['beep'].play)

    def play_beep_beep(self, wait=0):
        QTimer.singleShot(wait, self.sounds['beep-beep'].play)

    def play_error(self, wait=0):
        QTimer.singleShot(wait, self.sounds['error'].play)

    def play_number(self, number: int, wait=0):
        QTimer.singleShot(wait, self.sounds['number-' + str(number)].play)

    def play_gate_1(self, wait=0):
        QTimer.singleShot(wait, self.sounds['gate-1'].play)

    def play_gate_2(self, wait=0):
        QTimer.singleShot(wait, self.sounds['gate-2'].play)

    def play_left(self, wait=0):
        QTimer.singleShot(wait, self.sounds['left'].play)

    def play_right(self, wait=0):
        QTimer.singleShot(wait, self.sounds['right'].play)

    def play_cross_the_finish_line(self, wait=0):
        QTimer.singleShot(wait, self.sounds['crossed-the-finish-line'].play)

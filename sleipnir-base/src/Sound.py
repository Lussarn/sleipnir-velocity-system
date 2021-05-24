import pygame
import os

class Sound:
    sounds = {}

    def __init__(self):
        print("INFO: Sound.__init__() Initialize pygame")
        pygame.init()
        pygame.mixer.init()
        print("INFO: Sound.__init__() Preloading sounds")
        self.sounds['gate-1'] = pygame.mixer.Sound('assets/sounds/gate-1.ogg')
        self.sounds['gate-2'] = pygame.mixer.Sound('assets/sounds/gate-2.ogg')
        self.sounds['error'] = pygame.mixer.Sound('assets/sounds/error.ogg')
        for i in range (0, 500):
            self.sounds['number-' + str(i)] = pygame.mixer.Sound('assets/sounds/numbers/' + str(i) + '.ogg')
        print("INFO: Sound.__init__() All sounds loaded")

    def play_gate_1(self):
        self.sounds['gate-1'].play()

    def play_gate_2(self):
        self.sounds['gate-2'].play()

    def play_error(self):
        self.sounds['error'].play()

    def play_number(self, number: int):
        self.sounds['number-' + str(number)].play()
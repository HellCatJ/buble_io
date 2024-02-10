import datetime

import pygame
import time

class ImageButton:
    def __init__(self, x, y, width, height, text, image_path=None, hover_image_path=None, sound_path=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (width, height))
        self.hover_image = self.image
        if hover_image_path:
            self.hover_image = pygame.image.load(hover_image_path)
            self.hover_image = pygame.transform.scale(self.hover_image, (width, height))
        self.rect = self.image.get_rect(topleft=(x, y))

        self.sound = None
        if sound_path:
            self.sound = pygame.mixer.Sound(sound_path)
            self.sound.set_volume(0.1)

        self.is_hovered = False

    def draw(self, screen):
        current_image = self.hover_image if self.is_hovered else self.image
        screen.blit(current_image, self.rect.topleft)

        font = pygame.font.Font(None, 36)
        text_surface = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and self.is_hovered):
            if self.sound:
                self.sound.play()
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, button=self))


"""Draw text to the screen."""
import pygame
from pygame.locals import *


BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
WIDTH, HEIGHT = 800, 600
SCREEN_CENTER = WIDTH // 2, HEIGHT // 2
RADIUS = 100


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))

sysfont = pygame.font.get_default_font()


font = pygame.font.SysFont(None, 48)

img = font.render(sysfont, True, RED)
rect = img.get_rect()
pygame.draw.rect(img, BLUE, rect, 1)



font2 = pygame.font.SysFont('didot.ttc', 72)
img2 = font2.render('didot.ttc', True, GREEN, 1)


def write_nick(x, y, radius, name):

    font = pygame.font.Font(None, radius)
    nick = font.render(name, True, (0, 0, 0))
    rect = nick.get_rect(center=(x, y))
    screen.blit(nick, rect)


def main():
    running = True
    background = GRAY

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False


        screen.fill(background)

        pygame.draw.circle(
            screen,
            RED,
            SCREEN_CENTER,
            RADIUS
        )
        name = 'chalkduster.ttf'
        # font1 = pygame.font.SysFont('chalkduster.ttf', RADIUS)
        # img1 = font1.render(name, True, BLUE, 2)
        # rect1 = img.get_rect(center=SCREEN_CENTER)
        write_nick(WIDTH // 2, HEIGHT // 2, RADIUS, name)



        # screen.blit(img1, rect1)


        screen.blit(img, (20, 20))
        screen.blit(img2, (20, 120))


        pygame.display.update()


if __name__ == '__main__':
    main()
    pygame.quit()
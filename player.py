
import socket
import sys

import pygame
import itertools as it

from packages.button import ImageButton



WIDTH_WINDOW, HEIGHT_WINDOW = 700, 600
HALF_WIDTH, HALF_HEIGHT = WIDTH_WINDOW // 2, HEIGHT_WINDOW // 2
SCREEN_CENTER = (WIDTH_WINDOW // 2, HEIGHT_WINDOW // 2)
original_direction_vector = direction_vector = (0, 0)
COLORS = {0: (255, 255, 0), 1: (255, 0, 0), 2: (0, 255, 0), 3: (0, 255, 255)}
COLORS_SET = len(COLORS)
NICKNAME = '|>_<|'
SOUND = it.cycle((fr'packages\sound\{s}.mp3'
                  for s in ('main_theme', 'game1', 'game2', 'game3')))




def connect_to_server():
    # Настройка сокета AF_INET - IPv4, SOCK_STREAM - TCP protocol
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Запрет упаковки нескольких состояний в один пакет
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    # Подключение к серверу
    sock.connect(('localhost', 10000))
    return sock


def read_mouse_input(player):
    global direction_vector

    # Если мышь находится в пределах игрового окна
    if pygame.mouse.get_focused():

        # Считывание координат мыши
        pos = pygame.mouse.get_pos()

        # Вычисление вектора движения
        direction_vector = pos[0] - HALF_WIDTH, pos[1] - HALF_HEIGHT

        if direction_vector[0] ** 2 + direction_vector[1] ** 2 <= player.radius ** 2:
            direction_vector = (0, 0)


def send_direction_to_server(player_sock):
    global original_direction_vector
    if direction_vector != original_direction_vector:
        original_direction_vector = direction_vector
        message_for_server = '<{},{}>'.format(*direction_vector)
        player_sock.send(message_for_server.encode())


def get_data_from_server(player_sock):
    try:
        # Ожидание ответа от сервера
        data_ = player_sock.recv(2 ** 20)

        # Получаем радиус, х\у на сервере, масштаб
        data_ = find_data(data_.decode())
    except Exception as err:
        print(err)
        sys.exit()

    return data_.split(',')


def data_processing(player, grid, server_response: list):
    if server_response != ['']:
        parameters = list(map(int, server_response[0].split()))
        player.update(parameters[0])  # Радиус
        grid.update(*parameters[1:])  # х\у на сервере, масштаб

        # Рисуем новое состояние игрового поля
        screen.fill('gray')  # Заливка фона окна

        grid.draw()
        draw_opponents(server_response[1:])


        player.draw()



def find_data(line):
    open_index = None
    for i, elem in enumerate(line):
        if elem == '<':
            open_index = i
        if elem == '>' and open_index is not None:
            return line[open_index + 1:i]
    return ''


def write_nick(x, y, radius, name):
    # TODO исправить отображение ников
    font = pygame.font.Font(None, radius)
    nick = font.render(name, True, (0, 0, 0))
    rect = nick.get_rect(center=(x, y))
    screen.blit(nick, rect)


def draw_opponents(data):
    for i, obj in enumerate(data):
        new_obj = obj.split()
        x = WIDTH_WINDOW // 2 + int(new_obj[0])
        y = HEIGHT_WINDOW // 2 + int(new_obj[1])
        r = int(new_obj[2])
        color = int(new_obj[3])
        pygame.draw.circle(screen, COLORS[color], (x, y), r)

        if len(new_obj) == 5:
            write_nick(x, y, r, new_obj[4])


def draw_lose_screen(buttons):
    pygame.draw.rect(surface, (255, 255, 255, 120), (0, 0, WIDTH_WINDOW, HEIGHT_WINDOW))
    write_nick(HALF_WIDTH, HALF_HEIGHT - 50, 60, 'Попробовать снова')

    for button in buttons:
        button.check_hover(pygame.mouse.get_pos())
        button.draw(screen)




class Player:
    def __init__(self, data: str):
        self.radius, self.color = map(int, data.split())
        self.scale = 1

    def update(self, new_r):
        self.radius = new_r

    def draw(self):
        if not self.radius:
            return
        pygame.draw.circle(
            screen,
            COLORS[self.color],
            SCREEN_CENTER,
            self.radius
        )
        write_nick(HALF_WIDTH, HALF_HEIGHT, self.radius, NICKNAME)


class Grid:
    """Сетка на игровом поле"""

    def __init__(self, screen_):
        self.screen = screen_
        self.x = 0
        self.y = 0
        self.start_size = 200
        self.size = self.start_size
        self.color = (150, 150, 150)

    def update(self, x, y, scale):
        self.size = self.start_size // scale  # Обновление размера ячейки сетки когда меняется масштаб

        # Сетка движется противоположно направлению игрока потому "-"
        # Ограничение при помощи модуля чтобы сетка не убежала
        self.x = -self.size + (-x % self.size)
        self.y = -self.size + (-y % self.size)

    def draw(self):
        # Отрисовка вертикальных полос
        for i in range(WIDTH_WINDOW // self.size + 2):
            pygame.draw.line(self.screen,
                             self.color,
                             (self.x + i * self.size, 0),  # Координаты верхнего конца отрезка
                             (self.x + i * self.size, HEIGHT_WINDOW),  # Координаты нижнего конца отрезка
                             1)

        # Отрисовка горизонтальных полос
        for i in range(HEIGHT_WINDOW // self.size + 2):
            pygame.draw.line(self.screen,
                             self.color,
                             (0, self.y + i * self.size),  # Координаты верхнего конца отрезка
                             (WIDTH_WINDOW, self.y + i * self.size),  # Координаты нихденго конца отрезка
                             1)


pygame.init()

# Создание окна игры
screen = pygame.display.set_mode((WIDTH_WINDOW, HEIGHT_WINDOW))
pygame.display.set_caption('Untitled')

# Создание поверхности, которая будет над основным экраном
surface = pygame.Surface((WIDTH_WINDOW, HEIGHT_WINDOW), pygame.SRCALPHA)



def main():
    # Создание сокета и подключение к серверу
    try:
        player_sock = connect_to_server()
    except ConnectionRefusedError:
        print('Server not found')
        sys.exit()

    # Отправка серверу ник и размер окна
    player_sock.send(f'.{NICKNAME} {WIDTH_WINDOW} {HEIGHT_WINDOW}.'.encode())

    # Получение размера и цвета
    data = player_sock.recv(64).decode()

    # Отправка подтверждения получения
    player_sock.send('!'.encode())

    # Создание объектов сетки и игрока
    grid = Grid(screen)
    player = Player(data)

    # Создание объектов кнопок
    retry_button = ImageButton(HALF_WIDTH - 150, HALF_HEIGHT, 150, 50, 'ДА',
                               r'packages\img\simple_img1.jpg',
                               r'packages\img\simple_img2.jpg',
                               r'packages\sound\mouse_click.mp3')
    reject_button = ImageButton(HALF_WIDTH + 5, HALF_HEIGHT, 150, 50, 'НЕТ',
                                r'packages\img\simple_img1.jpg',
                                r'packages\img\simple_img2.jpg')
    buttons = (retry_button, reject_button)


    main_sound = pygame.mixer.Sound(next(SOUND))
    main_sound.set_volume(0.1)
    is_running = True

    while is_running:
        # Проигрывание музыки игры
        main_sound.play(-1)

        # Считывание мыши
        read_mouse_input(player)

        # Отправка вектора движения на сервер если он поменялся
        send_direction_to_server(player_sock)

        # Получение от сервера нового состояние игрового пля
        data = get_data_from_server(player_sock)

        # Обрабатываем сообщение с сервера
        data_processing(player, grid, data)

        if not player.radius:
            main_sound.stop()

            screen.blit(surface, (0, 0))  # Покрываем основной экран поверхностью
            draw_lose_screen(buttons)



        # Обработка событий
        for event in pygame.event.get():  # Список событий
            if event.type == pygame.QUIT:
                # is_running = False
                sys.exit()
            elif (event.type == pygame.USEREVENT and
                  event.button == retry_button):
                main()
            elif (event.type == pygame.USEREVENT and
                  event.button == reject_button):
                sys.exit()

            for button in buttons:
                button.handle_event(event)


        pygame.display.flip()  # Обновление дисплея

    pygame.quit()


if __name__ == '__main__':
    main()

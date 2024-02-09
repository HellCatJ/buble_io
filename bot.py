import pygame
import socket
import random as rnd


RUNNING = True
WIDTH_WINDOW, HEIGHT_WINDOW = 700, 600
HALF_WIDTH, HALF_HEIGHT = WIDTH_WINDOW // 2, HEIGHT_WINDOW // 2
SCREEN_CENTER = (WIDTH_WINDOW // 2, HEIGHT_WINDOW // 2)
PLAYER_RADIUS = 50
COLORS = {0: (255, 255, 0), 1: (255, 0, 0), 2: (0, 255, 0), 3: (0, 255, 255)}
COLORS_SET = len(COLORS)
NICKNAME = '|>_<|'
GRID_COLOR = (150, 150, 150)
original_direction_vector = (0, 0)
direction_vector = rnd.randint(-100, 100), rnd.randint(-100, 100)


def connect_to_server():
    # Создание сокета и подключение к серверу
    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_STREAM)  # Настройка сокета AF_INET - IPv4, SOCK_STREAM - TCP protocol

    sock.setsockopt(socket.IPPROTO_TCP,
                    socket.TCP_NODELAY, 1)  # Запрет упаковки нескольких состояний в один пакет

    sock.connect(('localhost', 10000))  # Подключение к серверу
    return sock


def create_screen():
    # Создание окна игры
    pygame.init()
    game_screen = pygame.display.set_mode((WIDTH_WINDOW, HEIGHT_WINDOW))
    pygame.display.set_caption('BOT')
    return game_screen


def find_data(line):
    open_index = None
    for i, elem in enumerate(line):
        if elem == '<':
            open_index = i
        if elem == '>' and open_index is not None:
            return line[open_index + 1:i]
    return ''


def write_nick(x, y, radius, name):
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


class Player:
    def __init__(self, data: str):
        self.radius, self.color = map(int, data.split())

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
    def __init__(self, screen):
        self.screen = screen
        self.x = 0
        self.y = 0
        self.start_size = 200
        self.size = self.start_size

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
                             GRID_COLOR,
                             (self.x + i * self.size, 0),  # Координаты верхнего конца отрезка
                             (self.x + i * self.size, HEIGHT_WINDOW),  # Координаты нижнего конца отрезка
                             1)

        # Отрисовка горизонтальных полос
        for i in range(HEIGHT_WINDOW // self.size + 2):
            pygame.draw.line(self.screen,
                             GRID_COLOR,
                             (0, self.y + i * self.size),  # Координаты верхнего конца отрезка
                             (WIDTH_WINDOW, self.y + i * self.size),  # Координаты нихденго конца отрезка
                             1)


while True:

    screen = create_screen()
    player_sock = connect_to_server()

    # Отправка серверу ник и размер окна
    player_sock.send(f'.{NICKNAME} {WIDTH_WINDOW} {HEIGHT_WINDOW}.'.encode())

    # Получение размера и цвета
    data = player_sock.recv(64).decode()

    # Отправка подтверждения получения
    player_sock.send('!'.encode())

    # Создание объектов сетки и игрока
    grid = Grid(screen)
    player = Player(data)
    tick = 0

    # Обработка событий
    for event in pygame.event.get():  # Список событий
        if event.type == pygame.QUIT:
           break

    while RUNNING:
        tick += 1

        # # Считывание мыши
        # if pygame.mouse.get_focused():  # Находится ли мышь в пределах игрового окна
        #     pos = pygame.mouse.get_pos()  # Считывание координат мыши
        #     direction_vector = pos[0] - HALF_WIDTH, pos[1] - HALF_HEIGHT  # Вычисление вектора движения
        #
        #
        #     if direction_vector[0] ** 2 + direction_vector[1] ** 2 <= player.radius ** 2:
        #         direction_vector = (0, 0)


        # Иммитация мыши

        pos = rnd.randint(-100, 100), rnd.randint(-100, 100)
        direction_vector = pos[0] - HALF_WIDTH, pos[1] - HALF_HEIGHT  # Вычисление вектора движения


        if direction_vector[0] ** 2 + direction_vector[1] ** 2 <= player.radius ** 2:
            direction_vector = (0, 0)



        # Отправка вектора движения на сервер если он поменялся
        if direction_vector != original_direction_vector:
            original_direction_vector = direction_vector
            message_for_server = '<{},{}>'.format(*direction_vector)
            player_sock.send(message_for_server.encode())

        # Получаем от сервера новое состояние игрового пля
        try:
            data = player_sock.recv(2 ** 20)  # Ожидание ответа от сервера
        except:
            break
        data = find_data(data.decode())  # Получаем радиус, х\у на сервере, масштаб
        data = data.split(',')

        # Обрабатываем сообщение с сервера
        if data != ['']:
            parameters = list(map(int, data[0].split()))
            player.update(parameters[0])  # Радиус
            grid.update(*parameters[1:])  # х\у на сервере, масштаб
            # Рисуем новое состояние игрового поля
            screen.fill('gray')  # Заливка фона окна
            grid.draw()
            draw_opponents(data[1:])
            player.draw()

        pygame.display.update()  # Обновление дисплея

pygame.quit()

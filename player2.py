import socket

import pygame

RUNNING = True
WIDTH_WINDOW, HEIGHT_WINDOW = 700, 600
HALF_WIDTH, HALF_HEIGHT = WIDTH_WINDOW // 2, HEIGHT_WINDOW // 2
SCREEN_CENTER = (WIDTH_WINDOW // 2, HEIGHT_WINDOW // 2)
PLAYER_RADIUS = 50
# PLAYER_COLOR = (255, 0, 0)
original_direction_vector = direction_vector = (0, 0)
COLORS = {0: (255, 255, 0), 1: (255, 0, 0), 2: (0, 255, 0), 3: (0, 255, 255)}
COLORS_SET = len(COLORS)
NICKNAME = '|>_<|'


def find_data(line):
    open_index = None
    for i, elem in enumerate(line):
        if elem == '<':
            open_index = i
        if elem == '>' and open_index is not None:
            return line[open_index + 1:i]
    return ''


def draw_opponents(data):
    for i, obj in enumerate(data):
        new_obj = obj.split()
        x = WIDTH_WINDOW // 2 + int(new_obj[0])
        y = HEIGHT_WINDOW // 2 + int(new_obj[1])
        r = int(new_obj[2])
        color = int(new_obj[3])
        pygame.draw.circle(screen, COLORS[color], (x, y), r)


class Me:
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


# Создание сокета и подключение к серверу
player_sock = socket.socket(socket.AF_INET,
                            socket.SOCK_STREAM)  # Настройка сокета AF_INET - IPv4, SOCK_STREAM - TCP protocol
player_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Запрет упаковки нескольких состояний в один пакет
player_sock.connect(('localhost', 10000))  # Подключение к серверу

# Отправка серверу ник и размер окна
player_sock.send(f'.{NICKNAME} {WIDTH_WINDOW} {HEIGHT_WINDOW}.'.encode())

# Получение размера и цвета
data = player_sock.recv(64).decode()

# Отправка подтверждения получения
player_sock.send('!'.encode())

# Объекта игрока
me = Me(data)

# Создание окна игры
pygame.init()
screen = pygame.display.set_mode((WIDTH_WINDOW, HEIGHT_WINDOW))
pygame.display.set_caption('Untitled')

while RUNNING:
    # Обработка событий
    for event in pygame.event.get():  # Список событий
        if event.type == pygame.QUIT:
            RUNNING = False

    # Считывание мыши
    if pygame.mouse.get_focused():  # Находится ли мышь в пределах игрового окна
        pos = pygame.mouse.get_pos()  # Считывание координат мыши
        direction_vector = pos[0] - HALF_WIDTH, pos[1] - HALF_HEIGHT  # Вычисление вектора движения

        if direction_vector[0] ** 2 + direction_vector[1] ** 2 <= me.radius ** 2:
            direction_vector = (0, 0)

    # Отправка вектора движения на сервер если он поменялся
    if direction_vector != original_direction_vector:
        original_direction_vector = direction_vector
        message_for_server = '<{},{}>'.format(*direction_vector)
        player_sock.send(message_for_server.encode())

    # Получаем от сервера новое состояние игрового пля
    data = player_sock.recv(1024)  # Ожидание ответа от сервера
    data = find_data(data.decode())
    data = data.split(',')

    # Рисуем новое состояние игрового поля
    screen.fill('gray')  # Заливка фона окна

    if data != ['']:
        me.update(int(data[0]))
        draw_opponents(data[1:])

    me.draw()


    pygame.display.update()  # Обновление дисплея

pygame.quit()

import socket
import pygame

RUNNING = True
WIDTH_WINDOW, HEIGHT_WINDOW = 700, 600
PLAYER_RADIUS = 50
PLAYER_COLOR = (255, 0, 0)
original_direction_vector = direction_vector = (0, 0)
COLORS = {0: (255, 255, 0), 1: (255, 0, 0), 2: (0, 255, 0), 3: (0, 255, 255)}


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



# Создание сокета и подключение к серверу
player_sock = socket.socket(socket.AF_INET,
                            socket.SOCK_STREAM)  # Настройка сокета AF_INET - IPv4, SOCK_STREAM - TCP protocol
player_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Запрет упаковки нескольких состояний в один пакет
player_sock.connect(('localhost', 10000))  # Подключение к серверу

PLAYER_COLOR = COLORS[int(player_sock.recv(16).decode())]


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
        direction_vector = pos[0] - WIDTH_WINDOW // 2, pos[1] - HEIGHT_WINDOW // 2  # Вычисление вектора движения

        if direction_vector[0] ** 2 + direction_vector[1] ** 2 <= PLAYER_RADIUS ** 2:
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
    pygame.draw.circle(screen,
                       PLAYER_COLOR,
                       (WIDTH_WINDOW // 2, HEIGHT_WINDOW // 2),
                       PLAYER_RADIUS)
    if data != ['']:
        draw_opponents(data)
    pygame.display.update()  # Обновление дисплея

pygame.quit()

import random as rnd
import socket

import pygame

RUNNING = True
FPS = 100
START_PLAYER_SIZE = 50
WIDTH_ROOM, HEIGHT_ROOM = 4000, 4000
WIDTH_SERVER_WINDOW, HEIGHT_SERVER_WINDOW = 300, 300

NPS_QUANTITY = 25
COLORS = {0: (255, 255, 0), 1: (255, 0, 0), 2: (0, 255, 0), 3: (0, 255, 255)}


def get_coord(line: str):
    open_index = None
    for i, elem in enumerate(line):
        if elem == '<':
            open_index = i
        if elem == '>' and open_index is not None:
            res = line[open_index + 1:i]
            return list(map(int, res.split(',')))
    return ''


class Player:
    def __init__(self, conn, addr, x, y, r, color):
        self.connection = conn
        self.address = addr

        self.x = x
        self.y = y
        self.radius = r
        self.color = color

        self.width_vision = 1000
        self.height_vision = 1000

        self.errors = 0

        self.absolute_speed = 1
        self.speed_x = self.speed_y = 0

    def update(self):
        # х координата
        if self.x - self.radius <= 0:
            if self.speed_x >= 0:
                self.x += self.speed_x
        else:
            if self.x + self.radius >= WIDTH_ROOM:
                if self.speed_x <= 0:
                    self.x += self.speed_x
            else:
                self.x += self.speed_x

        # y координата
        if self.y - self.radius <= 0:
            if self.speed_y >= 0:
                self.y += self.speed_y
        else:
            if self.y + self.radius >= HEIGHT_ROOM:
                if self.speed_y <= 0:
                    self.x += self.speed_y
            else:
                self.y += self.speed_y

    def change_speed(self, data):
        """Функция нормирования вектора направления движения
        (отбросить длину вектора и оставить только его направление) """
        if data == (0, 0):
            self.x, self.y = data
        else:
            len_vector = (data[0] ** 2 + data[1] ** 2) ** 0.5 or 0.1

            data = data[0] / len_vector, data[1] / len_vector
            data = tuple(map(lambda x: x * self.absolute_speed, data))
            self.speed_x, self.speed_y = data


# Создание основного (буферного) сокета
main_socket = socket.socket(socket.AF_INET,
                            socket.SOCK_STREAM)  # Настройка сокета AF_INET - IPv4, SOCK_STREAM - TCP protocol
main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Запрет упаковки нескольких состояний в один пакет
main_socket.bind(('localhost', 10000))  # Установка адреса и порта для сокета
main_socket.setblocking(False)  # Отключение блокировки выполнение программы на время ожидания ответа
# (работа независио от клиента)
main_socket.listen(5)  # Режим прослушивания с макс. 5 одноврем. подключениями к буферному сокету

# Создание графического окна сервера
pygame.init()
screen = pygame.display.set_mode((WIDTH_SERVER_WINDOW, HEIGHT_SERVER_WINDOW))
clock = pygame.time.Clock()

# Создание стартового набора НПС
players = [Player(None, None,
                  x=rnd.randrange(WIDTH_ROOM),
                  y=rnd.randrange(HEIGHT_ROOM),
                  r=rnd.randint(10, 100),
                  color=rnd.randrange(4)
                  )
           for _ in range(NPS_QUANTITY)
           ]

tick = 0

while RUNNING:
    tick += 1
    clock.tick(FPS)  # Установка кадров

    if tick == 200:
        tick = 0
        # Проверяем, есть ли желающие войти в игру
        try:
            new_socket, address = main_socket.accept()  # Проверка на наличие подключений
            new_socket.setblocking(False)
            new_player = Player(
                new_socket,
                address,
                rnd.randrange(WIDTH_ROOM),
                rnd.randrange(HEIGHT_ROOM),
                START_PLAYER_SIZE,
                color=rnd.randrange(4)
            )
            new_player.connection.send(str(new_player.color).encode())
            players.append(new_player)
            print('Connected ', address)
        except BlockingIOError:
            pass

    # Считываем команды игроков
    for player in players:
        if player.connection is not None:
            try:
                data = player.connection.recv(1024)  # Чтение данных с сокета
                data = get_coord(data.decode())

                # Обрабатываем команды
                player.change_speed(data)
            except (BlockingIOError, ConnectionResetError):
                pass
        else:
            if tick == 100:
                data = (rnd.randint(-100, 100), rnd.randint(-100, 100))
                player.change_speed(data)
        player.update()

    # Определяем что видит каждый игрок
    players_count = len(players)
    visible_obj = [[] for i in range(players_count)]
    for i in range(players_count):
        for j in range(i + 1, players_count):
            distance_x = players[j].x - players[i].x
            distance_y = players[j].y - players[i].y

            # игрок i видит игрока j
            if (
                    (abs(distance_x) <= players[i].width_vision // 2 + players[j].radius)
                    and
                    (abs(distance_y) <= players[i].height_vision // 2 + players[j].radius)
            ):
                # Проверка сможет ли i съесть j
                if ((distance_x ** 2 + distance_y ** 2) ** 0.5 <= players[i].radius and
                        players[i].radius > 1.1 * players[j].radius
                ):
                    #### Изменение радиуса i игрока
                    players[j].radius, players[j].speed_x, players[j].speed_y = 0, 0, 0

                if players[i].connection is not None:
                    # подготовка данных для добавления в список видимости
                    x_ = round(distance_x)
                    y_ = round(distance_y)
                    r_ = round(players[j].radius)
                    c_ = players[j].color

                    visible_obj[i].append('{} {} {} {}'.format(x_, y_, r_, c_))

            # игрок j видит игрока i
            if (
                    (abs(distance_x) <= players[j].width_vision // 2 + players[i].radius)
                    and
                    (abs(distance_y) <= players[j].height_vision // 2 + players[i].radius)
            ):
                # Проверка сможет ли j съесть i
                if ((distance_x ** 2 + distance_y ** 2) ** 0.5 <= players[j].radius and
                        players[j].radius > 1.1 * players[i].radius
                ):
                    #### Изменение радиуса j игрока
                    players[i].radius, players[i].speed_x, players[i].speed_y = 0, 0, 0

                if players[j].connection is not None:
                    # подготовка данных для добавления в список видимости
                    x_ = round(-distance_x)
                    y_ = round(-distance_y)
                    r_ = round(players[i].radius)
                    c_ = players[i].color

                    visible_obj[j].append('{} {} {} {}'.format(x_, y_, r_, c_))

    # Формируем ответ каждому игроку
    responses = ['' for i in range(len(players))]
    for i in range(len(players)):
        responses[i] = f'<{",".join(visible_obj[i])}>'

    # Отправляем новое состояние поля
    for i, player in enumerate(players):
        if players[i].connection is not None:
            try:
                player.connection.send(responses[i].encode())  # Отправляем данные
                player.errors = 0
            except:
                player.errors += 1

    # Очистка списка от игроков с ошибками
    for player in players:
        if player.errors == 500 or player.radius == 0:
            if player.connection is not None:
                player.connection.close()
            players.remove(player)

    # Рисуем комнату
    for event in pygame.event.get():  # Список событий
        if event.type == pygame.QUIT:
            RUNNING = False

    screen.fill('BLACK')

    for player in players:
        x = round(player.x * WIDTH_SERVER_WINDOW / WIDTH_ROOM)
        y = round(player.y * HEIGHT_SERVER_WINDOW / HEIGHT_ROOM)
        radius = round(player.radius * WIDTH_SERVER_WINDOW / WIDTH_ROOM)
        color = COLORS[player.color]

        pygame.draw.circle(screen, color, (x, y), radius)
        pygame.display.update()

pygame.quit()
main_socket.close()

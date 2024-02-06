import random as rnd
import socket

import pygame

RUNNING = True
FPS = 100
START_PLAYER_SIZE = 50
FOOD_SIZE = 15
WIDTH_ROOM, HEIGHT_ROOM = 4000, 4000
WIDTH_SERVER_WINDOW, HEIGHT_SERVER_WINDOW = 300, 300

NPS_QUANTITY = 25
FOOD_QUANTITY = (WIDTH_ROOM * HEIGHT_ROOM) // 80000
COLORS = {0: (255, 255, 0), 1: (255, 0, 0), 2: (0, 255, 0), 3: (0, 255, 255)}
COLORS_SET = len(COLORS)


def get_new_radius(player_radius, food_radius):
    return (player_radius ** 2 + food_radius ** 2) ** 0.5


def get_coord(line: str):
    open_index = None
    for i, elem in enumerate(line):
        if elem == '<':
            open_index = i
        if elem == '>' and open_index is not None:
            res = line[open_index + 1:i]
            return list(map(int, res.split(',')))
    return ''


class Food:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color


class Player:
    def __init__(self, conn, addr, x, y, radius, color):
        self.connection = conn
        self.address = addr

        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.name = '^_^'

        self.scale = 1
        self.width_window = 1000
        self.height_window = 800
        self.width_vision = 1000
        self.height_vision = 1000

        self.errors = 0
        self.ready = False  # True - отправка клиенту состояния поля

        self.absolute_speed = 30 / self.radius ** 0.5
        self.speed_x = self.speed_y = 0

    def set_options(self, data: str):
        data = iter(data[1:-1].split(' '))
        self.name = next(data)
        self.width_window = int(next(data))
        self.height_window = int(next(data))
        self.width_vision = self.width_window
        self.height_vision = self.height_window


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

        # Зависимость абсолютной скорости от размера игрока
        self.absolute_speed = 30 / self.radius ** 0.5

        # Уменьшение радиуса игрока
        if self.radius > 100:
            self.radius -= self.radius / 1800

        # Изменение масштаба от размера игрока
        if (self.radius >= self.width_vision / 4 or
                self.radius >= self.height_vision / 4):
            if (self.width_vision <= WIDTH_ROOM or
                    self.height_vision <= HEIGHT_ROOM):
                self.scale *= 2
                self.width_vision = self.width_vision * self.scale
                self.height_vision = self.height_vision * self.scale

        if (self.radius < self.width_vision / 8 and
                self.radius < self.height_vision / 8):
            if self.scale > 1:
                self.scale //= 2
                self.width_vision = self.width_window * self.scale
                self.height_vision = self.height_window * self.scale

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
                  radius=rnd.randint(10, 100),
                  color=rnd.randrange(COLORS_SET))
           for _ in range(NPS_QUANTITY)]

# Создание стартового набора еды
food = [Food(x=rnd.randrange(WIDTH_ROOM),
             y=rnd.randrange(HEIGHT_ROOM),
             radius=FOOD_SIZE,
             color=rnd.randrange(COLORS_SET))
        for _ in range(FOOD_QUANTITY)]

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
            spawn = rnd.choice(food)  # Выбираем место спавна на месте еды
            new_player = Player(
                new_socket,
                address,
                spawn.x,
                spawn.y,
                START_PLAYER_SIZE,
                color=rnd.randrange(4)
            )

            food.remove(spawn)
            players.append(new_player)

            print('Connected ', address)
        except BlockingIOError:
            pass

        # Дополняется список NPC
        for i in range(NPS_QUANTITY - len(players)):
            if len(food):
                spawn = rnd.choice(food)
                players.append(Player(None, None,
                                      x=spawn.x,
                                      y=spawn.y,
                                      radius=rnd.randint(10, 100),
                                      color=rnd.randrange(COLORS_SET)
                                      )
                               )
                food.remove(spawn)

    # Дополняется список еды
    food += [Food(x=rnd.randrange(WIDTH_ROOM),
                  y=rnd.randrange(HEIGHT_ROOM),
                  radius=FOOD_SIZE,
                  color=rnd.randrange(COLORS_SET))
             for _ in range(FOOD_QUANTITY - len(food))]

    # Считываем команды игроков
    for player in players:
        if player.connection is not None:
            try:
                data = player.connection.recv(1024).decode()  # Чтение данных с сокета
                # Пришло сообщение о готовности к диалогу
                if data[0] == '!':
                    player.ready = True
                # Пришло имя и размер окна игрока
                elif (data[0] + data[-1]) == '..':
                    player.set_options(data)
                    message = f'{START_PLAYER_SIZE} {player.color}'
                    player.connection.send(message.encode())
                # Пришел курсор
                else:
                    data = get_coord(data)
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
        # Какую еду видит игрок i
        for k in range(len(food)):
            distance_x = food[k].x - players[i].x
            distance_y = food[k].y - players[i].y

            # игрок i видит еду k
            if (
                    (abs(distance_x) <= players[i].width_vision // 2 + food[k].radius)
                    and
                    (abs(distance_y) <= players[i].height_vision // 2 + food[k].radius)
            ):

                # Проверка сможет ли i съесть j
                if (distance_x ** 2 + distance_y ** 2) ** 0.5 <= players[i].radius:
                    # Изменение радиуса i игрока
                    players[i].radius = get_new_radius(players[i].radius, food[k].radius)
                    food[k].radius = 0

                if players[i].connection is not None and food[k].radius != 0:
                    # подготовка данных для добавления в список видимости
                    x_ = round(distance_x / players[i].scale)
                    y_ = round(distance_y / players[i].scale)
                    r_ = round(food[k].radius / players[i].scale)
                    c_ = food[k].color

                    visible_obj[i].append(f'{x_} {y_} {r_} {c_}')

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
                    # Изменение радиуса i игрока
                    players[i].radius = get_new_radius(players[i].radius, players[j].radius)
                    players[j].radius, players[j].speed_x, players[j].speed_y = 0, 0, 0

                if players[i].connection is not None:
                    # подготовка данных для добавления в список видимости
                    x_ = round(distance_x / players[i].scale)
                    y_ = round(distance_y / players[i].scale)
                    r_ = round(players[j].radius / players[j].scale)
                    c_ = players[j].color

                    visible_obj[i].append(f'{x_} {y_} {r_} {c_}')

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
                    # Изменение радиуса j игрока
                    players[j].radius = get_new_radius(players[j].radius, players[i].radius)
                    players[i].radius, players[i].speed_x, players[i].speed_y = 0, 0, 0

                if players[j].connection is not None:
                    # подготовка данных для добавления в список видимости
                    x_ = round(-distance_x / players[j].scale)
                    y_ = round(-distance_y / players[j].scale)
                    r_ = round(players[i].radius / players[j].scale)
                    c_ = players[i].color

                    visible_obj[j].append(f'{x_} {y_} {r_} {c_}')

    # Формируем ответ каждому игроку
    responses = ['' for i in range(len(players))]
    for i in range(len(players)):
        player_radius = [str(round(players[i].radius / players[i].scale))]
        responses[i] = f'<{",".join(player_radius + visible_obj[i])}>'

    # Отправляем новое состояние поля
    for i, player in enumerate(players):
        if players[i].connection is not None and player.ready:
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

    # Очистка списка от съеденной еды
    for f in food:
        if not f.radius:
            food.remove(f)

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

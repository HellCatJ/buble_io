import pygame
import socket
import random as rnd


RUNNING = True
FPS = 100
START_PLAYER_SIZE = 50
WIDTH_ROOM, HEIGHT_ROOM = 4000, 4000
WIDTH_SERVER_WINDOW, HEIGHT_SERVER_WINDOW = 300, 300
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
        self.errors = 0
        self.speed_x = 5
        self.speed_y = 2

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y

    def change_speed(self, data):
        pass


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


players = []


while RUNNING:
    clock.tick(FPS)  # Установка кадров

    # Проверяем, есть ли желающие войти в игру
    try:
        new_socket, address = main_socket.accept()  # Проверка на наличие подключений
        new_socket.setblocking(False)
        new_player = Player(
            new_socket,
            address,
            rnd.randint(0, WIDTH_ROOM),
            rnd.randint(0, HEIGHT_ROOM),
            START_PLAYER_SIZE,
            rnd.randrange(4)
        )
        players.append(new_player)
        print('Connected ', address)
    except BlockingIOError:
        print('No palyers')


    # Считываем команды игроков
    for player in players:
        try:
            data = player.connection.recv(1024)  # Чтение данных с сокета
            data.decode()
            data = get_coord(data)
            player.change_speed(data)
        except:
            pass

        player.update()

    # Обрабатываем команды


    # Отправляем новое состояние поля
    for player in players:
        try:
            player.connection.send('New state of game'.encode())  # Отправляем данные
            player.errors = 0
        except:
            player.errors += 1

    # Очистка списка от игроков с ошибками
    for player in players:
        if player.errors == 500:
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

import pygame
import socket



# Создание сокета
player_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Настройка сокета AF_INET - IPv4, SOCK_STREAM - TCP protocol
player_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Запрет упаковки нескольких состояний в один пакет
player_sock.connect(('localhost', 10000))  # Подключение к серверу


while True:
    # Считываем команды игрока


    # Отправка команды на сервер
    player_sock.send('I have to go right'.encode())

    # Получаем от сервера новое состояние игрового пля
    data = player_sock.recv(1024)  # Ожидание ответа от сервера
    data = data.decode()

    # Рисуем новое состояние игрового поля
    print(data)
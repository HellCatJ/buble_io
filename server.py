import pygame
import socket
import time


# Создание основного (буферного) сокета
main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Настройка сокета AF_INET - IPv4, SOCK_STREAM - TCP protocol
main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Запрет упаковки нескольких состояний в один пакет
main_socket.bind(('localhost', 10000))  # Установка адреса и порта для сокета
main_socket.setblocking(False)  # Отключение блокировки выполнение программы на время ожидания ответа(работа независио от клиента)
main_socket.listen(5)  # Режим прослушивания с макс. 5 одноврем. подключениями к буферному сокету


players_socket = []

while True:
    # Проверяем, есть ли желающие войти в игру
    try:
        new_socket, address = main_socket.accept()  # Проверка на наличие подключений
        new_socket.setblocking(False)
        players_socket.append(new_socket)
        print('Connected ', address)
    except BlockingIOError:
        print('No palyers')


    # Считываем комады игроков
    for sock in players_socket:
        try:
            data = sock.recv(1024)  # Чтение данных с сокета
            data.decode()
            print('Got ', data)
        except:
            pass

    # Обрабатываем команды



    # Отправляем новое состояние поля
    for sock in players_socket:
        try:
            sock.send('New state of game'.encode())  # Отправляем данные
        except:
            players_socket.remove(sock)
            sock.close()  # Закрываем сокет
            print('Player disconnected')





    time.sleep(0.1)
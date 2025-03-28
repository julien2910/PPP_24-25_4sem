import socket
import logging

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')


def send_command(command, client_socket):
    try:
        client_socket.sendall(command.encode('utf-8'))
        if command.startswith("Стоп"):
            return None

        response = client_socket.recv(4096).decode('utf-8')
        return response
    except Exception as e:
        logging.error(f"Ошибка при отправке команды: {str(e)}")
        return None


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect(('localhost', 12345))
            print("Успешно подключено к серверу")

            while True:
                try:
                    command = input("Введите команду (Добавить [программа], Запустить [программа], Интервал [секунды], Стоп): ").strip()

                    if not command:
                        continue

                    response = send_command(command, client_socket)

                    if command.startswith("Стоп"):
                        print("Завершение работы клиента")
                        break

                    if response is not None:
                        print("Ответ сервера:", response)

                except KeyboardInterrupt:
                    print("\nОтмена команды (для выхода введите 'Стоп')")
                    continue

        except ConnectionRefusedError:
            print("Ошибка: сервер не доступен")
        except Exception as e:
            print(f"Ошибка: {str(e)}")
        finally:
            print("Соединение закрыто")


if __name__ == "__main__":
    main()
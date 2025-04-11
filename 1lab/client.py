import socket
import struct
import json
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('client.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()


def send_command(command):
    try:
        logger.info(f"Отправка команды: {command}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect(('localhost', 65432))

            data = json.dumps(command).encode('utf-8')
            sock.sendall(struct.pack('>I', len(data)) + data)

            raw_len = sock.recv(4)
            if not raw_len:
                return {'status': 'error', 'message': 'Нет ответа от сервера'}

            msg_len = struct.unpack('>I', raw_len)[0]
            data = sock.recv(msg_len)
            response = json.loads(data.decode('utf-8'))
            logger.info(f"Получен ответ: {response}")
            return response

    except Exception as e:
        logger.error(f"Ошибка соединения: {e}")
        return {'status': 'error', 'message': str(e)}


def save_output(filename, content):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\nВывод сохранен в файл: {filename}")
        return True
    except Exception as e:
        print(f"\nОшибка сохранения: {e}")
        return False


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def show_menu():
    print("\n" + "=" * 40)
    print(" Управление сервером команд ".center(40, '='))
    print("=" * 40)
    print("1. Добавить команду")
    print("2. Получить вывод команды")
    print("3. Изменить интервал выполнения")
    print("4. Показать список команд")
    print("5. Выход")
    print("=" * 40)


def get_input(prompt, validator=None):
    while True:
        value = input(prompt).strip()
        if not value:
            print("Ошибка: значение не может быть пустым")
            continue
        if validator and not validator(value):
            print("Ошибка: недопустимое значение")
            continue
        return value


def main():
    logger.info("Клиент запущен")
    try:
        while True:
            clear_screen()
            show_menu()

            choice = input("\nВыберите действие (1-5): ").strip()

            if choice == '1':
                clear_screen()
                print("\nДобавление новой команды")
                cmd = get_input("\nВведите команду: ")
                response = send_command({'action': 'add_command', 'command': cmd})
                print(f"\nСтатус: {response.get('status')}")
                print(f"Сообщение: {response.get('message')}")
                input("\nНажмите Enter...")

            elif choice == '2':
                clear_screen()
                print("\nПолучение вывода команды")
                cmd = get_input("\nВведите команду: ")
                response = send_command({'action': 'get_output', 'command': cmd})
                if response.get('status') == 'success':
                    save_output(response.get('filename', 'output.txt'), response['output'])
                else:
                    print(f"\nОшибка: {response.get('message')}")
                input("\nНажмите Enter...")

            elif choice == '3':
                clear_screen()
                print("\nИзменение интервала выполнения")
                try:
                    interval = int(get_input("\nНовый интервал (сек, мин. 1): ", lambda x: x.isdigit() and int(x) > 0))
                    response = send_command({'action': 'set_interval', 'interval': interval})
                    print(f"\n{response.get('message')}")
                except ValueError:
                    print("\nОшибка: введите целое число > 0")
                input("\nНажмите Enter...")

            elif choice == '4':
                clear_screen()
                print("\nСписок выполняемых команд:")
                response = send_command({'action': 'get_programs'})
                if response.get('status') == 'success':
                    for i, cmd in enumerate(response.get('programs', []), 1):
                        print(f"{i}. {cmd}")
                else:
                    print(f"Ошибка: {response.get('message')}")
                input("\nНажмите Enter...")

            elif choice == '5':
                print("\nЗавершение работы...")
                break

            else:
                print("\nОшибка: выберите пункт от 1 до 5")
                input("Нажмите Enter...")

    except KeyboardInterrupt:
        print("\nЗавершение работы...")
    finally:
        logger.info("Клиент остановлен")


if __name__ == "__main__":
    main()
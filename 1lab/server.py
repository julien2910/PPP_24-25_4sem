import os
import time
import json
import socket
import logging
import signal
import sys
import subprocess
from threading import Thread, Event

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)

programs = []
interval = 10
stop_event = Event()

def load_programs():
    global programs
    try:
        with open('programs.json', 'r') as f:
            programs = json.load(f)
        logging.info(f"Загружено {len(programs)} программ")
    except FileNotFoundError:
        programs = []
    except json.JSONDecodeError:
        logging.error("Ошибка чтения файла programs.json")
        programs = []

def save_programs():
    try:
        with open('programs.json', 'w') as f:
            json.dump(programs, f, indent=2)
    except IOError as e:
        logging.error(f"Ошибка сохранения программ: {e}")

def is_system_program(name):
    try:
        result = subprocess.run(
            ['where', name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        return result.returncode == 0
    except Exception:
        return False

def add_program(name):
    global programs
    try:
        # Нормализация пути
        if not os.path.isabs(name):
            if is_system_program(name):
                full_path = name
            else:
                full_path = os.path.abspath(name)
        else:
            full_path = name

        # Проверка существования (кроме системных программ)
        if not is_system_program(name) and not os.path.exists(full_path):
            logging.error(f"Файл не существует: {full_path}")
            return False

        if full_path in programs:
            logging.warning(f"Программа уже добавлена: {full_path}")
            return False

        # Создаем директорию для результатов
        base_name = os.path.splitext(os.path.basename(full_path))[0]
        output_dir = f"outputs_{base_name}"
        os.makedirs(output_dir, exist_ok=True)

        programs.append(full_path)
        save_programs()
        logging.info(f"Добавлена программа: {full_path}")
        return True

    except Exception as e:
        logging.error(f"Ошибка добавления программы {name}: {str(e)}")
        return False

def run_program(program):
    try:
        base_name = os.path.splitext(os.path.basename(program))[0]
        output_dir = f"outputs_{base_name}"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = int(time.time())
        output_file = os.path.join(output_dir, f"result_{timestamp}.txt")

        # Формируем команду в зависимости от типа программы
        if program.endswith('.py'):
            cmd = ['python', program]
        else:
            cmd = program

        with open(output_file, 'w') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                shell=True,
                text=True
            )
            exit_code = process.wait()

        if exit_code != 0:
            logging.error(f"Ошибка выполнения {program} (код: {exit_code})")
            return False
        else:
            logging.info(f"Успешно выполнено: {program}")
            return True

    except Exception as e:
        logging.error(f"Ошибка запуска программы {program}: {str(e)}")
        return False

def run_programs():
    while not stop_event.is_set():
        for program in programs:
            run_program(program)
        stop_event.wait(interval)

def handle_client(client_socket):
    try:
        with client_socket:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                parts = data.strip().split(maxsplit=1)
                command = parts[0] if parts else ""
                args = parts[1] if len(parts) > 1 else ""

                if command == "Добавить":
                    success = add_program(args)
                    response = "Программа добавлена" if success else "Ошибка добавления"

                elif command == "Запустить":
                    if args in programs:
                        base_name = os.path.splitext(os.path.basename(args))[0]
                        output_dir = f"outputs_{base_name}"
                        try:
                            output = ""
                            if os.path.exists(output_dir):
                                for fname in sorted(os.listdir(output_dir)):
                                    if fname.startswith('result_'):
                                        with open(os.path.join(output_dir, fname), 'r') as f:
                                            output += f"=== {fname} ===\n{f.read()}\n\n"
                            response = output or "Нет результатов выполнения"
                        except Exception as e:
                            response = f"Ошибка чтения результатов: {str(e)}"
                    else:
                        response = "Программа не найдена"

                elif command == "Интервал":
                    try:
                        global interval
                        new_interval = int(args)
                        if 1 <= new_interval <= 3600:
                            interval = new_interval
                            response = f"Интервал изменен на {interval} сек"
                        else:
                            response = "Интервал должен быть от 1 до 3600 сек"
                    except ValueError:
                        response = "Неверный формат интервала"

                elif command == "Стоп":
                    stop_event.set()
                    response = "Сервер завершает работу"
                    break

                else:
                    response = "Неизвестная команда"

                client_socket.sendall(response.encode('utf-8'))

    except Exception as e:
        logging.error(f"Ошибка обработки клиента: {str(e)}")

def signal_handler(sig, frame):
    logging.info("Получен сигнал завершения, останавливаю сервер...")
    stop_event.set()
    sys.exit(0)

def main():
    load_programs()
    signal.signal(signal.SIGINT, signal_handler)

    # Запускаем поток выполнения программ
    program_thread = Thread(target=run_programs, daemon=True)
    program_thread.start()

    # Настраиваем сокет сервера
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('localhost', 12345))
        server.listen(5)
        logging.info("Сервер запущен на localhost:12345")

        while not stop_event.is_set():
            try:
                client_socket, addr = server.accept()
                logging.info(f"Новое подключение от {addr[0]}:{addr[1]}")
                Thread(
                    target=handle_client,
                    args=(client_socket,),
                    daemon=True
                ).start()
            except Exception as e:
                if not stop_event.is_set():
                    logging.error(f"Ошибка принятия подключения: {str(e)}")

if __name__ == "__main__":
    main()
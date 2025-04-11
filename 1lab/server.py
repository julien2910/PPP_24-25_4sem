import os
import json
import time
import socket
import struct
import logging
import threading
import subprocess
import re
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# Глобальные переменные
programs = []
interval = 10
is_running = False
BLACKLIST = {'format', 'del', 'rmdir', 'shutdown', 'taskkill'}


def sanitize_filename(cmd):
    """Заменяет недопустимые символы в имени файла"""
    return re.sub(r'[\\/*?:"<>| ]', "_", cmd)


def is_command_safe(cmd):
    first_word = cmd.strip().split()[0].lower()
    return first_word not in BLACKLIST


def load_programs():
    global programs, interval
    try:
        if not Path('programs.json').exists():
            with open('programs.json', 'w', encoding='utf-8') as f:
                json.dump({'programs': [], 'interval': 10}, f)

        with open('programs.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            programs = data.get('programs', [])
            interval = data.get('interval', 10)
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
        programs = []
        interval = 10


def save_programs():
    with open('programs.json', 'w', encoding='utf-8') as f:
        json.dump({'programs': programs, 'interval': interval}, f, indent=2)


def add_program(cmd):
    cmd = cmd.strip()
    if not cmd or not is_command_safe(cmd):
        return False
    if cmd not in programs:
        programs.append(cmd)
        safe_name = sanitize_filename(cmd)
        Path(f"commands/{safe_name}").mkdir(parents=True, exist_ok=True)
        return True
    return False


def run_command(cmd):
    safe_name = sanitize_filename(cmd)
    cmd_dir = Path(f"commands/{safe_name}")
    output_file = cmd_dir / "output.log"

    try:
        cmd_dir.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            ['cmd', '/c', cmd],
            capture_output=True,
            text=True,
            encoding='cp866',
            timeout=30,
            shell=False
        )

        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n=== Запуск {time.ctime()} ===\n")
            f.write(f"Команда: {cmd}\n")
            f.write(f"Код возврата: {result.returncode}\n")
            if result.stderr:
                f.write(f"Ошибки:\n{result.stderr}\n")
            f.write(f"Вывод:\n{result.stdout}")

        logger.info(f"Выполнено: {cmd}")
    except subprocess.TimeoutExpired:
        logger.error(f"Таймаут выполнения команды: {cmd}")
    except PermissionError:
        logger.error(f"Нет прав на запись в {output_file}")
    except Exception as e:
        logger.error(f"Ошибка выполнения {cmd}: {e}")


def command_loop():
    global is_running
    is_running = True
    while is_running:
        for cmd in programs:
            if not is_running:
                break
            run_command(cmd)
            time.sleep(interval)


def handle_client(conn, addr):
    try:
        raw_len = conn.recv(4)
        if not raw_len:
            return
        msg_len = struct.unpack('>I', raw_len)[0]
        data = conn.recv(msg_len)

        command = json.loads(data.decode('utf-8'))
        logger.info(f"Получена команда от {addr}: {command['action']}")

        response = {'status': 'error', 'message': 'Неизвестная команда'}

        if command['action'] == 'add_command':
            if add_program(command['command']):
                save_programs()
                response = {'status': 'success', 'message': 'Команда добавлена'}
            else:
                response = {'status': 'error', 'message': 'Недопустимая или существующая команда'}

        elif command['action'] == 'get_output':
            cmd = command['command']
            safe_name = sanitize_filename(cmd)
            output_file = Path(f"commands/{safe_name}/output.log")
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    response = {
                        'status': 'success',
                        'output': f.read(),
                        'filename': f"{safe_name}_output.txt"
                    }
            else:
                response = {'status': 'error', 'message': 'Нет данных'}

        elif command['action'] == 'set_interval':
            try:
                global interval
                interval = max(1, int(command['interval']))
                save_programs()
                response = {'status': 'success', 'message': f'Интервал обновлен: {interval} сек'}
            except ValueError:
                response = {'status': 'error', 'message': 'Неверный интервал'}

        elif command['action'] == 'get_programs':
            response = {'status': 'success', 'programs': programs}

        response_data = json.dumps(response).encode('utf-8')
        conn.sendall(struct.pack('>I', len(response_data)) + response_data)

    except Exception as e:
        logger.error(f"Ошибка обработки клиента: {e}")
    finally:
        conn.close()


def start_server():
    global is_running
    load_programs()
    Path("commands").mkdir(exist_ok=True)

    threading.Thread(target=command_loop, daemon=True).start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', 65432))
        s.listen()
        logger.info("Сервер запущен на localhost:65432")

        try:
            while True:
                conn, addr = s.accept()
                threading.Thread(
                    target=handle_client,
                    args=(conn, addr),
                    daemon=True
                ).start()
        except KeyboardInterrupt:
            logger.info("Остановка сервера...")
            is_running = False
            save_programs()


if __name__ == "__main__":
    start_server()
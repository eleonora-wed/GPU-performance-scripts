import paramiko
import logging
import time
import sys
import re

# Настройка логирования
logging.basicConfig(filename='cpu_mem_net_ib_check.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Путь к вашему SSH ключу
SSH_KEY_PATH = 'C:\\Users\\eleonora.chorshanbie\\Downloads\\eleonora_test_gpu_sines'  # Замените на фактический путь

# Команда для выполнения lscpu
LSCPU_COMMAND = 'lscpu'

# Ожидаемые значения lscpu
EXPECTED_MODEL_NAME = 'Intel(R) Xeon(R) Platinum 8480+'
EXPECTED_SOCKETS = '2'
EXPECTED_THREADS_PER_CORE = '2'
EXPECTED_CORES_PER_SOCKET = '56'
EXPECTED_CPUS = '224'

# Команда для выполнения free -h
FREE_COMMAND = 'free -h'

# Ожидаемые значения total memory
EXPECTED_TOTAL_MEMORY_LIST = ['1.8Ti', '1.9Ti', '2.0Ti']

# Команда для проверки количества Ethernet интерфейсов
NET_COMMAND = 'ls /sys/class/net/ | grep eth | wc -l'
EXPECTED_NET_COUNT = '5'

# Команда для проверки количества InfiniBand интерфейсов
IB_COMMAND = 'ls /sys/class/net/ | grep ib | wc -l'
EXPECTED_IB_COUNT = '8'

def check_cpu_info(client, hostname):
    """Выполняет lscpu и проверяет вывод."""
    logging.info(f"Выполнение команды: '{LSCPU_COMMAND}' на {hostname}...")
    stdin, stdout, stderr = client.exec_command(LSCPU_COMMAND, timeout=60)
    output = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()

    if error:
        log_message = f"Ошибка при выполнении команды '{LSCPU_COMMAND}' на {hostname}: {error}"
        logging.error(log_message)
        print(f"\033[91m{log_message}\033[0m")
        return False

    logging.info(f"Вывод команды '{LSCPU_COMMAND}' с {hostname}:\n{output}")

    model_name_found = False
    sockets_found = False
    threads_per_core_found = False
    cores_per_socket_found = False
    cpus_found = False

    for line in output.splitlines():
        if "Model name:" in line:
            value = line.split(':')[1].strip()
            if value == EXPECTED_MODEL_NAME.strip():
                model_name_found = True
        elif "Socket(s):" in line:
            value = line.split(':')[1].strip()
            if value == EXPECTED_SOCKETS.strip():
                sockets_found = True
        elif "Thread(s) per core:" in line:
            value = line.split(':')[1].strip()
            if value == EXPECTED_THREADS_PER_CORE.strip():
                threads_per_core_found = True
        elif "Core(s) per socket:" in line:
            value = line.split(':')[1].strip()
            if value == EXPECTED_CORES_PER_SOCKET.strip():
                cores_per_socket_found = True
        elif "CPU(s):" in line:
            value = line.split(':')[1].strip()
            if value == EXPECTED_CPUS.strip():
                cpus_found = True

    if (model_name_found and sockets_found and threads_per_core_found and
            cores_per_socket_found and cpus_found):
        log_message = f"Проверка CPU на {hostname} прошла успешно."
        logging.info(log_message)
        print(f"\033[92m{log_message}\033[0m")
        return True
    else:
        log_message = f"Проверка CPU на {hostname} не прошла. Обнаружены следующие несоответствия:"
        logging.warning(log_message)
        print(f"\033[93m{log_message}\033[0m")
        if not model_name_found:
            logging.warning(f"  Ожидаемый Model name: '{EXPECTED_MODEL_NAME}' не найден.")
            print(f"\033[93m  Ожидаемый Model name: '{EXPECTED_MODEL_NAME}' не найден.\033[0m")
        if not sockets_found:
            logging.warning(f"  Ожидаемое Socket(s): '{EXPECTED_SOCKETS}' не найдено.")
            print(f"\033[93m  Ожидаемое Socket(s): '{EXPECTED_SOCKETS}' не найдено.\033[0m")
        if not threads_per_core_found:
            logging.warning(f"  Ожидаемое Thread(s) per core: '{EXPECTED_THREADS_PER_CORE}' не найдено.")
            print(f"\033[93m  Ожидаемое Thread(s) per core: '{EXPECTED_THREADS_PER_CORE}' не найдено.\033[0m")
        if not cores_per_socket_found:
            logging.warning(f"  Ожидаемое Core(s) per socket: '{EXPECTED_CORES_PER_SOCKET}' не найдено.")
            print(f"\033[93m  Ожидаемое Core(s) per socket: '{EXPECTED_CORES_PER_SOCKET}' не найдено.\033[0m")
        if not cpus_found:
            logging.warning(f"  Ожидаемое CPU(s): '{EXPECTED_CPUS}' не найден.")
            print(f"\033[93m  Ожидаемое CPU(s): '{EXPECTED_CPUS}' не найден.\033[0m")
        return False

def check_memory_info(client, hostname):
    """Выполняет free -h и проверяет значение total memory."""
    logging.info(f"Выполнение команды: '{FREE_COMMAND}' на {hostname}...")
    stdin, stdout, stderr = client.exec_command(FREE_COMMAND, timeout=60)
    output = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()

    if error:
        log_message = f"Ошибка при выполнении команды '{FREE_COMMAND}' на {hostname}: {error}"
        logging.error(log_message)
        print(f"\033[91m{log_message}\033[0m")
        return False

    logging.info(f"Вывод команды '{FREE_COMMAND}' с {hostname}:\n{output}")
    print(f"Вывод команды '{FREE_COMMAND}' с {hostname}:\n{output}") # Вывод free -h

    total_memory_found = False
    for line in output.splitlines():
        if line.startswith("Mem:"):
            parts = line.split()
            if len(parts) > 1 and parts[1].strip() in [mem.strip() for mem in EXPECTED_TOTAL_MEMORY_LIST]:
                total_memory_found = True
                break

    if total_memory_found:
        log_message = f"Проверка памяти на {hostname} прошла успешно. Total Mem: {EXPECTED_TOTAL_MEMORY_LIST}"
        logging.info(log_message)
        print(f"\033[92mПроверка памяти на {hostname} прошла успешно. Total Mem: {', '.join(EXPECTED_TOTAL_MEMORY_LIST)}\033[0m")
        return True
    else:
        log_message = f"Проверка памяти на {hostname} не прошла. Ожидаемые Total Mem: '{EXPECTED_TOTAL_MEMORY_LIST}' не найдены."
        logging.warning(log_message)
        print(f"\033[93mПроверка памяти на {hostname} не прошла. Ожидаемые Total Mem: '{', '.join(EXPECTED_TOTAL_MEMORY_LIST)}' не найдены.\033[0m")
        return False

def check_network_interfaces(client, hostname):
    """Выполняет команду для подсчета Ethernet интерфейсов и проверяет результат."""
    logging.info(f"Выполнение команды: '{NET_COMMAND}' на {hostname}...")
    stdin, stdout, stderr = client.exec_command(NET_COMMAND, timeout=60)
    output = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()

    if error:
        log_message = f"Ошибка при выполнении команды '{NET_COMMAND}' на {hostname}: {error}"
        logging.error(log_message)
        print(f"\033[91m{log_message}\033[0m")
        return False

    logging.info(f"Вывод команды '{NET_COMMAND}' с {hostname}: '{output}'")
    print(f"Вывод команды '{NET_COMMAND}' с {hostname}: '{output}'") # Вывод команды сети

    if output.strip() == EXPECTED_NET_COUNT.strip():
        log_message = f"Проверка количества Ethernet интерфейсов на {hostname} прошла успешно. Обнаружено: {EXPECTED_NET_COUNT}"
        logging.info(log_message)
        print(f"\033[92mПроверка Ethernet интерфейсов на {hostname} прошла успешно. Обнаружено: {EXPECTED_NET_COUNT}\033[0m")
        return True
    else:
        log_message = f"Проверка количества Ethernet интерфейсов на {hostname} не прошла. Ожидалось: '{EXPECTED_NET_COUNT}', обнаружено: '{output}'."
        logging.warning(log_message)
        print(f"\033[93mПроверка Ethernet интерфейсов на {hostname} не прошла. Ожидалось: '{EXPECTED_NET_COUNT}', обнаружено: '{output}'.\033[0m")
        return False

def check_infiniband_interfaces(client, hostname):
    """Выполняет команду для подсчета InfiniBand интерфейсов и проверяет результат."""
    logging.info(f"Выполнение команды: '{IB_COMMAND}' на {hostname}...")
    stdin, stdout, stderr = client.exec_command(IB_COMMAND, timeout=60)
    output = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()

    if error:
        log_message = f"Ошибка при выполнении команды '{IB_COMMAND}' на {hostname}: {error}"
        logging.error(log_message)
        print(f"\033[91m{log_message}\033[0m")
        return False

    logging.info(f"Вывод команды '{IB_COMMAND}' с {hostname}: '{output}'")
    print(f"Вывод команды '{IB_COMMAND}' с {hostname}: '{output}'") # Вывод команды InfiniBand

    if output.strip() == EXPECTED_IB_COUNT.strip():
        log_message = f"Проверка количества InfiniBand интерфейсов на {hostname} прошла успешно. Обнаружено: {EXPECTED_IB_COUNT}"
        logging.info(log_message)
        print(f"\033[92mПроверка InfiniBand интерфейсов на {hostname} прошла успешно. Обнаружено: {EXPECTED_IB_COUNT}\033[0m")
        return True
    else:
        log_message = f"Проверка количества InfiniBand интерфейсов на {hostname} не прошла. Ожидалось: '{EXPECTED_IB_COUNT}', обнаружено: '{output}'."
        logging.warning(log_message)
        print(f"\033[93mПроверка InfiniBand интерфейсов на {hostname} не прошла. Ожидалось: '{EXPECTED_IB_COUNT}', обнаружено: '{output}'.\033[0m")
        return False

def check_server(hostname, key_path):
    """Подключается к удаленному серверу и выполняет все проверки."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key = paramiko.RSAKey.from_private_key_file(key_path)

    try:
        log_message = f"Подключение к {hostname}..."
        logging.info(log_message)
        print(log_message)
        client.connect(hostname=hostname, username='ubuntu', pkey=private_key, timeout=10)
        log_message = f"Успешно подключено к {hostname}."
        logging.info(log_message)
        print(log_message)

        cpu_check_passed = check_cpu_info(client, hostname)
        memory_check_passed = check_memory_info(client, hostname)
        network_check_passed = check_network_interfaces(client, hostname)
        infiniband_check_passed = check_infiniband_interfaces(client, hostname)

        return (cpu_check_passed and memory_check_passed and
                network_check_passed and infiniband_check_passed)

    except paramiko.AuthenticationException:
        log_message = f"Ошибка аутентификации при подключении к {hostname}."
        logging.error(log_message)
        print(f"\033[91m{log_message}\033[0m")
        return False
    except paramiko.SSHException as e:
        log_message = f"Ошибка SSH при подключении к {hostname}: {e}"
        logging.error(log_message)
        print(f"\033[91m{log_message}\033[0m")
        return False
    except Exception as e:
        log_message = f"Произошла ошибка при работе с {hostname}: {e}"
        logging.error(log_message)
        print(f"\033[91m{log_message}\033[0m")
        return False
    finally:
        if client:
            client.close()
            log_message = f"Соединение с {hostname} закрыто."
            logging.info(log_message)
            print(log_message)

if __name__ == "__main__":
    try:
        with open('ips.txt', 'r', encoding='utf-8') as f:
            ip_list = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        log_message = "Файл 'ips.txt' не найден."
        logging.error(log_message)
        print(f"\033[91m{log_message}\033[0m")
        exit(1)

    if not ip_list:
        log_message = "Файл 'ips.txt' пуст."
        logging.info(log_message)
        print(log_message)
        exit(0)

    for ip in ip_list:
        print(f"\n{'='*30} Проверка IP: {ip} {'='*30}")
        if check_server(ip, SSH_KEY_PATH):
            print(f"\033[94m{'='*20} Все проверки для {ip} пройдены успешно! {'='*20}\033[0m")
        else:
            print(f"\033[91m{'='*20} Одна или несколько проверок для {ip} не пройдены. {'='*20}\033[0m")
        time.sleep(1)
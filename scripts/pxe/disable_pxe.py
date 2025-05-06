import paramiko
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# === Настройки ===
IP_LIST_FILE = "ips.txt"
PRIVATE_KEY_PATH = "C:\\Users\\eleonora.chorshanbie\\Downloads\\eleonora_test_gpu_sines"  # ← Заменить на путь к твоему ключу
USERNAME = "ubuntu"           # ← Заменить на SSH-пользователя
SSH_PORT = 22
MAX_WORKERS = 5                      # Кол-во параллельных подключений
DELAY_BETWEEN_COMMANDS = 5          # секунд

# Команды для запуска
COMMANDS = [
    "sudo -i",
    "sudo mst start",
    "for i in {0..7}; do sudo mlxconfig -d /dev/mst/mt4129_pciconf$i -y set EXP_ROM_UEFI_x86_ENABLE=0 EXP_ROM_UEFI_ARM_ENABLE=0 EXP_ROM_PXE_ENABLE=0; done",
    "reboot"
]

# === Настройка логгера ===
logging.basicConfig(
    filename="ssh_execution.log",
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("[%(levelname)s] %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

def run_commands_over_ssh(ip, username, key_path):
    logging.info(f"Подключение к {ip}")
    try:
        key = paramiko.RSAKey.from_private_key_file(key_path)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port=SSH_PORT, username=username, pkey=key, timeout=10)

        shell = ssh.invoke_shell()
        time.sleep(1)

        for cmd in COMMANDS:
            shell.send(cmd + "\n")
            time.sleep(DELAY_BETWEEN_COMMANDS)

        output = shell.recv(10000).decode()
        logging.info(f"[{ip}] Успешно выполнено.")
        logging.debug(f"[{ip}] Вывод команд:\n{output}")

        ssh.close()

    except Exception as e:
        logging.error(f"[{ip}] Ошибка: {e}")

def main():
    with open(IP_LIST_FILE, "r") as file:
        ip_list = [line.strip() for line in file if line.strip()]

    logging.info(f"Всего IP: {len(ip_list)}. Запуск с {MAX_WORKERS} потоками.")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_commands_over_ssh, ip, USERNAME, PRIVATE_KEY_PATH): ip for ip in ip_list}

        for future in as_completed(futures):
            ip = futures[future]
            try:
                future.result()
            except Exception as exc:
                logging.error(f"[{ip}] Ошибка выполнения потока: {exc}")

if __name__ == "__main__":
    main()

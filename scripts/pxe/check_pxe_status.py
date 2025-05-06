import paramiko
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# === Настройки ===
IP_LIST_FILE = "ips.txt"
PRIVATE_KEY_PATH = "C:\\Users\\eleonora.chorshanbie\\Downloads\\eleonora_test_gpu_sines"
USERNAME = "ubuntu"
SSH_PORT = 22
MAX_WORKERS = 5
DELAY_BETWEEN_COMMANDS = 2  # чуть меньше, т.к. команд меньше

# === Настройка логгера ===
logging.basicConfig(
    filename="pxe_check.log",
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("[%(levelname)s] %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)


def execute_ssh_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.read().decode() + stderr.read().decode()


def check_pxe_disabled(ip, username, key_path):
    logging.info(f"Подключение к {ip} для проверки PXE")
    try:
        key = paramiko.RSAKey.from_private_key_file(key_path)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port=SSH_PORT, username=username, pkey=key, timeout=10)

        # Запускаем mst
        execute_ssh_command(ssh, "sudo mst start")
        time.sleep(1)

        for i in range(8):
            cmd = f"sudo mlxconfig -d /dev/mst/mt4129_pciconf{i} q | grep -E 'PXE|UEFI'"
            output = execute_ssh_command(ssh, cmd)

            if re.search(r"EXP_ROM_UEFI_x86_ENABLE\s+True\(1\)", output):
                raise AssertionError(f"[{ip}] PXE still enabled on interface {i}: EXP_ROM_UEFI_x86_ENABLE")
            if re.search(r"EXP_ROM_UEFI_ARM_ENABLE\s+True\(1\)", output):
                raise AssertionError(f"[{ip}] PXE still enabled on interface {i}: EXP_ROM_UEFI_ARM_ENABLE")
            if re.search(r"EXP_ROM_PXE_ENABLE\s+True\(1\)", output):
                raise AssertionError(f"[{ip}] PXE still enabled on interface {i}: EXP_ROM_PXE_ENABLE")

        logging.info(f"[{ip}] PXE отключён на всех интерфейсах.")
        ssh.close()

    except AssertionError as ae:
        logging.error(str(ae))
    except Exception as e:
        logging.error(f"[{ip}] Ошибка: {e}")


def main():
    with open(IP_LIST_FILE, "r") as file:
        ip_list = [line.strip() for line in file if line.strip()]

    logging.info(f"Всего IP: {len(ip_list)}. Запуск проверки с {MAX_WORKERS} потоками.")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_pxe_disabled, ip, USERNAME, PRIVATE_KEY_PATH): ip for ip in ip_list}

        for future in as_completed(futures):
            ip = futures[future]
            try:
                future.result()
            except Exception as exc:
                logging.error(f"[{ip}] Ошибка выполнения потока: {exc}")


if __name__ == "__main__":
    main()
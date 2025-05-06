import paramiko
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# === Конфигурация ===
IP_LIST_FILE = "ips.txt"
PRIVATE_KEY_PATH = "C:\\Users\\eleonora.chorshanbie\\Downloads\\eleonora_test_gpu_sines"  # ← Укажи путь
USERNAME = "ubuntu"           # ← Укажи логин
SSH_PORT = 22
MAX_WORKERS = 10

# === Настройка логгера ===
logging.basicConfig(
    filename="ssh_availability.log",
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logging.getLogger().addHandler(console)

def check_ssh(ip, username, key_path):
    try:
        key = paramiko.RSAKey.from_private_key_file(key_path)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(
            hostname=ip,
            port=SSH_PORT,
            username=username,
            pkey=key,
            timeout=10,
            banner_timeout=10,
            auth_timeout=10
        )

        ssh.close()
        logging.info(f"[{ip}] ✅ Успешное подключение.")
    except paramiko.AuthenticationException:
        logging.warning(f"[{ip}] ❌ Ошибка аутентификации.")
    except paramiko.SSHException as e:
        logging.warning(f"[{ip}] ❌ SSH ошибка: {str(e)}")
    except Exception as e:
        logging.warning(f"[{ip}] ❌ Сетевая/непредвиденная ошибка: {str(e)}")

def main():
    with open(IP_LIST_FILE, "r") as f:
        ip_list = [line.strip() for line in f if line.strip()]

    logging.info(f"🔍 Проверка SSH-доступности для {len(ip_list)} IP...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_ssh, ip, USERNAME, PRIVATE_KEY_PATH): ip for ip in ip_list}

        for future in as_completed(futures):
            ip = futures[future]
            try:
                future.result()
            except Exception as e:
                logging.error(f"[{ip}] ❗ Необработанная ошибка: {e}")

if __name__ == "__main__":
    main()

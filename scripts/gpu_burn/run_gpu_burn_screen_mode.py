import paramiko

PRIVATE_KEY_PATH = "C:\\Users\\eleonora.chorshanbie\\Downloads\\eleonora_test_gpu_sines"  # Укажи свой путь к приватному ключу
USERNAME = "ubuntu"                      # Замени на имя SSH-пользователя
GPU_BURN_TIME_SECONDS = 3600                        # Время работы gpu_burn — 1 час

def read_ips(file_path="ips.txt"):
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def run_gpu_burn_on_host(ip, username, private_key_path):
    print(f"🔌 Connecting to {ip}...")

    key = paramiko.RSAKey.from_private_key_file(private_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(ip, username=username, pkey=key)

        commands = [
            # Установка screen
            "sudo apt-get update && sudo apt-get install -y screen",

            # Клонирование и сборка gpu-burn
            "rm -rf gpu-burn && git clone https://github.com/wilicc/gpu-burn.git",
            "cd gpu-burn && make",

            # Запуск gpu_burn в screen-сессии
            f'screen -dmS gpu_burn_session bash -c "cd gpu-burn && ./gpu_burn {GPU_BURN_TIME_SECONDS} > gpu_burn_output.log 2>&1"'
        ]

        for cmd in commands:
            print(f"[{ip}] 🛠 Executing: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                err = stderr.read().decode()
                print(f"[{ip}] ⚠️ Error: {err.strip()}")

        print(f"[{ip}] ✅ GPU Burn started in screen session.\n")

    except Exception as e:
        print(f"[{ip}] ❌ ERROR: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    ips = read_ips()
    for ip in ips:
        run_gpu_burn_on_host(ip, USERNAME, PRIVATE_KEY_PATH)

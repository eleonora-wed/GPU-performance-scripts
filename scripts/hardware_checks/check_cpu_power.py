import paramiko

SSH_KEY_PATH = "C:\\Users\\eleonora.chorshanbie\\Downloads\\eleonora_test_gpu_sines"  # Укажи путь к приватному ключу
SSH_USER = "ubuntu"  # Имя пользователя для SSH
IPS_FILE = "ips.txt"

CHECK_GOVERNOR_CMD = "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
CHECK_DISABLE_CMD = "cat /sys/devices/system/cpu/cpu*/cpuidle/state*/disable"

SERVICE_UNIT_COMMAND = """sudo tee /etc/systemd/system/disable-cstates.service > /dev/null << EOF
[Unit]
Description=Disable CPU C-States
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c "for i in /sys/devices/system/cpu/cpu*/cpuidle/state*/disable; do echo 1 > \\$i; done"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
"""

ENABLE_SERVICE_CMDS = [
    "sudo systemctl daemon-reload",
    "sudo systemctl enable disable-cstates.service",
    "sudo systemctl start disable-cstates.service"
]

def run_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

def connect_ssh(ip):
    key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=SSH_USER, pkey=key)
    return ssh

def check_and_fix(ip):
    print(f"\n🔗 Подключаюсь к {ip}...")
    try:
        ssh = connect_ssh(ip)
        governor_output, _ = run_command(ssh, CHECK_GOVERNOR_CMD)
        disable_output, _ = run_command(ssh, CHECK_DISABLE_CMD)

        governor_issue = any(line.strip() != "performance" for line in governor_output.splitlines())
        disable_issue = any(line.strip() != "1" for line in disable_output.splitlines())

        if not governor_issue and not disable_issue:
            print(f"✅ {ip}: Всё в порядке")
        else:
            print(f"⚠️ {ip}: Найдены отклонения:")

            if governor_issue:
                print(f"  - Проблемы с scaling_governor")
            if disable_issue:
                print(f"  - Проблемы с cpuidle/state*/disable")

            # Создаем и запускаем сервис
            run_command(ssh, SERVICE_UNIT_COMMAND)
            for cmd in ENABLE_SERVICE_CMDS:
                run_command(ssh, cmd)

            # Повторная проверка
            governor_output, _ = run_command(ssh, CHECK_GOVERNOR_CMD)
            disable_output, _ = run_command(ssh, CHECK_DISABLE_CMD)

            # Проверяем снова, есть ли проблемы
            governor_issue = any(line.strip() != "performance" for line in governor_output.splitlines())
            disable_issue = any(line.strip() != "1" for line in disable_output.splitlines())

            if not governor_issue and not disable_issue:
                print(f"✅ {ip}: Всё исправлено")
            else:
                print(f"❌ {ip}: После исправления всё ещё есть проблемы:")
                if governor_issue:
                    print(f"  - Проблемы с scaling_governor")
                if disable_issue:
                    print(f"  - Проблемы с cpuidle/state*/disable")

        ssh.close()
    except Exception as e:
        print(f"🚨 Ошибка при работе с {ip}: {e}")

def main():
    with open(IPS_FILE, "r") as file:
        ips = [line.strip() for line in file if line.strip()]
    for ip in ips:
        check_and_fix(ip)

if __name__ == "__main__":
    main()

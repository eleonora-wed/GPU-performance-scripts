import paramiko
import re

IP_FILE = "ips2.txt"
PRIVATE_KEY_PATH = "C:\\Users\\eleonora.chorshanbie\\Downloads\\eleonora_test_gpu_sines"
USERNAME = "ubuntu"

def check_firmware_status(ip):
    try:
        print(f"\nConnecting to {ip}...")

        key = paramiko.RSAKey.from_private_key_file(PRIVATE_KEY_PATH)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=USERNAME, pkey=key)

        stdin, stdout, stderr = ssh.exec_command("sudo mlxfwmanager --query --online")
        output = stdout.read().decode()
        error = stderr.read().decode()

        if error:
            print(f"[{ip}] ❌ ERROR during command execution:\n{error}")
            return

        # Проверка статуса
        status_list = re.findall(r"Status:\s+(.*?)\n", output)

        if any("Update required" in status for status in status_list):
            print(f"[{ip}] ❌ FAILED: At least one device needs an update")
        else:
            print(f"[{ip}] ✅ PASSED: All devices are up to date")

        ssh.close()

    except Exception as e:
        print(f"[{ip}] ❌ ERROR: {str(e)}")


def main():
    with open(IP_FILE, "r") as f:
        ips = [line.strip() for line in f if line.strip()]

    for ip in ips:
        check_firmware_status(ip)

if __name__ == "__main__":
    main()

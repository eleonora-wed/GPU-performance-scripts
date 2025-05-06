import paramiko
import os
import re
import subprocess

def run_remote_command(hostname, username, private_key_path, command):
    """Выполняет команду на удаленном сервере через SSH."""
    try:
        key = paramiko.RSAKey.from_private_key_file(private_key_path)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Автоматически добавлять хосты в known_hosts (не рекомендуется для production)

        print(f"Подключаюсь к {hostname}...")
        client.connect(hostname=hostname, username=username, pkey=key)

        print(f"Выполняю команду: {command}")
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()

        if error:
            print(f"❌ Ошибка на {hostname}: {error}")
            return None
        else:
            print(f"Вывод на {hostname}:\n{output}")
            return output
    except paramiko.AuthenticationException:
        print(f"❌ Ошибка аутентификации на {hostname}. Проверьте ключ или имя пользователя.")
        return None
    except paramiko.SSHException as e:
        print(f"❌ Ошибка SSH на {hostname}: {e}")
        return None
    except FileNotFoundError:
        print(f"❌ Ошибка: Файл приватного ключа не найден по пути: {private_key_path}")
        return None
    except Exception as e:
        print(f"❌ Произошла ошибка при подключении к {hostname}: {e}")
        return None
    finally:
        if 'client' in locals():
            client.close()
            print(f"Соединение с {hostname} закрыто.")

def check_disk_count(output, expected_count):
    """Проверяет, что количество строк в выводе соответствует ожидаемому, с визуальными знаками."""
    if output is not None:
        lines = output.strip().split('\n')
        actual_count = len(lines)
        if actual_count == expected_count:
            print(f"✅ Ожидаемое количество дисков ({expected_count}) совпадает с фактическим ({actual_count}).")
            return True
        else:
            print(f"❌ Внимание: Ожидалось {expected_count} дисков, найдено {actual_count}.")
            return False
    else:
        return False

def check_gpu_info(output, expected_output):
    """Проверяет, что вывод команды nvidia-smi соответствует ожидаемому."""
    if output is not None and output.strip() == expected_output.strip():
        print(f"✅ Вывод nvidia-smi соответствует ожидаемому: '{expected_output.strip()}'")
        return True
    else:
        print(f"❌ Внимание: Вывод nvidia-smi ('{output}') не соответствует ожидаемому: '{expected_output.strip()}'")
        return False

def count_active_ib_ports(hostname, username, private_key_path):
    """Подсчитывает количество активных InfiniBand портов с заданными параметрами на удаленном сервере."""
    command = 'ibstat'
    output = run_remote_command(hostname, username, private_key_path, command)
    if not output:
        print("❌ Ошибка: Не удалось получить вывод команды ibstat")
        return 0

    # Разделяем вывод на блоки CA
    ca_blocks = re.split(r"CA '.*?'", output)[1:]  # Пропускаем первый пустой элемент
    count = 0

    for block in ca_blocks:
        # Ищем информацию о порте
        port_section = re.search(r"Port \d+:\n(.*?)(?=\n\s*\n|$)", block, re.DOTALL)
        if not port_section:
            continue
        port_info = port_section.group(1)

        # Извлекаем параметры
        state = re.search(r"State:\s+(\w+)", port_info)
        rate = re.search(r"Rate:\s+(\d+)", port_info)
        link_layer = re.search(r"Link layer:\s+(\w+)", port_info)

        # Проверяем соответствие критериям
        if (state and state.group(1) == "Active" and
            rate and rate.group(1) == "400" and
            link_layer and link_layer.group(1) == "InfiniBand"):
            count += 1

    return count

if __name__ == "__main__":
    ips_file_path = "ips.txt"
    private_key_path = r"C:\Users\eleonora.chorshanbie\Downloads\eleonora_test_gpu_sines"
    username = "ubuntu"  # Укажи имя пользователя для подключения
    expected_gpu_output = "8 NVIDIA 80GB"  # Ожидаемый вывод nvidia-smi
    expected_ib_count = 8  # Ожидаемое количество InfiniBand интерфейсов

    if not os.path.exists(ips_file_path):
        print(f"❌ Ошибка: Файл с IP-адресами '{ips_file_path}' не найден.")
        exit(1)

    with open(ips_file_path, 'r') as f:
        public_ips = [line.strip() for line in f if line.strip()]

    passed_all_checks = []
    failed_any_check = []

    for ip in public_ips:
        print(f"\n--- Обработка IP: {ip} ---")
        all_checks_passed = True

        # Проверка 3.5T дисков
        print("Проверка количества дисков размером 3.5T:")
        command_3_5t = 'lsblk -o NAME,TYPE,SIZE | grep "disk" | grep "3.5T"'
        output_3_5t = run_remote_command(ip, username, private_key_path, command_3_5t)
        if not check_disk_count(output_3_5t, 6):
            all_checks_passed = False

        print("\nПроверка количества дисков размером 1.7T:")
        # Проверка 1.7T дисков
        command_1_7t = 'lsblk -o NAME,TYPE,SIZE | grep "disk" | grep "1.7T"'
        output_1_7t = run_remote_command(ip, username, private_key_path, command_1_7t)
        if not check_disk_count(output_1_7t, 2):
            all_checks_passed = False

        print("\nПроверка информации о GPU:")
        # Проверка информации о GPU
        command_gpu_info = 'nvidia-smi --query-gpu=gpu_name,memory.total --format=csv,noheader | awk -F\',\'' \
                          ' \'{name=$1; match(name, /.* ([0-9]+GB)/, arr); if (arr[1]) {sub(/ .*/, " " arr[1], name); print name}}\' | sort | uniq -c'
        output_gpu_info = run_remote_command(ip, username, private_key_path, command_gpu_info)
        if not check_gpu_info(output_gpu_info, expected_gpu_output):
            all_checks_passed = False

        print("\nПроверка активных InfiniBand портов:")
        # Проверка InfiniBand портов
        ib_port_count = count_active_ib_ports(ip, username, private_key_path)
        print(f"Найдено активных IB-портов со скоростью 400: {ib_port_count}")
        if ib_port_count != expected_ib_count:
            print(f"❌ Ошибка: Ожидается {expected_ib_count} активных IB-портов.")
            all_checks_passed = False
        else:
            print(f"✅ Все {expected_ib_count} IB-портов в норме.")

        # Добавляем IP в соответствующий список
        if all_checks_passed:
            passed_all_checks.append(ip)
        else:
            failed_any_check.append(ip)

    print("\nСкрипт завершен.")
    print("\n--- Итоговый отчет ---")
    print("IP-адреса, успешно прошедшие все проверки:")
    if passed_all_checks:
        for ip in passed_all_checks:
            print(f"✅ {ip}")
    else:
        print("Нет IP-адресов, прошедших все проверки.")

    print("\nIP-адреса, не прошедшие хотя бы одну проверку:")
    if failed_any_check:
        for ip in failed_any_check:
            print(f"❌ {ip}")
    else:
        print("Нет IP-адресов, не прошедших проверки.")
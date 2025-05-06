#!/usr/bin/env python3
import os
import paramiko
import logging
import sys
from pathlib import Path

# Настройка логирования с явным указанием кодировки
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ssh_deploy_key.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Публичный ключ, который нужно добавить
PUBLIC_KEY = "ecdsa-sha2-nistp521 AAAAE2VjZHNhLXNoYTItbmlzdHA1MjEAAAAIbmlzdHA1MjEAAACFBAFvGdA7AibL8lEFIxHkX8ZmcKi8vYc1e/yaaddkDtz3kkWUmbHjImsJg8pr26+LVjAvyZvUXuXLMLFTQ+2atyzdLQCT5RkqWqn6mMAfRMdyrxnkuI+8eg8esiaCOBXDdlKM8AQ/0kh0f/Rn0hRGIhlS1efpwy8Ua8U+8ANeiH5NffXwDQ== christofstuehrmann@MacBook-Pro-von-Christof.local"

def add_ssh_key_to_server(ip, private_key_path, username='ubuntu'):
    """
    Подключается к серверу по SSH и добавляет публичный ключ в authorized_keys
    """
    try:
        # Создаем SSH клиент
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Подключаемся к серверу
        print(f"[{ip}] Попытка подключения...")
        logger.info(f"Подключение к {ip} с ключом {private_key_path}")
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
        client.connect(
            hostname=ip,
            username=username,
            pkey=private_key,
            timeout=10
        )
        print(f"[{ip}] Успешное подключение по SSH")
        
        # Команды для добавления ключа без дублирования
        commands = [
            f'mkdir -p /home/{username}/.ssh',
            f'touch /home/{username}/.ssh/authorized_keys',
            f'grep -q "{PUBLIC_KEY}" /home/{username}/.ssh/authorized_keys || echo "{PUBLIC_KEY}" >> /home/{username}/.ssh/authorized_keys',
            f'chmod 700 /home/{username}/.ssh',
            f'chmod 600 /home/{username}/.ssh/authorized_keys',
            f'chown -R {username}:{username} /home/{username}/.ssh'
        ]
        
        # Выполняем команды
        print(f"[{ip}] Добавление ключа...")
        for cmd in commands:
            stdin, stdout, stderr = client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error = stderr.read().decode('utf-8')
                error_msg = f"Ошибка при выполнении '{cmd}' на {ip}: {error}"
                print(f"[{ip}] {error_msg}")
                logger.error(error_msg)
                return False
        
        success_msg = f"Ключ успешно добавлен на {ip}"
        print(f"[{ip}] УСПЕХ: {success_msg}")
        logger.info(success_msg)
        return True
    
    except Exception as e:
        error_msg = f"Не удалось подключиться к {ip}: {str(e)}"
        print(f"[{ip}] ОШИБКА: {error_msg}")
        logger.error(error_msg)
        return False
    
    finally:
        if 'client' in locals() and client:
            client.close()

def main():
    """
    Основная функция для обработки всех IP из файла
    """
    print("=" * 60)
    print("Скрипт для развертывания SSH ключей на удаленных серверах")
    print("=" * 60)
    
    # Запрос пути к приватному ключу с проверкой
    while True:
        private_key_path = input("Введите полный путь к приватному SSH ключу: ").strip()
        
        # Если пользователь ввел путь в кавычках, убираем их
        if (private_key_path.startswith('"') and private_key_path.endswith('"')) or \
           (private_key_path.startswith("'") and private_key_path.endswith("'")):
            private_key_path = private_key_path[1:-1]
        
        # Проверка наличия ключа
        if not private_key_path:
            print("ОШИБКА: Путь к ключу не может быть пустым. Попробуйте снова.")
            continue
        
        if not os.path.isfile(private_key_path):
            print(f"ОШИБКА: Файл ключа '{private_key_path}' не найден. Проверьте путь и повторите ввод.")
            try:
                logger.error(f"Файл ключа '{private_key_path}' не найден")
            except UnicodeEncodeError:
                logger.error("Файл ключа не найден (ошибка кодировки пути)")
            continue
        
        # Если дошли до этой точки, значит ключ найден
        break
    
    # Проверка наличия файла с IP
    if not os.path.isfile("ips.txt"):
        error_msg = "Файл ips.txt не найден в текущей директории"
        print(f"ОШИБКА: {error_msg}")
        logger.error(error_msg)
        return
    
    try:
        # Чтение списка IP из файла
        with open("ips.txt", "r") as f:
            ips = [line.strip() for line in f if line.strip()]
    except Exception as e:
        error_msg = f"Ошибка при чтении файла ips.txt: {str(e)}"
        print(f"ОШИБКА: {error_msg}")
        logger.error(error_msg)
        return
    
    if not ips:
        print("ОШИБКА: Файл ips.txt пуст или не содержит IP-адресов")
        logger.error("Файл ips.txt пуст или не содержит IP-адресов")
        return
    
    print(f"Найдено {len(ips)} IP-адресов в файле")
    logger.info(f"Найдено {len(ips)} IP-адресов в файле")
    
    # Счетчики для статистики
    success_count = 0
    fail_count = 0
    
    # Обработка каждого IP
    for i, ip in enumerate(ips, 1):
        print(f"\nОбработка сервера {i}/{len(ips)}: {ip}")
        if add_ssh_key_to_server(ip, private_key_path):
            success_count += 1
        else:
            fail_count += 1
    
    # Вывод статистики
    print("\n" + "=" * 60)
    print(f"ИТОГИ РАЗВЕРТЫВАНИЯ:")
    print(f"✓ Успешно: {success_count} серверов")
    print(f"✗ Ошибки: {fail_count} серверов")
    print("=" * 60)
    
    logger.info(f"Итоги: успешно добавлен ключ на {success_count} серверов, ошибки на {fail_count} серверов")

if __name__ == "__main__":
    main()
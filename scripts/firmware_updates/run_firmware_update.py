import paramiko
import subprocess
import time
import logging

# Настройка логгирования
logging.basicConfig(filename='log.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Путь к приватному ключу SSH
private_key_path = r'C:\Users\eleonora.chorshanbie\Downloads\eleonora_test_gpu_sines'  # Замените на ваш фактический путь

# Имя пользователя для подключения по SSH
ssh_username = 'ubuntu'  # Замените на ваше имя пользователя

QUERY_TIMEOUT = 60  # Максимальное время ожидания выполнения команды mlxfwmanager --query (в секундах)
MAX_RETRIES = 3     # Максимальное количество попыток подключения и выполнения команды

def execute_remote_command(client, command, timeout=None):
    """Выполняет команду на удалённом сервере с возможностью установки таймаута и возвращает вывод."""
    try:
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        output = ""
        start_time = time.time()
        while not stdout.channel.exit_status_ready():
            if timeout and (time.time() - start_time) > timeout:
                stdout.channel.close()
                stderr.channel.close()
                return None, "Timeout"
            try:
                line = stdout.readline()
                if line:
                    output += line
            except Exception:
                pass
            time.sleep(0.1)
        
        # Получаем оставшийся вывод
        output += stdout.read().decode('utf-8', errors='ignore')
        errors = stderr.read().decode('utf-8', errors='ignore')
        return output, errors
    except Exception as e:
        return None, str(e)

def check_fw_status(output):
    """Анализирует вывод mlxfwmanager --query --online и возвращает True, если требуется обновление."""
    for line in output.splitlines():
        if 'Status:' in line and 'Update required' in line:
            return True
    return False

def perform_fw_update(client):
    """Запускает обновление прошивки и перезагружает сервер."""
    command = 'sudo mlxfwmanager --update --online'
    try:
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)

        # Автоматически отвечаем 'y' на запрос подтверждения
        stdin.write('y\n')
        stdin.flush()

        output = ""
        while not stdout.channel.exit_status_ready():
            line = stdout.readline()
            if not line:
                continue
            line = line.strip()
            print(line)
            logging.info(line)
            output += line + '\n'
            if 'Restart needed for updates to take effect.' in line:
                print("Обновление завершено. Требуется перезагрузка.")
                logging.info("Обновление завершено. Требуется перезагрузка.")
                break
        
        # Получаем оставшийся вывод
        remaining = stdout.read().decode('utf-8', errors='ignore')
        output += remaining
        errors = stderr.read().decode('utf-8', errors='ignore')
        
        if errors:
            print(f"Ошибка при обновлении: {errors}")
            logging.error(f"Ошибка при обновлении: {errors}")
            return False

        if 'Restart needed for updates to take effect.' in output:
            print("Выполняю перезагрузку...")
            logging.info("Выполняю перезагрузку...")
            client.exec_command('sudo reboot')
            return True
        else:
            print("Обновление не завершилось успешно.")
            logging.warning("Обновление не завершилось успешно.")
            return False

    except Exception as e:
        print(f"Ошибка при выполнении обновления: {e}")
        logging.error(f"Ошибка при выполнении обновления: {e}")
        return False

def connect_to_server(ip):
    """Создает SSH подключение к серверу"""
    client = None
    try:
        key = paramiko.RSAKey.from_private_key_file(private_key_path)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Подключение к {ip}...")
        logging.info(f"Подключение к {ip}...")
        client.connect(ip, username=ssh_username, pkey=key, timeout=10)
        print("Подключено.")
        logging.info("Подключено.")
        return client
    except Exception as e:
        if client:
            client.close()
        raise e

def main():
    """Основная функция скрипта."""
    try:
        with open('ips.txt', 'r') as f:
            ip_addresses = [line.strip() for line in f]
    except FileNotFoundError:
        print("Ошибка: Файл ips.txt не найден.")
        logging.error("Ошибка: Файл ips.txt не найден.")
        return

    for ip in ip_addresses:
        print(f"\n--- Обработка IP: {ip} ---")
        logging.info(f"--- Обработка IP: {ip} ---")

        client = None
        
        # Попытка подключения к серверу
        for retry in range(MAX_RETRIES):
            try:
                client = connect_to_server(ip)
                break  # Успешное подключение
            except paramiko.AuthenticationException:
                print(f"Ошибка аутентификации для IP: {ip}. Проверьте приватный ключ и имя пользователя.")
                logging.error(f"Ошибка аутентификации для IP: {ip}. Проверьте приватный ключ и имя пользователя.")
                break  # Нет смысла повторять при ошибке аутентификации
            except Exception as e:
                print(f"Ошибка при подключении к {ip} (попытка {retry + 1}/{MAX_RETRIES}): {e}")
                logging.error(f"Ошибка при подключении к {ip} (попытка {retry + 1}/{MAX_RETRIES}): {e}")
                if retry < MAX_RETRIES - 1:
                    time.sleep(5)  # Пауза перед следующей попыткой
        
        if not client:
            print(f"Не удалось подключиться к {ip} после {MAX_RETRIES} попыток.")
            logging.error(f"Не удалось подключиться к {ip} после {MAX_RETRIES} попыток.")
            continue  # Переходим к следующему IP

        # Выполнение проверки прошивки
        try:
            query_command = 'sudo mlxfwmanager --query --online'
            query_successful = False
            
            for retry in range(MAX_RETRIES):
                print(f"Выполнение команды: {query_command} на {ip} (попытка {retry + 1}/{MAX_RETRIES})...")
                logging.info(f"Выполнение команды: {query_command} на {ip} (попытка {retry + 1}/{MAX_RETRIES})...")
                
                output, errors = execute_remote_command(client, query_command, timeout=QUERY_TIMEOUT)
                
                if output is None:
                    print(f"Ошибка или таймаут при выполнении команды: {errors}")
                    logging.error(f"Ошибка или таймаут при выполнении команды: {errors}")
                    
                    # Переподключаемся если таймаут
                    if errors == "Timeout":
                        try:
                            client.close()
                        except:
                            pass
                        
                        try:
                            client = connect_to_server(ip)
                        except Exception as e:
                            print(f"Не удалось переподключиться к {ip}: {e}")
                            logging.error(f"Не удалось переподключиться к {ip}: {e}")
                            client = None
                            break
                    
                    if retry < MAX_RETRIES - 1:
                        time.sleep(5)
                    continue
                
                # Обработка вывода команды
                print("Вывод команды:")
                print(output)
                logging.info(f"Вывод команды:\n{output}")
                query_successful = True
                
                # Проверка необходимости обновления
                if check_fw_status(output):
                    print(f"Для IP: {ip} требуется обновление.")
                    logging.info(f"Для IP: {ip} требуется обновление.")
                    if perform_fw_update(client):
                        print(f"Перезагрузка выполнена для IP: {ip}.")
                        logging.info(f"Перезагрузка выполнена для IP: {ip}.")
                    else:
                        print(f"Не удалось выполнить обновление или перезагрузку для IP: {ip}.")
                        logging.warning(f"Не удалось выполнить обновление или перезагрузку для IP: {ip}.")
                else:
                    print(f"Обновление не требуется для IP: {ip}")
                    logging.info(f"Обновление не требуется для IP: {ip}")
                
                break  # Успешно выполнили команду
            
            if not query_successful:
                print(f"Не удалось выполнить проверку прошивки для {ip} после {MAX_RETRIES} попыток.")
                logging.error(f"Не удалось выполнить проверку прошивки для {ip} после {MAX_RETRIES} попыток.")
                
        finally:
            # Закрытие соединения
            if client:
                try:
                    client.close()
                    print(f"Соединение с {ip} закрыто.")
                    logging.info(f"Соединение с {ip} закрыто.")
                except:
                    pass

if __name__ == "__main__":
    main()
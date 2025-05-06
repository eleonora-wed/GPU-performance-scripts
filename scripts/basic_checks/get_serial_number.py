import paramiko

# Чтение IP-адресов из файла ips3.txt
def read_ips_from_file(file_path):
    with open(file_path, 'r') as file:
        # Чтение всех строк, удаление лишних пробелов и пустых строк
        return [line.strip() for line in file.readlines() if line.strip()]

# Путь к вашему приватному SSH ключу
ssh_key_path = "C:\\Users\\eleonora.chorshanbie\\Downloads\\qa_test_gpu_sines"  # Замените на путь к вашему ключу

# Команда для получения серийного номера
command = 'sudo dmidecode -t system | grep "Serial Number"'

# Функция для выполнения команды на сервере
def get_serial_number(ip):
    try:
        # Настройка SSH клиента
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Подключение к серверу через SSH
        client.connect(ip, username='ubuntu', key_filename=ssh_key_path)
        
        # Выполнение команды
        stdin, stdout, stderr = client.exec_command(command)
        
        # Чтение и обработка вывода
        output = stdout.read().decode('utf-8').strip()
        
        # Проверка на наличие серийного номера в выводе
        if output:
            serial_number = output.split(":")[-1].strip()
            print(f"{ip} = {serial_number}")
        else:
            print(f"{ip} = Серийный номер не найден")
        
        # Закрытие соединения
        client.close()
    
    except Exception as e:
        print(f"Ошибка при подключении к {ip}: {e}")

# Чтение IP-адресов из файла
ips = read_ips_from_file('ips3.txt')

# Пройдем по всем IP-адресам и получим серийный номер
for ip in ips:
    get_serial_number(ip)

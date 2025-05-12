def generate_inventory(ip_file, output_file, reverse=False):
    with open(ip_file, 'r') as f:
        ips = [line.strip() for line in f if line.strip()]

    if reverse:
        servers = ips[::2]  # IP на нечётных позициях
        clients = ips[1::2]  # IP на чётных позициях
    else:
        servers = ips[1::2]
        clients = ips[::2]
        # IP на чётных позициях

    with open(output_file, 'w') as f:
        f.write('[qperf_server]\n')
        for i, ip in enumerate(servers, 1):
            f.write(f'server{i} ansible_host={ip}\n')

        f.write('\n[qperf_client]\n')
        for i, ip in enumerate(clients, 1):
            f.write(f'client{i} ansible_host={ip}\n')

        f.write('\n[qperf_pairs]\n')
        for i in range(1, min(len(servers), len(clients)) + 1):
            f.write(f'pair{i} ansible_client=client{i} ansible_server=server{i}\n')

        f.write('\n[all:vars]\n')
        f.write('ansible_user=ubuntu\n')
        f.write('ansible_ssh_private_key_file=<ADD PATH TO SSH KEY FILE>\n')

generate_inventory('ip', 'inventory.ini', reverse=True)
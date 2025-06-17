from template_loader import load_template
import threading, argparse, paramiko

# carregar targets
with open("targets.txt") as f:
    targets = [line.strip() for line in f if line.strip()]

# carregar servidores
with open("servers.txt") as f:
    servers = [line.strip() for line in f if line.strip()]

# dividir targets igualmente
def split_targets(targets, n):
    k, m = divmod(len(targets), n)
    return [targets[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]

divided_targets = split_targets(targets, len(servers))

# carregar template
template = load_template("templates/nuclei.yaml")

def deploy_and_execute(server, assigned_targets, flag):
    private_key_path = "C:Users/user/.ssh/id_rsa"
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
    print(f"[!] Queued server: {server}")
    client.connect(hostname=server.split("@")[1], username=server.split("@")[0], pkey=private_key, timeout=5)
    
    # instalar ferramenta
    if flag == 1:
        print(f"[!] Installing toolset on server: {server}")
        install_commands = template['install'].strip().split('\n')
        for cmd in install_commands:
            print(cmd)
            stdin, stdout, stderr = client.exec_command(cmd)
            print(f"[{server} said:] {stdout.read().decode().strip()}")
            print(f"[{server} said:] {stderr.read().decode().strip()}")

    # criar um arquivo de targets no servidor (simplificado)
    if flag == 2:
        print(f"[!] Running template on: {server}")
        target_file_content = "\n".join(assigned_targets)
        client.exec_command(f"echo '{target_file_content}' > splinter_tools/targets.txt")

        # executar ferramenta
        stdin, stdout, stderr = client.exec_command(template['execute'])
        print(f"{stdout.read().decode().strip()}")
        print(f"[{server} said:] {stderr.read().decode().strip()}")

    client.close()

parser = argparse.ArgumentParser()
parser.add_argument('--install', action='store_true', help='Instala a ferramenta remotamente')
parser.add_argument('--execute', action='store_true', help='Executa um set de instrução')
args = parser.parse_args()
flag = 0
if args.install:
    flag = 1
elif args.execute:
    flag = 2

# iniciar threads para múltiplos servidores
threads = []
for i, server in enumerate(servers):
    t = threading.Thread(target=deploy_and_execute, args=(server, divided_targets[i], flag))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("Execução finalizada!")

import os
import subprocess
import re
import socket

def obter_diretorio_padrao():
    sistema_operacional = os.name

    if sistema_operacional == 'posix' and os.path.exists("/opt/e-SUS/database/postgresql-9.6.13-1-linux-x64/data/pg_hba.conf"):  # Linux
        return "/opt/e-SUS/database/postgresql-9.6.13-1-linux-x64/data/"
    elif sistema_operacional == 'nt' and os.path.exists("C:\\Program Files\\e-SUS\\database\\postgresql-9.6.13-4-windows-x64\\data\\pg_hba.conf"):  # Windows
        return "C:\\Program Files\\e-SUS\\database\\postgresql-9.6.13-4-windows-x64\\data\\"
    else:
        return None

def solicitar_diretorio_usuario():
    return input("Digite o caminho completo do diretório do pg_hba.conf: ")


def verifica_pg_hba_conf():
    diretorio_padrao = obter_diretorio_padrao()

    if diretorio_padrao is None or not os.path.exists(diretorio_padrao):
        print("Diretório padrão não encontrado.")
        diretorio_usuario = solicitar_diretorio_usuario()

        if not os.path.exists(diretorio_usuario):
            print("Diretório não encontrado. Certifique-se de inserir um caminho válido.")
            exit(1)
        else:
            diretorio_padrao = diretorio_usuario

    print(f"Verificando pg_hba.conf no diretório: {diretorio_padrao}")

    # Padrão para linhas no formato host all all x.x.x.x/xx md5
    padrao_host = re.compile(r'^\s*host\s+.*\s+.*\s+(\d+\.\d+\.\d+\.\d+/\d+)\s+md5$')

    # Padrão para linhas no formato host all all 0.0.0.0/0 trust
    padrao_host_trust = re.compile(r'^\s*host\s+.*\s+.*\s+0\.0\.0\.0/0\s+trust$')

    # Padrão para linhas no formato hostssl all all x.x.x.x/xx md5
    padrao_hostssl = re.compile(r'^\s*hostssl\s+.*\s+.*\s+(\d+\.\d+\.\d+\.\d+/\d+)\s+md5$')

    # Padrão para linhas no formato host all all all trust
    padrao_host_all_trust = re.compile(r'^\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+trust$')

    hosts_potencialmente_inseguros = False

    with open(os.path.join(diretorio_padrao, "pg_hba.conf"), 'r') as f:
        for num_linha, linha in enumerate(f, start=1):
            # Ignora linhas comentadas
            if linha.strip().startswith('#'):
                continue

            # Verifica se a linha corresponde ao padrão host
            match_host = padrao_host.match(linha)
            if match_host:
                # Extrai o endereço IP e a máscara da correspondência
                endereco_ip, _ = match_host.group(1).split('/')

                # Verifica se o IP está fora da rede interna
                if not any(padrao in endereco_ip for padrao in ['192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.','127.0.0.1']):
                    # Verifica se não está configurado como SSL
                    if not padrao_hostssl.match(linha):
                        print(f"Aviso: A linha {num_linha} '{linha.strip()}' permite acesso de fora da rede interna sem SSL ou modo trust.")
                        hosts_potencialmente_inseguros = True

            # Verifica se a linha corresponde ao padrão trust
            match_host_trust = padrao_host_trust.match(linha)
            if match_host_trust:
                print(f"Aviso: A linha {num_linha} '{linha.strip()}' está configurada com o modo 'trust'. Recomenda-se evitar o uso do modo 'trust' para segurança.")
                hosts_potencialmente_inseguros = True

            # Verifica se a linha corresponde ao padrão host all all all trust
            match_host_all_trust = padrao_host_all_trust.match(linha)
            if match_host_all_trust:
                print(f"Aviso: A linha {num_linha} '{linha.strip()}' está configurada com o modo 'trust' para qualquer host, usuário e banco. Recomenda-se evitar o uso do modo 'trust' para segurança.")
                hosts_potencialmente_inseguros = True

    # Verifica programas escutando em IPs externos
    print("\nVerificando programas escutando em IPs externos:")
    for porta in [5432, 5433]:
        try:
            # Tenta abrir uma conexão para verificar se a porta está escutando
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            resultado = sock.connect_ex(('0.0.0.0', porta))
            sock.close()

            # Se a porta está escutando, exibe um alerta
            if resultado == 0:
                print(f"Aviso: Programa escutando na porta {porta}.")
                hosts_potencialmente_inseguros = True
        except Exception as e:
            pass

    if not hosts_potencialmente_inseguros:
        print("Configuração do pg_hba.conf passou no teste. Não foram encontrados hosts com configurações potencialmente inseguras.")
# Executa a função de verificação
verifica_pg_hba_conf()

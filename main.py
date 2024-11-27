import os
import hashlib
import getpass
import string
import random
from multiprocessing import Process

ARQUIVO_USUARIOS = "usuarios.txt"
PROPRIETARIOS = "proprietarios.txt"

def processo_wrapper(funcao, *args):
    print(f"----[PID: {os.getpid()}]----")
    funcao(*args)


def executar_comando_no_processo(funcao, *args):
    processo = Process(target=processo_wrapper, args=(funcao, *args))
    processo.start()
    processo.join()

def gerar_salt():
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(10))


def gerar_hash_senha(senha, salt):
    return hashlib.sha512((salt + senha).encode()).hexdigest()


def verificar_usuario_existente(login):
    if not os.path.exists(ARQUIVO_USUARIOS):
        return False
    with open(ARQUIVO_USUARIOS, "r") as file:
        for linha in file:
            if linha.startswith(login + ":"):
                return True
    return False


def menu_inicial():
    while True:
        print("\nMiniSO - Sistema Operacional Simples")
        print("1. Fazer login")
        print("2. Cadastrar novo usuário")
        print("3. Sair")
        
        opcao = input("Escolha uma opção: ").strip()
        if opcao == "1":
            if not os.path.exists(ARQUIVO_USUARIOS):
                print("Nenhum usuário cadastrado. Use a opção de cadastro para criar o primeiro usuário.")
                login = input("Digite o login: ").strip()
                senha = getpass.getpass("Digite a senha: ").strip()
                executar_comando_no_processo(cadastrar_usuario, login, senha)
                
                usuario_logado = login_usuario(login, senha)
                if usuario_logado:
                    return usuario_logado
            else:
                login = input("Digite o login: ").strip()
                senha = getpass.getpass("Digite a senha: ").strip()
                usuario_logado = login_usuario(login, senha)
                if usuario_logado:
                    return usuario_logado  # Retorna o login do usuário autenticado
                else:
                    print("Login ou senha incorretos. Tente novamente.")
        elif opcao == "2":
            login = input("Digite o login: ").strip()
            senha = getpass.getpass("Digite a senha: ").strip()
            executar_comando_no_processo(cadastrar_usuario, login, senha)

            usuario_logado = login_usuario(login, senha)
            if usuario_logado:
                    return usuario_logado
        elif opcao == "3":
            print("Saindo do MiniSO...")
            exit()
        else:
            print("Opção inválida. Tente novamente.")


def cadastrar_usuario(login, senha):
    if verificar_usuario_existente(login):
        print("Usuário já cadastrado.")
        return None
    salt = gerar_salt()
    hash_senha = gerar_hash_senha(senha, salt)
    senha_armazenada = f"{login}:$6${salt}${hash_senha}"
    with open(ARQUIVO_USUARIOS, "a") as file:
        file.write(senha_armazenada + "\n")
    print("Usuário cadastrado com sucesso!")
    return login


def login_usuario(login, senha):
    if not os.path.exists(ARQUIVO_USUARIOS):
        print(f"[PID: {os.getpid()}] Nenhum usuário cadastrado.")
        return None
    with open(ARQUIVO_USUARIOS, "r") as file:
        for linha in file:
            partes = linha.strip().split(":")
            if partes[0] == login:
                salt, hash_armazenado = partes[1].split("$")[2:]
                if gerar_hash_senha(senha, salt) == hash_armazenado:
                    print(f"[PID: {os.getpid()}] Login bem-sucedido!")
                    return login  # Retorna o login do usuário autenticado
    print(f"[PID: {os.getpid()}] Login ou senha incorretos.")
    return None


def verificar_permissao(usuario, caminho):
    if not os.path.exists(PROPRIETARIOS):
        return False
    with open(PROPRIETARIOS, "r") as file:
        for linha in file:
            dono, recurso = linha.strip().split(":", 1)
            if recurso == caminho and dono == usuario:
                return True
    return False


def registrar_proprietario(usuario, caminho):
    with open(PROPRIETARIOS, "a") as file:
        file.write(f"{usuario}:{caminho}\n")


import os

def ls(diretorio=".", nivel=0):
    try:
        conteudo = os.listdir(diretorio)
        
        diretorios = []
        arquivos = []
        
        for item in conteudo:
            caminho_completo = os.path.join(diretorio, item)
            if os.path.isdir(caminho_completo):
                diretorios.append(item)
            else:
                arquivos.append(item)

        for item in sorted(diretorios):
            print("    " * nivel + item + "/")
            ls(os.path.join(diretorio, item), nivel + 1)

        for item in sorted(arquivos):
            print("    " * nivel + item)

    except FileNotFoundError:
        print(f"Erro: Diretório '{diretorio}' não encontrado.")
    except PermissionError:
        print(f"Erro: Sem permissão para acessar '{diretorio}'.")


def touch(usuario, caminho):
    try:
        with open(caminho, "w") as file:
            file.write("Conteúdo aleatório.\n")
        registrar_proprietario(usuario, caminho)
        print(f"Arquivo '{caminho}' criado com sucesso.")
    except Exception as e:
        print(f"Erro ao criar arquivo: {e}")

def rm(usuario, caminho):
    try:
        if os.path.isdir(caminho):
            print(f"Erro: '{caminho}' é um diretório. Use 'rm -r'.")
            return
        
        if not verificar_permissao(usuario, caminho):
            print(f"Erro: Você não tem permissão para remover o arquivo '{caminho}'.")
            return
        
        os.remove(caminho)
        if os.path.exists(PROPRIETARIOS):
            with open(PROPRIETARIOS, "r") as file:
                linhas = file.readlines()
            with open(PROPRIETARIOS, "w") as file:
                for linha in linhas:
                    if not linha.strip().startswith(f"{usuario}:{caminho}"):
                        file.write(linha)

        print(f"Arquivo '{caminho}' removido com sucesso.")

    except FileNotFoundError:
        print(f"Erro: Arquivo '{caminho}' não encontrado.")
    except PermissionError:
        print(f"Erro: Sem permissão para apagar '{caminho}'.")
    except Exception as e:
        print(f"Erro inesperado: {e}")

def mkdir(usuario, diretorio):
    try:
        os.makedirs(diretorio)
        registrar_proprietario(usuario, diretorio)
        print(f"Diretório '{diretorio}' criado com sucesso.")
    except FileExistsError:
        print(f"Erro: Diretório '{diretorio}' já existe.")
    except Exception as e:
        print(f"Erro ao criar diretório: {e}")

def rmdir(usuario, diretorio):
    try:
        if not os.path.isdir(diretorio):
            print(f"Erro: '{diretorio}' não é um diretório.")
            return

        if not verificar_permissao(usuario, diretorio):
            print(f"Erro: Você não tem permissão para remover o diretório '{diretorio}'")
            return
        
        os.rmdir(diretorio)

        if os.path.exists(PROPRIETARIOS):
            with open(PROPRIETARIOS, "r") as file:
                linhas = file.readlines()
            with open(PROPRIETARIOS, "w") as file:
                for linha in linhas:
                    if not linha.strip().startswith(f"{usuario}:{diretorio}"):
                        file.write(linha)

        print(f"Diretório '{diretorio}' removido com sucesso.")

    except FileNotFoundError:
        print(f"Erro: Diretório '{diretorio}' não encontrado.")
    except OSError:
        print(f"Erro: Diretório '{diretorio}' não está vazio ou há um problema ao removê-lo.")
    except Exception as e:
        print(f"Erro inesperado: {e}")

def rm_r(usuario, diretorio):
    try:
        import shutil

        if not os.path.isdir(diretorio):
            print(f"Erro: '{diretorio}' não é um diretório.")
            return
        
        if not verificar_permissao(usuario, diretorio):
            print(f"Erro: Você não tem permissão para remover o diretório '{diretorio}'.")
            return
        
        shutil.rmtree(diretorio)

        if os.path.exists(PROPRIETARIOS):
            with open(PROPRIETARIOS, "r") as file:
                linhas = file.readlines()
            with open(PROPRIETARIOS, "w") as file:
                for linha in linhas:
                    _, recurso = linha.strip().split(":", 1)
                    if not recurso.startswith(diretorio):
                        file.write(linha)
        print(f"Diretório '{diretorio}' removido com sucesso.")

    except FileNotFoundError:
        print(f"Erro: Diretório '{diretorio}' não encontrado.")
    except PermissionError:
        print(f"Erro: Sem permissão para apagar '{diretorio}'.")
    except Exception as e:
        print(f"Erro ao remover diretório: {e}")


def exibir_comandos():
    print("\nComandos disponíveis no MiniSO:")
    print("  - listar [diretório]                -> Lista o conteúdo do diretório (ou do atual, se não especificado)")
    print("     Exemplo: listar                 -> Lista o conteúdo do diretório atual")
    print("     Exemplo: listar /caminho/dir    -> Lista o conteúdo do diretório '/caminho/dir'")
    print()
    print("  - criar arquivo [arquivo]          -> Cria um arquivo no diretório especificado")
    print("     Exemplo: criar arquivo arquivo.txt  -> Cria o arquivo 'arquivo.txt' no diretório atual")
    print("     Exemplo: criar arquivo /dir/novo.txt -> Cria o arquivo 'novo.txt' no diretório '/dir'")
    print()
    print("  - apagar arquivo [arquivo]         -> Remove o arquivo especificado")
    print("     Exemplo: apagar arquivo arquivo.txt -> Remove o arquivo 'arquivo.txt' no diretório atual")
    print("     Exemplo: apagar arquivo /dir/velho.txt -> Remove o arquivo 'velho.txt' no diretório '/dir'")
    print()
    print("  - criar diretorio [diretório]      -> Cria um diretório no caminho especificado")
    print("     Exemplo: criar diretorio novo_dir -> Cria o diretório 'novo_dir' no diretório atual")
    print("     Exemplo: criar diretorio /dir/subdir -> Cria o diretório 'subdir' dentro de '/dir'")
    print()
    print("  - apagar diretorio [diretório]     -> Remove um diretório vazio")
    print("     Exemplo: apagar diretorio vazio -> Remove o diretório 'vazio' no diretório atual")
    print("     Exemplo: apagar diretorio /dir/vazio -> Remove o diretório 'vazio' em '/dir'")
    print()
    print("  - apagar diretorio [diretório] --force  -> Remove um diretório e seu conteúdo recursivamente")
    print("     Exemplo: apagar diretorio -r cheio -> Remove o diretório 'cheio' e todo seu conteúdo")
    print("     Exemplo: apagar diretorio -r /dir/cheio -> Remove o diretório 'cheio' em '/dir' e todo seu conteúdo")
    print()
    print("  - exit                             -> Sai do MiniSO")
    print("     Exemplo: exit                   -> Encerra o sistema")



def shell(usuario):
    while True:
        comando = input(f"{usuario}@miniso:~$ ").strip()
        
        if comando.startswith("listar"):
            args = comando.split(" ", 1)
            diretorio = args[1] if len(args) > 1 else "."
            executar_comando_no_processo(ls, diretorio)
        
        elif comando.startswith("criar arquivo"):
            args = comando.split(" ", 2)
            if len(args) > 2:
                executar_comando_no_processo(touch, usuario, args[2])
            else:
                print("Uso: criar arquivo <arquivo>")
        
        elif comando.startswith("apagar diretorio"):
            args = comando.split(" ")
            if "--force" in args:
                index = args.index("--force")
                caminho = " ".join(args[2:index]).strip()
                if caminho:
                    executar_comando_no_processo(rm_r, usuario, caminho)
                else:
                    print("Uso: apagar diretorio [diretório] --force")
            elif len(args) > 2:
                executar_comando_no_processo(rmdir, usuario, args[2])
            else:
                print("Uso: apagar diretorio <diretório> ou apagar diretorio [diretório] --force")
        
        elif comando.startswith("apagar diretorio"):
            args = comando.split(" ", 2)
            if len(args) > 2:
                executar_comando_no_processo(rmdir, usuario, args[2])
            else:
                print("Uso: apagar diretorio <diretório>")
        
        elif comando.startswith("apagar arquivo"):
            args = comando.split(" ", 2)
            if len(args) > 2:
                executar_comando_no_processo(rm, usuario, args[2])
            else:
                print("Uso: apagar arquivo <arquivo>")
        
        elif comando.startswith("criar diretorio"):
            args = comando.split(" ", 2)
            if len(args) > 2:
                executar_comando_no_processo(mkdir, usuario, args[2])
            else:
                print("Uso: criar diretorio <diretório>")
        
        elif comando == "exit":
            print("Saindo do MiniSO...")
            break
        
        else:
            print(f"Comando não reconhecido: {comando}")


if __name__ == "__main__":
    usuario_logado = menu_inicial()
    if usuario_logado:
        exibir_comandos()
        shell(usuario_logado)

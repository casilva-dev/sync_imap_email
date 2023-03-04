![Sync Email Image](https://cdn-icons-png.flaticon.com/128/9197/9197904.png)
# SyncImapEmail

[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)

Este projeto é um script em Python3 que automatiza o processo de migração de mensagens de e-mail. Ele copia todas as mensagens de um determinado e-mail e as cola em outro, facilitando significativamente a tarefa de transferir uma ou mais contas de e-mail de um servidor/hospedagem para outro. Com este script, a migração é realizada de forma rápida, simples e eficiente.

## Como usar

Baixe o SyncImapEmail no repositório Git:

```bash
git clone https://gitlab.com/cesarasilva/sync_imap_email.git
```

Entre na pasta do projeto, copie o arquivo "credentials.json.default" para um novo arquivo chamado "credentials.json".

```bash
cd sync_imap_email/
cp credentials.json.default credencials.json
```

Edite o arquivo "credencials.json" e adicione as credenciais dos e-mails:

```json
[
    {
        "src": {
            "email": "email@domain1.com",
            "password": "password",
            "server": "imap.domain1.com",
            "port": 143,
            "security": "TLS"
        },
        "dst": {
            "email": "email@domain2.com",
            "password": "password",
            "server": "mail.domain2.com",
            "port": 993,
            "security": "SSL"
        }
    },
    ...
]
```

O script pode ser utilizado de duas formas diferentes:

1. **Docker**

    Inicie o Docker, caso não esteja rodando, e execute o seguinte comando:

    ```bash
    docker build -t sync_imap_email .
    docker run -it --name my_container sync_imap_email
    ```

    O Docker irá iniciar o container para executar o script. Após a conclusão da migração, o nome do arquivo de log será exibido. Copie o arquivo de log do container para o seu computador local.

    ```bash
    docker cp my_container:/log_20230202_030302.txt .
    ```

2. **Manual**

    Para rodar o script manualmente no terminal do seu computador, é necessário instalar o Python3.8 e suas dependências.

    - ***Linux:***

    ```bash
    sudo apt-get update
    sudo apt-get install python3.8
    sudo apt-get install python3-pip
    pip3 install chardet google-auth google-auth-oauthlib==0.8.0
    ```

    - ***MacOS:***

    ```zsh
    brew install python3
    pip3 install chardet google-auth google-auth-oauthlib==0.8.0
    ```

    Após a instalação dos pacotes necessários, execute o script:

    ```bash
    python3 sync_imap_email.py
    ```

## Contribuição

Nós encorajamos a contribuição de todos! Aqui estão as instruções para começar:

1. Faça um fork do projeto.
2. Crie sua branch para a nova funcionalidade (`git checkout -b nova-funcionalidade`).
3. Commit suas mudanças (`git commit -am 'Adicionando nova funcionalidade'`).
4. Empurre a branch (`git push origin nova-funcionalidade`).
5. Crie um novo Pull Request para o projeto principal.

Por favor, verifique antes de enviar seu pull request que o código segue as diretrizes de codificação do projeto, incluindo os padrões de formatação e testes automatizados.

## Licença

Este projeto está licenciado sob a licença [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).
# SyncImapEmail

Este projeto é um script em Python3 que automatiza o processo de migração de mensagens de e-mail. Ele copia todas as mensagens de um determinado e-mail e as cola em outro, facilitando significativamente a tarefa de transferir uma ou mais contas de e-mail de um servidor/hospedagem para outro. Com este script, a migração é realizada de forma rápida, simples e eficiente.

## Instalação

**Passo 1:** Baixar o script no repositório git

Você pode baixar o script executando o seguinte comando no terminal:

```bash
git clone https://gitlab.com/cesarasilva/sync_imap_email.git
```

**Passo 2:** Instalar e atualizar as dependências

Antes de executar o script, é necessário instalar e atualizar as dependências, incluindo o Python e o pacote "chardet". Você pode fazer isso executando o seguinte comando no terminal:

```bash
pip3 install --upgrade python chardet
```

Depois de seguir esses passos, o script deve ser executado sem problemas e realizar a migração de mensagens de e-mail como desejado.

## Como usar

Siga os seguintes passos para utilizar este script:

**Passo 1:** Configurar as credenciais

Você precisa configurar as credenciais dos e-mails. Para fazer isso, copie o arquivo "credentials.json.default" para um novo arquivo chamado "credentials.json" e adicione as credenciais dos e-mails.

**Passo 2:** Executar o script

Finalmente, você pode executar o script "sync_imap_email.py" usando o seguinte comando no terminal:

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

## Créditos

Gostaria de agradecer à [OpenAI](https://openai.com) pela utilização de seu modelo [ChatGPT](https://chat.openai.com), que me ajudou imensamente durante o desenvolvimento deste projeto.
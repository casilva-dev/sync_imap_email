#!/usr/bin/python3
#
# Copyright (C) 2023 Cesar Augustus Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
The objective of this script is to copy all the messages from one email
to another, facilitating the migration of emails from one server/hosting
to another in a simple way.
"""

import chardet, datetime, email, imaplib, json, os, pprint, re, sys, time

from email.utils import parsedate_to_datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

class SyncImapEmail:

    def __init__(self):
        self.__log_start()
        credentials = self.__load_credentials()
        self.__generate_tokens(credentials)
        for credential in credentials:
            self.__log_print(f"\nIniciando a migração do e-mail <{credential['src']['email']}>...")
            conn_result, src_mail, dst_mail = self.__connect(credential)
            if conn_result == "OK":
                self.__migrate(src_mail, dst_mail)
            self.__log_print(f"\nFinalizado a migração do e-mail <{credential['src']['email']}>.")
            self.__disconnect(src_mail, dst_mail)
        self.__log_print("\nMigração do(s) e-mail(s) finalizado.")
        self.__log_print("\nConfere no arquivo de log, se não houve nenhum erro durante o processo de migração.")
        self.__log_print("Nome do arquivo: {}".format(self.__log_filename))

    # Load JSON credentials file
    def __load_credentials(self):
        try:
            with open("credentials.json", "r") as file:
                credentials = json.load(file)
        except FileNotFoundError:
            self.__log_print("\nO arquivo credentials.json não foi encontrado.")
            self.__log_print("Copie o credentials.json.default, renomeie para credentials.json e define as credenciais.")
            sys.exit()
        return credentials

    # Create log file name with current date
    def __log_start(self):
        now = datetime.datetime.now()
        self.__log_filename = f"log_{now.strftime('%Y%m%d_%H%M%S')}.txt"

    # Print the values in sys.stdout and append to the log file
    def __log_print(self, message, type = print):
        type(message)
        if type == pprint.pprint:
            message = repr(message)
        with open(self.__log_filename, "a") as f:
            f.write(f"{message}\r\n")

    # Check credentials that have OAUTH2 authentication and generate the tokens.
    def __generate_tokens(self, credentials):
        # If modifying these scopes, delete the files token_<email>.json.
        self.__scopes = ['https://mail.google.com/']
        list = []
        for credential in credentials:
            list.append(credential["src"])
            list.append(credential["dst"])
        for data in list:
            if data["security"] != "OAUTH2":
                continue
            if not os.path.exists(f"oauth_client_secret.json"):
                self.__log_print("\nO arquivo oauth_client_secret.json não foi encontrado.")
                self.__log_print("Para dar continuidade, será necessário o arquivo de credenciais do Google Cloud.")
                self.__log_print("https://cloud.google.com/docs/authentication/client-libraries?hl=pt-br")
                sys.exit()
            creds = None
            email = re.sub(r'[^\w._-]+', '_', data["email"])
            if os.path.exists(f"token_{email}.json"):
                creds = Credentials.from_authorized_user_file(f"token_{email}.json", self.__scopes)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    self.__log_print(f"\nCriando o token OAUTH2 do e-mail: <{data['email']}>\n")
                    flow = InstalledAppFlow.from_client_secrets_file('oauth_client_secret.json', self.__scopes)
                    prompt_msg = "Visite a URL para autorizar este aplicativo: \n{url}"
                    code_msg = "Digite o código de autorização: "
                    creds = flow.run_console(authorization_prompt_message=prompt_msg, authorization_code_message=code_msg)
                # Save the credentials for the next run
                with open(f"token_{email}.json", 'w') as token:
                    token.write(creds.to_json())

    # Instantiate the IMAP connection class according to the security type
    def __imap_security(self, type, host, port):
        if type == "SSL" or type == "OAUTH2":
            rtn = imaplib.IMAP4_SSL(host, port)
        else:
            rtn = imaplib.IMAP4(host, port)
            if type == "STARTTLS":
                rtn.starttls()
        return rtn

    # Connects and authenticates source and destination IMAP servers
    def __connect(self, credential):
        # Connect to source IMAP server
        try:
            self.__log_print("Conectando no servidor de origem...")
            src_mail = self.__imap_security(credential["src"]["security"], credential["src"]["server"], credential["src"]["port"])
        except ConnectionRefusedError as e:
            self.__log_print("\nErro na conexão no servidor de origem.\nVerifique se a configuração do e-mail está correta:")
            self.__log_print(credential["src"], pprint.pprint)
            self.__log_print("\nExcept error: \"{}\"".format(e))
            return "ERROR", None, None

        # Authenticate a connection to the source IMAP server
        if credential["src"]["security"] == "OAUTH2":
            oauth2 = True
            email = re.sub(r'[^\w._-]+', '_', credential["src"]["email"])
            creds = Credentials.from_authorized_user_file(f"token_{email}.json", self.__scopes)
            auth_string = f"user={credential['src']['email']}\1auth=Bearer {creds.token}\1\1"
            self.__log_print("Autenticando com o token OAUTH2 no servidor de origem...")
        else:
            oauth2 = False
            self.__log_print("Autenticando com e-mail e senha no servidor de origem...")
        try:
            if oauth2:
                src_mail.authenticate('XOAUTH2', lambda x: auth_string)
            else:
                src_mail.login(credential["src"]["email"], credential["src"]["password"])
        except imaplib.IMAP4.error as e:
            self.__log_print("\nErro na autenticação no servidor de origem.")
            if oauth2:
                os.remove(f"token_{email}.json")
            else:
                self.__log_print("Verifique se o e-mail e senha estão corretas.")
            self.__log_print("\nExcept error: \"{}\"".format(e))
            return "ERROR", src_mail, None

        # Connect to destination IMAP server
        try:
            self.__log_print("Conectando no servidor de destino...")
            dst_mail = self.__imap_security(credential["dst"]["security"], credential["dst"]["server"], credential["dst"]["port"])
        except ConnectionRefusedError as e:
            self.__log_print("\nErro na conexão no servidor de destino.\nVerifique se a configuração do e-mail está correta:")
            self.__log_print(credential["dst"], pprint.pprint)
            self.__log_print("\nExcept error: \"{}\"".format(e))
            return "ERROR", src_mail, None

        # Authenticate a connection to the destination IMAP server
        if credential["dst"]["security"] == "OAUTH2":
            oauth2 = True
            email = re.sub(r'[^\w._-]+', '_', credential["dst"]["email"])
            creds = Credentials.from_authorized_user_file(f"token_{email}.json", self.__scopes)
            auth_string = f"user={credential['dst']['email']}\1auth=Bearer {creds.token}\1\1"
            self.__log_print("Autenticando com o token OAUTH2 no servidor de destino...")
        else:
            oauth2 = False
            self.__log_print("Autenticando com e-mail e senha no servidor de destino...")
        try:
            if oauth2:
                dst_mail.authenticate('XOAUTH2', lambda x: auth_string)
            else:
                dst_mail.login(credential["dst"]["email"], credential["dst"]["password"])
        except imaplib.IMAP4.error as e:
            self.__log_print("\nErro na autenticação no servidor de destino.")
            if oauth2:
                os.remove(f"token_{email}.json")
            else:
                self.__log_print("Verifique se o e-mail e senha estão corretas.")
            self.__log_print("\nExcept error: \"{}\"".format(e))
            return "ERROR", src_mail, dst_mail

        return "OK", src_mail, dst_mail

    # Closing the session and logging out
    def __disconnect(self, src_mail, dst_mail):
        if src_mail:
            if src_mail.state == 'SELECTED':
                src_mail.close()
            src_mail.logout()
        if dst_mail:
            if dst_mail.state == 'SELECTED':
                dst_mail.close()
            dst_mail.logout()

    # Migrate all folders along with messages from source email to destination
    def __migrate(self, src_mail, dst_mail):
        # Get all source mailboxes
        try:
            self.__log_print("Obtendo a lista de pastas no servidor de origem...")
            src_mailboxes = src_mail.list()
        except imaplib.IMAP4.error as e:
            self.__log_print("\nErro ao tentar obter a lista de pastas no servidor de origem.")
            self.__log_print("\nExcept error: \"{}\"".format(e))
            return

        # Get all destination mailboxes
        try:
            self.__log_print("Obtendo a lista de pastas no servidor de destino...")
            dst_mailboxes = dst_mail.list()
            dst_mailboxes = [dst_mailbox.decode() for dst_mailbox in dst_mailboxes[1]]
        except imaplib.IMAP4.error as e:
            self.__log_print("\nErro ao tentar obter a lista de pastas no servidor de destino.")
            self.__log_print("\nExcept error: \"{}\"".format(e))
            return

        mailboxes_defaults = ["Sent", "Drafts", "Junk", "Trash", "Archive"]

        # Loop through all source mailboxes
        for src_mailbox in src_mailboxes[1]:
            src_mailbox = src_mailbox.decode()

            # Mailboxes that are not copied
            if re.search(r"\\[Noselect|All|Flagged]", src_mailbox):
                continue

            mailbox_default = re.search(r"\\({})".format("|".join(mailboxes_defaults)), src_mailbox)
            if mailbox_default:
                mailbox_default = mailbox_default.group(1)

            src_separator = re.search('"(/|.)"', src_mailbox).group(1)
            src_mailbox = src_mailbox.split(f'"{src_separator}"')[-1].strip()
            try:
                self.__log_print(f"Selecionando a pasta {src_mailbox} do servidor de origem...")
                src_mail.select(src_mailbox)
            except imaplib.IMAP4.error as e:
                self.__log_print(f"\nErro ao tentar selecionar a pasta {src_mailbox} no servidor de origem.")
                self.__log_print("\nExcept error: \"{}\"".format(e))
                continue

            # Get all messages in the source mailbox
            src_result, src_data = src_mail.search(None, "ALL")
            if src_data[0]:
                src_msgs = src_data[0].split(b' ')

                dst_separator = re.search('"(/|.)"', dst_mailboxes[0]).group(1)
                if mailbox_default:
                    for mailbox in dst_mailboxes:
                        if mailbox.find(f"\\{mailbox_default}") != -1:
                            dst_mailbox = mailbox.split(f'"{dst_separator}"')[-1].strip()
                else:
                    dst_mailbox = src_mailbox
                    if src_separator != dst_separator:
                        dst_mailbox = dst_mailbox.replace(src_separator, dst_separator)

                if dst_separator == "/":
                    dst_mailbox = dst_mailbox.replace("INBOX/", "")
                if dst_mailbox.find("[Gmail]") != -1 and dst_mail.host.find("gmail.com") == -1:
                    dst_mailbox = dst_mailbox.replace("[Gmail]/", "")

                # Create the same mailbox on the destination server
                try:
                    dst_result, dst_data = dst_mail.select(dst_mailbox)
                    if dst_result == "NO" and dst_data[0].decode().find("prefixed with: INBOX.") != -1:
                        dst_mailbox = '"INBOX.{}"'.format(dst_mailbox.strip('"').replace("/", "."))
                        dst_result, dst_data = dst_mail.select(dst_mailbox)
                    if dst_result != "OK":
                        self.__log_print(f"Criando a pasta {dst_mailbox} no servidor de destino...")
                        dst_mail.create(dst_mailbox)
                        dst_mail.select(dst_mailbox)
                except imaplib.IMAP4.error as e:
                    self.__log_print(f"\nErro ao tentar criar a pasta {dst_mailbox} no servidor de destino.")
                    self.__log_print("\nExcept error: \"{}\"".format(e))
                    continue

                # Loop through all messages in the source mailbox
                for src_msg in src_msgs:
                    # Fetch the message header
                    try:
                        src_result, src_data = src_mail.fetch(src_msg, "(BODY.PEEK[HEADER])")
                    except imaplib.IMAP4.error as e:
                        self.__log_print(f"Erro ao tentar obter o cabeçalho da mensagem no servidor de origem.")
                        self.__log_print("\nExcept error: \"{}\"".format(e))
                        continue

                    # Extract the Message-ID from the header
                    encoding = chardet.detect(src_data[0][1])['encoding']
                    header = src_data[0][1].decode(encoding)
                    pattern = r"message-id:[\r\n\s]*\<?([a-z0-9_.%=+-]+@[a-z0-9_.%=+-]+)\>?"
                    message_id = re.search(pattern, header.lower(), re.IGNORECASE)

                    if message_id:
                        message_id = message_id.group(1)
                        self.__log_print(f"\nMessage-ID: <{message_id}>")

                        # Use the Message-ID to check if the message already exists in the destination mailbox
                        dst_result, dst_data = dst_mail.search(None, "HEADER Message-ID <{}>".format(message_id))
                        if not dst_data[0]:
                            # Fetch the source message
                            src_result, src_data = src_mail.fetch(src_msg, "BODY.PEEK[]")
                            if src_result == "OK":
                                # Get the date the original message was received
                                msg = email.message_from_bytes(src_data[0][1])
                                received_datetime = parsedate_to_datetime(msg["Date"])
                                received_timestamp = time.mktime(received_datetime.timetuple())
                                received_date = imaplib.Time2Internaldate(received_timestamp)

                                # Append the source message to the destination mailbox
                                try:
                                    self.__log_print(f"Copiando mensagem da pasta {src_mailbox} no servidor de origem para a pasta {dst_mailbox} no servidor de destino...")
                                    dst_result, dst_data = dst_mail.append(dst_mailbox, None, received_date, src_data[0][1])
                                    if dst_result != "OK":
                                        self.__log_print(f"Erro ao tentar adicionar a mensagem para a pasta {dst_mailbox} no servidor de destino.")
                                        self.__log_print(f"dst_result: {dst_result}\ndst_data: {dst_data}")
                                except imaplib.IMAP4.error as e:
                                    self.__log_print(f"Erro ao tentar adicionar a mensagem para a pasta {dst_mailbox} no servidor de destino.")
                                    self.__log_print("\nExcept error: \"{}\"".format(e))
                                    continue

                                # Preserved original message flags when copying to target email
                                flags = src_mail.fetch(src_msg, "(FLAGS)")[1][0]
                                flags = re.findall(r'\\\w+', flags.decode())
                                if flags:
                                    if "\\Recent" in flags:
                                        flags.remove("\\Recent")
                                    flags = ' '.join(flags)
                                    dst_data = dst_mail.search(None, 'HEADER Message-ID "{}"'.format(message_id))[1]
                                    dst_mail.store(dst_data[0].split()[-1], "+FLAGS", flags)
                            else:
                                self.__log_print(f"Erro ao tentar buscar a mensagem na pasta {src_mailbox} no servidor de origem.")
                                self.__log_print(f"src_result: {src_result}\nsrc_data: {src_data}")
                        else:
                            self.__log_print(f"Mensagem já existe na pasta {dst_mailbox} no servidor de destino.")
                    else:
                        self.__log_print("Message-ID não encontrado no cabeçalho.")
                        self.__log_print(f"header: {header}")
            else:
                self.__log_print(f"A pasta {src_mailbox} está vazia no servidor de origem.")

if __name__ == '__main__':
    SyncImapEmail()
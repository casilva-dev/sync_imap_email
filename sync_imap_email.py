# sync_imap_email.py
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
#
# The objective of this script is to copy all the messages from one email
# to another, facilitating the migration of emails from one server/hosting
# to another in a simple way.

#!/usr/bin/env python3
from email.utils import parsedate_to_datetime
import sys, re, json, chardet, imaplib, pprint, time, datetime, email

class SyncImapEmail:

    def __init__(self):
        json_credentials = self.__load_credentials()
        self.__log_start()
        for credential in json_credentials:
            self.__migrate(credential)
            self.__disconnect()
        self.__log_print("\nMigração do(s) e-mail(s) finalizado.")
        self.__log_print("\nConfere no arquivo de log, se não houve nenhum erro durante o processo de migração.")
        self.__log_print("Nome do arquivo: {}".format(self.__log_filename))

    # Load JSON credentials file
    def __load_credentials(self):
        try:
            with open("credentials.json", "r") as file:
                json_credentials = json.load(file)
        except FileNotFoundError:
            self.__log_print("\nO arquivo credentials.json não foi encontrado.")
            self.__log_print("Copie o credentials.json.default, renomeie para credentials.json e define as credenciais.")
            sys.exit()
        return json_credentials

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

    # Instantiate the IMAP connection class according to the security type
    def __imap_security(self, type, host, port):
        if type == "SSL":
            rtn = imaplib.IMAP4_SSL(host, port)
        else:
            rtn = imaplib.IMAP4(host, port)
            if type == "STARTTLS":
                rtn.starttls()
        return rtn

    # Connects and authenticates source and destination IMAP servers
    def __connect(self, cfg):
        # Connect to source IMAP server
        try:
            self.__log_print("Conectando no servidor de origem...")
            self.__src_mail = self.__imap_security(cfg["src"]["security"], cfg["src"]["server"], cfg["src"]["port"])
        except ConnectionRefusedError as e:
            self.__log_print("\nErro na conexão no servidor de origem.\nVerifique se a configuração do e-mail está correta:")
            self.__log_print(cfg["src"], pprint.pprint)
            self.__log_print("\nExcept error: \"{}\"".format(e))
            return False

        # Authenticate a connection to the source IMAP server
        try:
            self.__log_print("Autenticando a conexão no servidor de origem...")
            self.__src_mail.login(cfg["src"]["user"], cfg["src"]["password"])
        except imaplib.IMAP4.error as e:
            self.__log_print("\nErro na autenticação no servidor de origem.\nVerifique se o usuário/e-mail e senha estão corretas.")
            self.__log_print("\nExcept error: \"{}\"".format(e))
            return False

        # Connect to destination IMAP server
        try:
            self.__log_print("Conectando no servidor de destino...")
            self.__dst_mail = self.__imap_security(cfg["dst"]["security"], cfg["dst"]["server"], cfg["dst"]["port"])
        except ConnectionRefusedError as e:
            self.__log_print("\nErro na conexão no servidor de destino.\nVerifique se a configuração do e-mail está correta:")
            self.__log_print(cfg["dst"], pprint.pprint)
            self.__log_print("\nExcept error: \"{}\"".format(e))
            return False

        # Authenticate a connection to the destination IMAP server
        try:
            self.__log_print("Autenticando no servidor de destino...")
            self.__dst_mail.login(cfg["dst"]["user"], cfg["dst"]["password"])
        except imaplib.IMAP4.error as e:
            self.__log_print("\nErro na autenticação no servidor de destino.\nVerifique se o usuário/e-mail e senha estão corretas.")
            self.__log_print("\nExcept error: \"{}\"".format(e))
            return False

        return True

    # Closing the session and logging out
    def __disconnect(self):
        if hasattr(self, '_SyncImapEmail__src_mail'):
            if self.__src_mail.state == 'SELECTED':
                self.__src_mail.close()
            self.__src_mail.logout()
        if hasattr(self, '_SyncImapEmail__dst_mail'):
            if self.__dst_mail.state == 'SELECTED':
                self.__dst_mail.close()
            self.__dst_mail.logout()

    # Migrate all folders along with messages from source email to destination
    def __migrate(self, json):
        self.__log_print(f"\nIniciando a migração do e-mail <{json['src']['user']}>...")
        if (not self.__connect(json)):
            return

        # Get all source mailboxes
        try:
            self.__log_print("Obtendo a lista de pastas do servidor de origem...")
            src_mailboxes = self.__src_mail.list()
        except imaplib.IMAP4.error as e:
            self.__log_print("\nErro ao tentar obter a lista de pastas no servidor de origem.")
            self.__log_print("\nExcept error: \"{}\"".format(e))
            return

        if src_mailboxes[0] == "OK":

            # Loop through all source mailboxes
            for mailbox in src_mailboxes[1]:
                # Get the mailbox name and select it
                try:
                    self.__log_print("Obtendo o nome da pasta do servidor de origem...")
                    mailbox_name = mailbox.split(b'"."')[-1].strip(b'"')
                    mailbox_name2 = mailbox_name.decode().strip()
                except TypeError as e:
                    self.__log_print("\nErro ao tentar obter o nome da pasta no servidor de origem.")
                    self.__log_print("\nExcept error: \"{}\"".format(e))
                    continue

                try:
                    self.__log_print(f"Selecionando a pasta {mailbox_name2} do servidor de origem...")
                    self.__src_mail.select(mailbox_name)
                except imaplib.IMAP4.error as e:
                    self.__log_print(f"\nErro ao tentar selecionar a pasta {mailbox_name2} no servidor de origem.")
                    self.__log_print("\nExcept error: \"{}\"".format(e))
                    continue

                # Get all messages in the source mailbox
                src_result, src_data = self.__src_mail.search(None, "ALL")
                if src_data[0]:
                    src_msgs = src_data[0].split(b' ')

                    # Create the same mailbox on the destination server
                    try:
                        self.__log_print(f"Criando a pasta {mailbox_name2} no servidor de destino, caso não exista...")
                        self.__dst_mail.create(mailbox_name)
                        self.__dst_mail.select(mailbox_name)
                    except imaplib.IMAP4.error as e:
                        self.__log_print(f"\nErro ao tentar criar/selecionar a pasta {mailbox_name2} no servidor de destino.")
                        self.__log_print("\nExcept error: \"{}\"".format(e))
                        continue

                    # Loop through all messages in the source mailbox
                    for src_msg in src_msgs:
                        # Fetch the message header
                        try:
                            src_result, src_data = self.__src_mail.fetch(src_msg, "(BODY[HEADER])")
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
                            dst_result, dst_data = self.__dst_mail.search(None, "HEADER Message-ID <{}>".format(message_id))
                            if not dst_data[0]:
                                # Fetch the source message
                                src_result, src_data = self.__src_mail.fetch(src_msg, "(RFC822)")
                                if src_result == "OK":
                                    # Get the date the original message was received
                                    msg = email.message_from_bytes(src_data[0][1])
                                    received_datetime = parsedate_to_datetime(msg["Date"])
                                    received_timestamp = time.mktime(received_datetime.timetuple())
                                    received_date = imaplib.Time2Internaldate(received_timestamp)

                                    # Append the source message to the destination mailbox
                                    try:
                                        self.__log_print(f"Copiando mensagem de {mailbox_name2} para o servidor de destino...")
                                        dst_result, dst_data = self.__dst_mail.append(mailbox_name, None, received_date, src_data[0][1])
                                        if dst_result != "OK":
                                            self.__log_print(f"Erro ao tentar copiar a mensagem de {mailbox_name2} para o servidor de destino.")
                                            self.__log_print(f"dst_result: {dst_result}\ndst_data: {dst_data}")
                                    except imaplib.IMAP4.error as e:
                                        self.__log_print(f"Erro ao tentar copiar a mensagem de {mailbox_name2} para o servidor de destino.")
                                        self.__log_print("\nExcept error: \"{}\"".format(e))
                                else:
                                    self.__log_print(f"Erro ao tentar buscar a mensagem de {mailbox_name2} do servidor de origem.")
                                    self.__log_print(f"src_result: {src_result}\nsrc_data: {src_data}")
                            else:
                                self.__log_print(f"Mensagem já existe em {mailbox_name2} no servidor de destino.")
                        else:
                            self.__log_print("Message-ID não encontrado no cabeçalho.")
                            self.__log_print(f"header: {header}")
                else:
                    self.__log_print(f"A pasta {mailbox_name2} está vazia no servidor de origem.")
            self.__log_print(f"\nFinalizado a migração do e-mail <{json['src']['user']}>.")
        else:
            self.__log_print("\nErro ao tentar obter a lista de pastas no servidor de origem.")
            self.__log_print("\nExcept error: \"{}\"".format(src_mailboxes))

SyncImapEmail()
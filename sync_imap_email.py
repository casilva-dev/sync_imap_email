#!/usr/bin/env python3
from email.utils import parsedate_to_datetime
import sys, re, json, chardet, imaplib, pprint, time, datetime, email

# Creating log file name with current date
now = datetime.datetime.now()
log_filename = f"log_{now.strftime('%Y%m%d_%H%M%S')}.txt"

def log_print(message, type = print):
    type(message)
    if type == pprint.pprint:
        message = repr(message)
    with open(log_filename, "a") as f:
        f.write(f"{message}\r\n")

def imap_security(type, host, port):
    if type == "SSL":
        rtn = imaplib.IMAP4_SSL(host, port)
    else:
        rtn = imaplib.IMAP4(host, port)
        if type == "STARTTLS":
            rtn.starttls()
    return rtn

def migrate_emails(json):
    # Connect to source IMAP server
    try:
        log_print("Conectando no servidor de origem...")
        src_mail = imap_security(json["src"]["security"], json["src"]["server"], json["src"]["port"])
    except ConnectionRefusedError as e:
        log_print("\nErro na conexão no servidor de origem.\nVerifique se a configuração do e-mail está correta:")
        log_print(json["src"], pprint.pprint)
        log_print(f"\nError Message: \"{e}\"")
        return

    # Authenticate a connection to the destination IMAP server
    try:
        log_print("Autenticando a conexão no servidor de origem...")
        src_mail.login(json["src"]["user"], json["src"]["password"])
    except imaplib.IMAP4.error as e:
        log_print("\nErro na autenticação no servidor de origem.\nVerifique se o usuário/e-mail e senha estão corretas.")
        log_print(f"\nError Message: \"{e}\"\n")
        return

    # Connect to source IMAP server
    try:
        log_print("Conectando no servidor de destino...")
        dst_mail = imap_security(json["dst"]["security"], json["dst"]["server"], json["dst"]["port"])
    except ConnectionRefusedError as e:
        log_print("\nErro na conexão no servidor de destino.\nVerifique se a configuração do e-mail está correta:")
        log_print(json["dst"], pprint.pprint)
        log_print(f"Error Message: \"{e}\"")
        return

    # Authenticate a connection to the destination IMAP server
    try:
        log_print("Autenticando no servidor de destino...")
        dst_mail.login(json["dst"]["user"], json["dst"]["password"])
    except imaplib.IMAP4.error as e:
        log_print("\nErro na autenticação no servidor de destino.\nVerifique se o usuário/e-mail e senha estão corretas.")
        log_print(f"\nError Message: \"{e}\"\n")
        src_mail.logout()
        return

    # Get all source mailboxes
    try:
        log_print("Obtendo a lista de pastas do servidor de origem...")
        src_mailboxes = src_mail.list()
    except imaplib.IMAP4.error as e:
        log_print("\nErro ao tentar obter a lista de pastas no servidor de origem.")
        log_print(f"\nError Message: \"{e}\"\n")
        src_mail.logout()
        dst_mail.logout()
        return

    if src_mailboxes[0] == "OK":

        # Loop through all source mailboxes
        for mailbox in src_mailboxes[1]:
            # Get the mailbox name and select it
            try:
                log_print("Obtendo o nome da pasta do servidor de origem...")
                mailbox_name = mailbox.split(b'"."')[-1].strip(b'"')
                mailbox_name2 = mailbox_name.decode().strip()
            except TypeError as e:
                log_print("\nErro ao tentar obter o nome da pasta no servidor de origem.")
                log_print(f"\nError Message: \"{e}\"\n")
                src_mail.logout()
                dst_mail.logout()
                return

            try:
                log_print(f"Selecionando a pasta {mailbox_name2} do servidor de origem...")
                src_mail.select(mailbox_name)
            except imaplib.IMAP4.error as e:
                log_print(f"\nErro ao tentar selecionar a pasta {mailbox_name2} no servidor de origem.")
                log_print(f"\nError Message: \"{e}\"\n")
                src_mail.logout()
                dst_mail.logout()
                return

            # Get all messages in the source mailbox
            src_result, src_data = src_mail.search(None, "ALL")
            if src_data[0]:
                src_msgs = src_data[0].split(b' ')

                # Create the same mailbox on the destination server
                try:
                    log_print(f"Criando a pasta {mailbox_name2} no servidor de destino, caso não exista...")
                    dst_mail.create(mailbox_name)
                    dst_mail.select(mailbox_name)
                except imaplib.IMAP4.error as e:
                    log_print(f"\nErro ao tentar criar/selecionar a pasta {mailbox_name2} no servidor de destino.")
                    log_print(f"\nError Message: \"{e}\"\n")
                    src_mail.logout()
                    dst_mail.logout()
                    return

                # Loop through all messages in the source mailbox
                for src_msg in src_msgs:
                    # Fetch the message header
                    try:
                        src_result, src_data = src_mail.fetch(src_msg, "(BODY[HEADER])")
                    except imaplib.IMAP4.error as e:
                        log_print(f"Erro ao tentar obter o cabeçalho do e-mail no servidor de origem.")
                        log_print(f"\nError Message: \"{e}\"\n")
                        src_mail.logout()
                        dst_mail.logout()
                        return

                    # Extract the Message-ID from the header
                    encoding = chardet.detect(src_data[0][1])['encoding']
                    header = src_data[0][1].decode(encoding)
                    pattern = r"message-id:[\r\n\s]*\<?([a-z0-9_.%=+-]+@[a-z0-9_.%=+-]+)\>?"
                    message_id = re.search(pattern, header.lower(), re.IGNORECASE)

                    if message_id:
                        message_id = message_id.group(1)
                        log_print(f"\nMessage-ID: <{message_id}>")

                        # Use the Message-ID to check if the message already exists in the destination mailbox
                        dst_result, dst_data = dst_mail.search(None, "HEADER Message-ID <{}>".format(message_id))
                        if not dst_data[0]:
                            # Fetch the source message
                            src_result, src_data = src_mail.fetch(src_msg, "(RFC822)")
                            if src_result == "OK":

                                # Append the source message to the destination mailbox
                                try:
                                    log_print(f"Copiando mensagem de {mailbox_name2} para o servidor de destino...")
                                    msg = email.message_from_bytes(src_data[0][1])
                                    received_datetime = parsedate_to_datetime(msg["Date"])
                                    received_timestamp = time.mktime(received_datetime.timetuple())
                                    received_date = imaplib.Time2Internaldate(received_timestamp)
                                    dst_result, dst_data = dst_mail.append(mailbox_name, None, received_date, src_data[0][1])
                                    #                      dst_mail.append('INBOX', '', imaplib.Time2Internaldate(time.time()), data[0][1])
                                    if dst_result != "OK":
                                        log_print(f"Erro ao tentar copiar a mensagem de {mailbox_name2} para o servidor de destino.")
                                        log_print(f"dst_result: {dst_result}\ndst_data: {dst_data}")
                                        sys.exit()
                                except imaplib.IMAP4.error as e:
                                    log_print(f"Erro ao tentar copiar a mensagem de {mailbox_name2} para o servidor de destino.")
                                    log_print(f"\nError Message: \"{e}\"\n")
                                    src_mail.logout()
                                    dst_mail.logout()
                                    return
                            else:
                                log_print(f"Erro ao tentar buscar a mensagem de {mailbox_name2} para o servidor de origem.")
                                log_print(f"src_result: {src_result}\nsrc_data: {src_data}")
                                sys.exit()
                        else:
                            log_print(f"Mensagem já existe em {mailbox_name2} no servidor de destino.")
                    else:
                        log_print("Message-ID não encontrado no cabeçalho.")
                        log_print(f"header: {header}")
                        sys.exit()
            else:
                log_print(f"A pasta {mailbox_name2} está vazia.")

        # Close both IMAP connections
        src_mail.close()
        src_mail.logout()
        dst_mail.close()
        dst_mail.logout()
    
    else:
        log_print("Erro na conexão.")

# Load JSON credentials file
try:
    with open("credentials.json", "r") as file:
        json_credentials = json.load(file)
except FileNotFoundError:
    log_print("\nO arquivo credentials.json não foi encontrado.")
    log_print("Copie o credentials.json.default, renomeie para credentials.json e define as credenciais.")
    sys.exit()

for credential in json_credentials:
    log_print(f"\nIniciando a migração do e-mail <{credential['src']['user']}>...")
    migrate_emails(credential)
    log_print(f"\nFinalizado a migração do e-mail <{credential['src']['user']}>.")
log_print("\nMigração do(s) e-mail(s) finalizado.")
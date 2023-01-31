import imaplib
import chardet
import sys
import re

def migrate_emails(src_user, src_password, src_server, src_port, src_security, dst_user, dst_password, dst_server, dst_port, dst_security):

    # Connect to source IMAP server
    src_mail = imaplib.IMAP4_SSL(src_server, src_port)
    try:
        src_mail.login(src_user, src_password)
    except imaplib.IMAP4.error:
        print("Erro na autenticação no servidor de origem.")
        return

    # Connect to destination IMAP server
    dst_mail = imaplib.IMAP4_SSL(dst_server, dst_port)
    try:
        dst_mail.login(dst_user, dst_password)
    except imaplib.IMAP4.error:
        print("Erro na autenticação no servidor de destino.")
        src_mail.logout()
        return

    # Get all source mailboxes
    try:
        src_mailboxes = src_mail.list()
    except imaplib.IMAP4.error:
        print("Erro ao listar as pastas do servidor de origem.")
        src_mail.logout()
        dst_mail.logout()
        return

    if src_mailboxes[0] == "OK":

        # Loop through all source mailboxes
        for mailbox in src_mailboxes[1]:
            # Get the mailbox name and select it
            try:
                mailbox_name = mailbox.split(b'"."')[-1].strip(b'"')
                mailbox_name2 = mailbox_name.decode().strip()
            except TypeError:
                print("Erro ao obter o nome da pasta.")
                src_mail.logout()
                dst_mail.logout()
                return

            try:
                src_mail.select(mailbox_name)
            except imaplib.IMAP4.error:
                print(f"Erro ao selecionar a pasta {mailbox_name} no servidor de origem.")
                src_mail.logout()
                dst_mail.logout()
                return

            # Create the same mailbox on the destination server
            try:
                dst_mail.create(mailbox_name)
                dst_mail.select(mailbox_name)
            except imaplib.IMAP4.error:
                print(f"Erro ao criar a pasta {mailbox_name} no servidor de destino.")
                src_mail.logout()
                dst_mail.logout()
                return

            # Get all messages in the source mailbox
            src_result, src_data = src_mail.search(None, "ALL")
            if src_data[0]:
                src_msgs = src_data[0].split(b' ')

                # Loop through all messages in the source mailbox
                for src_msg in src_msgs:
                    # Fetch the message header
                    src_result, src_data = src_mail.fetch(src_msg, "(BODY[HEADER])")


                    encoding = chardet.detect(src_data[0][1])['encoding']

                    # Extract the Message-ID from the header
                    header = src_data[0][1].decode(encoding)
                    pattern = r"message-id:[\r\n\s]*\<?([a-z0-9_.%=+-]+@[a-z0-9_.%=+-]+)\>?"
                    message_id = re.search(pattern, header.lower(), re.IGNORECASE)

                    if message_id:
                        message_id = message_id.group(1)

                        # Use the Message-ID to check if the message already exists in the destination mailbox
                        dst_result, dst_data = dst_mail.search(None, "HEADER Message-ID <{}>".format(message_id))
                        if not dst_data[0]:
                            # Fetch the source message
                            src_result, src_data = src_mail.fetch(src_msg, "(RFC822)")
                            if src_result == "OK":
                                # Append the source message to the destination mailbox
                                dst_result, dst_data = dst_mail.append(mailbox_name, None, None, src_data[0][1])
                                if dst_result == "OK":
                                    print(f"Mensagem copiada de {mailbox_name2} para o servidor de destino. Message-ID: {message_id}")
                                else:
                                    print(f"Erro ao tentar copiar de {mailbox_name2} para o servidor de destino. Message-ID: {message_id}")
                                    sys.exit(dst_result, dst_data)
                            else:
                                print(f"Erro ao buscar a mensagem de {mailbox_name2} para o servidor de origem: {src_data}")
                                sys.exit(src_result, src_data)
                        else:
                            print(f"Mensagem já existe em {mailbox_name2} no servidor de destino. Message-ID: {message_id}")
                    else:
                        print("Message-ID não encontrado no cabeçalho")
                        sys.exit(header)
            else:
                print(f"A pasta {mailbox_name2} está vazia")

        # Close both IMAP connections
        src_mail.close()
        src_mail.logout()
        dst_mail.close()
        dst_mail.logout()
    
    else:
        print("Erro na conexão.")

# Source IMAP credentials
src_user = "user@domain.com"
src_password = "password"
src_server = "mail.domain.com"
src_port = 993
src_security = "SSL/TLS"

# Destination IMAP credentials
dst_user = "contato@domain.com"
dst_password = "password"
dst_server = "mail.domain.com"
dst_port = 993
dst_security = "SSL/TLS"

# Call the function
migrate_emails(src_user, src_password, src_server, src_port, src_security, dst_user, dst_password, dst_server, dst_port, dst_security)
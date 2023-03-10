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

import chardet, datetime, email, imaplib, json, os, pprint, re, sys, time, argparse

from email.utils import parsedate_to_datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

class SyncImapEmail:

    # Array with all script messages previously defined here.
    __messages = {
        "migrate_start": "Starting email migration <{}>...",
        "migrate_finish": "Finished email migration <{}>.",
        "migrate_success": "Email(s) migration completed.",
        "check_log": "Check the log file to verify if there were any errors during the migration process.",
        "file_name": "File name: {}",
        "lang_not_found": "The lang/{}.json file was not found. The default language set is: en-us (English).",
        "cred_not_found": "The credentials.json file was not found.",
        "copy_cred_file": "Copy the credentials.json.default, rename it to credentials.json, and set the credentials.",
        "oauth_not_found": "The oauth_client_secret.json file was not found.",
        "oauth_required": "To proceed, the Google Cloud credentials file is required.",
        "create_oauth_token": "Creating OAUTH2 token for email: <{}>",
        "auth_app_url": "Visit the URL to authorize this application:",
        "auth_code": "Enter the authorization code: ",
        "connect_src_server": "Connecting to the source server...",
        "connect_src_server_error": "Error connecting to the source server.",
        "auth_token_src_server": "Authenticating with OAUTH2 token on the source server...",
        "auth_src_server": "Authenticating with email and password on the source server...",
        "auth_src_server_error": "Error authenticating on the source server.",
        "connect_server_verify": "Verify if the email configuration is correct:",
        "auth_server_verify": "Verify if the email and password are correct.",
        "connect_dst_server": "Connecting to the destination server...",
        "connect_dst_server_error": "Error connecting to the destination server.",
        "auth_token_dst_server": "Authenticating with OAUTH2 token on the destination server...",
        "auth_dst_server": "Authenticating with email and password on the destination server...",
        "auth_dst_server_error": "Error authenticating on the destination server.",
        "get_src_folders": "Getting the list of folders on the source server...",
        "get_src_folders_error": "Error trying to get the list of folders on the source server.",
        "except_error": "Exception error: \"{}\"",
        "get_dst_folders": "Getting the list of folders on the destination server...",
        "get_dst_folders_error": "Error trying to get the list of folders on the destination server.",
        "select_src_folder": "Selecting {} folder from the source server...",
        "select_src_folder_error": "Error trying to select the {} folder on the source server.",
        "create_dst_folder": "Creating {} folder on the destination server...",
        "create_dst_folder_error": "Error trying to create the {} folder on the destination server.",
        "get_src_msg_header_error": "Error trying to get the message header on the source server.",
        "copy_src_msg_to_dst_folder": "Copying message from {} folder on the source server to {} folder on the destination server...",
        "add_dst_msg_error": "Error trying to add the message to the {} folder on the destination server.",
        "get_src_msg_error": "Error trying to fetch the message in the {} folder on the source server.",
        "dst_msg_exists": "Message already exists in the {} folder on the destination server.",
        "msg_id_not_found": "Message-ID not found in the header.",
        "src_folder_empty": "The {} folder is empty on the source server."
    }

    # Initial method of the SyncImapEmail class.
    def __init__(self):
        self.__log_start()
        self.__load_arguments()
        credentials = self.__load_credentials()
        self.__generate_tokens(credentials)
        for credential in credentials:
            self.__log_print("\n" + self.__messages["migrate_start"].format(credential['src']['email']))
            conn_result, src_mail, dst_mail = self.__connect(credential)
            if conn_result == "OK":
                self.__migrate(src_mail, dst_mail)
            self.__log_print("\n" + self.__messages["migrate_finish"].format(credential['src']['email']))
            self.__disconnect(src_mail, dst_mail)
        self.__log_print("\n" + self.__messages["migrate_success"])
        self.__log_print("\n" + self.__messages["check_log"])
        self.__log_print(self.__messages["file_name"].format(self.__log_filename))

    # Load command line arguments
    def __load_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-l", "--language")
        args = parser.parse_args()
        if args.language:
            self.__set_language(args.language)

    # Load JSON credentials file
    def __load_credentials(self):
        try:
            with open("credentials.json", "r") as file:
                credentials = json.load(file)
        except FileNotFoundError:
            self.__log_print("\n" + self.__messages["cred_not_found"])
            self.__log_print(self.__messages["copy_cred_file"])
            sys.exit()
        return credentials

    # Set language and load messages
    def __set_language(self, language):
        try:
            with open(f"lang/{language}.json", "r") as file:
                messages = json.load(file)
            self.__messages = messages.copy()
            self.__log_print("\n" + self.__messages["lang_found"].format(language))
        except FileNotFoundError:
            self.__log_print("\n" + self.__messages["lang_not_found"].format(language))

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
                self.__log_print("\n" + self.__messages["oauth_not_found"])
                self.__log_print(self.__messages["oauth_required"])
                self.__log_print("https://cloud.google.com/docs/authentication/client-libraries")
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
                    self.__log_print(f"\n" + self.__messages["create_oauth_token"].format(data['email']) + "\n")
                    flow = InstalledAppFlow.from_client_secrets_file('oauth_client_secret.json', self.__scopes)
                    prompt_msg = self.__messages["auth_app_url"] + "\n{url}"
                    code_msg = self.__messages["auth_code"]
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
            self.__log_print(self.__messages["connect_src_server"])
            src_mail = self.__imap_security(credential["src"]["security"], credential["src"]["server"], credential["src"]["port"])
        except ConnectionRefusedError as e:
            self.__log_print("\n" + self.__messages["connect_src_server_error"] + "\n" + self.__messages["connect_server_verify"])
            self.__log_print(credential["src"], pprint.pprint)
            self.__log_print("\n" + self.__messages["except_error"].format(e))
            return "ERROR", None, None

        # Authenticate a connection to the source IMAP server
        if credential["src"]["security"] == "OAUTH2":
            oauth2 = True
            email = re.sub(r'[^\w._-]+', '_', credential["src"]["email"])
            creds = Credentials.from_authorized_user_file(f"token_{email}.json", self.__scopes)
            auth_string = f"user={credential['src']['email']}\1auth=Bearer {creds.token}\1\1"
            self.__log_print(self.__messages["auth_token_src_server"])
        else:
            oauth2 = False
            self.__log_print(self.__messages["auth_src_server"])
        try:
            if oauth2:
                src_mail.authenticate('XOAUTH2', lambda x: auth_string)
            else:
                src_mail.login(credential["src"]["email"], credential["src"]["password"])
        except imaplib.IMAP4.error as e:
            self.__log_print("\n" + self.__messages["auth_src_server_error"])
            if oauth2:
                os.remove(f"token_{email}.json")
            else:
                self.__log_print(self.__messages["auth_server_verify"])
            self.__log_print("\n" + self.__messages["except_error"].format(e))
            return "ERROR", src_mail, None

        # Connect to destination IMAP server
        try:
            self.__log_print(self.__messages["connect_dst_server"])
            dst_mail = self.__imap_security(credential["dst"]["security"], credential["dst"]["server"], credential["dst"]["port"])
        except ConnectionRefusedError as e:
            self.__log_print("\n" + self.__messages["connect_dst_server_error"] + "\n" + self.__messages["connect_server_verify"])
            self.__log_print(credential["dst"], pprint.pprint)
            self.__log_print("\n" + self.__messages["except_error"].format(e))
            return "ERROR", src_mail, None

        # Authenticate a connection to the destination IMAP server
        if credential["dst"]["security"] == "OAUTH2":
            oauth2 = True
            email = re.sub(r'[^\w._-]+', '_', credential["dst"]["email"])
            creds = Credentials.from_authorized_user_file(f"token_{email}.json", self.__scopes)
            auth_string = f"user={credential['dst']['email']}\1auth=Bearer {creds.token}\1\1"
            self.__log_print(self.__messages["auth_token_dst_server"])
        else:
            oauth2 = False
            self.__log_print(self.__messages["auth_dst_server"])
        try:
            if oauth2:
                dst_mail.authenticate('XOAUTH2', lambda x: auth_string)
            else:
                dst_mail.login(credential["dst"]["email"], credential["dst"]["password"])
        except imaplib.IMAP4.error as e:
            self.__log_print("\n" + self.__messages["auth_dst_server_error"])
            if oauth2:
                os.remove(f"token_{email}.json")
            else:
                self.__log_print(self.__messages["auth_server_verify"])
            self.__log_print("\n" + self.__messages["except_error"].format(e))
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
            self.__log_print(self.__messages["get_src_folders"])
            src_mailboxes = src_mail.list()
        except imaplib.IMAP4.error as e:
            self.__log_print("\n" + self.__messages["get_src_folders_error"])
            self.__log_print("\n" + self.__messages["except_error"].format(e))
            return
        src_mailboxes = [src_mailbox.decode() for src_mailbox in src_mailboxes[1]]
        src_separator = re.search('"(/|.)"', src_mailboxes[0]).group(1)

        # Checks if source mailboxes are prefixed with "INBOX.".
        src_prefix = "INBOX."
        for src_mailbox in src_mailboxes:
            src_mailbox = src_mailbox.split(f'"{src_separator}"')[-1].strip() 
            if src_mailbox.upper() == "INBOX":
                continue
            if src_mailbox.find(src_prefix) == -1:
                src_prefix = None
                break

        # Get all destination mailboxes
        try:
            self.__log_print(self.__messages["get_dst_folders"])
            dst_mailboxes = dst_mail.list()
        except imaplib.IMAP4.error as e:
            self.__log_print("\n" + self.__messages["get_dst_folders_error"])
            self.__log_print("\n" + self.__messages["except_error"].format(e))
            return
        dst_mailboxes = [dst_mailbox.decode() for dst_mailbox in dst_mailboxes[1]]
        dst_separator = re.search('"(/|.)"', dst_mailboxes[0]).group(1)

        # Checks if destination mailboxes are prefixed with "INBOX.".
        dst_prefix = "INBOX."
        for dst_mailbox in dst_mailboxes:
            dst_mailbox = dst_mailbox.split(f'"{dst_separator}"')[-1].strip() 
            if dst_mailbox.upper() == "INBOX":
                continue
            if dst_mailbox.find(dst_prefix) == -1:
                dst_prefix = None
                break

        mailboxes_defaults = ["Sent", "Drafts", "Junk", "Trash", "Archive"]

        # Loop through all source mailboxes
        for src_mailbox in src_mailboxes:

            # Mailboxes that are not copied
            if re.search(r"\\[Noselect|All|Flagged]", src_mailbox):
                continue

            mailbox_default = re.search(r"[\\|\.]+({})".format("|".join(mailboxes_defaults)), src_mailbox)
            if mailbox_default:
                mailbox_default = mailbox_default.group(1)

            src_mailbox = src_mailbox.split(f'"{src_separator}"')[-1].strip()
            try:
                self.__log_print(self.__messages["select_src_folder"].format(src_mailbox))
                src_mail.select(src_mailbox)
            except imaplib.IMAP4.error as e:
                self.__log_print("\n" + self.__messages["select_src_folder_error"].format(src_mailbox))
                self.__log_print("\n" + self.__messages["except_error"].format(e))
                continue

            # Get all messages in the source mailbox
            src_result, src_data = src_mail.search(None, "ALL")
            if src_data[0]:
                src_msgs = src_data[0].split(b' ')

                if mailbox_default:
                    for mailbox in dst_mailboxes:
                        if re.search(r"[\\|\.]{}".format(mailbox_default), mailbox):
                            dst_mailbox = mailbox.split(f'"{dst_separator}"')[-1].strip()
                else:
                    dst_mailbox = src_mailbox
                    if dst_mailbox.upper() != "INBOX" and dst_prefix != src_prefix:
                        if src_prefix:
                            dst_mailbox = dst_mailbox.replace(src_prefix, "")
                        else:
                            dst_mailbox = '"INBOX.{}"'.format(dst_mailbox.strip('"'))
                    if src_separator != dst_separator:
                        dst_mailbox = dst_mailbox.replace(src_separator, dst_separator)

                if dst_separator == "/":
                    dst_mailbox = dst_mailbox.replace("INBOX/", "")
                if dst_mailbox.find("[Gmail]") != -1 and dst_mail.host.find("gmail.com") == -1:
                    dst_mailbox = dst_mailbox.replace("[Gmail]/", "")

                # Create the same mailbox on the destination server
                try:
                    dst_result, dst_data = dst_mail.select(dst_mailbox)
                    if dst_result != "OK":
                        self.__log_print(self.__messages["create_dst_folder"].format(dst_mailbox))
                        dst_mail.create(dst_mailbox)
                        dst_mail.select(dst_mailbox)
                except imaplib.IMAP4.error as e:
                    self.__log_print(self.__messages["create_dst_folder_error"].format(dst_mailbox))
                    self.__log_print("\n" + self.__messages["except_error"].format(e))
                    continue

                # Loop through all messages in the source mailbox
                for src_msg in src_msgs:
                    # Fetch the message header
                    try:
                        src_result, src_data = src_mail.fetch(src_msg, "(BODY.PEEK[HEADER])")
                    except imaplib.IMAP4.error as e:
                        self.__log_print(self.__messages["get_src_msg_header_error"])
                        self.__log_print("\n" + self.__messages["except_error"].format(e))
                        continue

                    # Extract the Message-ID from the header
                    encoding = chardet.detect(src_data[0][1])['encoding']
                    header = src_data[0][1].decode(encoding)
                    pattern = r"message-id:[\r\n\s]*\<?([a-z0-9_.%$!#&/*=+-]+@[a-z0-9_.%$!#&/*=+-]+)\>?"
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
                                try:
                                    msg = email.message_from_bytes(src_data[0][1])
                                    received_datetime = parsedate_to_datetime(msg["Date"])
                                    received_timestamp = time.mktime(received_datetime.timetuple())
                                    received_date = imaplib.Time2Internaldate(received_timestamp)
                                except TypeError as e:
                                    received_date = None

                                # Append the source message to the destination mailbox
                                try:
                                    self.__log_print(self.__messages["copy_src_msg_to_dst_folder"].format(src_mailbox, dst_mailbox))
                                    dst_result, dst_data = dst_mail.append(dst_mailbox, None, received_date, src_data[0][1])
                                    if dst_result != "OK":
                                        self.__log_print(self.__messages["add_dst_msg_error"].format(dst_mailbox))
                                        self.__log_print(f"dst_result: {dst_result}\ndst_data: {dst_data}")
                                except imaplib.IMAP4.error as e:
                                    self.__log_print(self.__messages["add_dst_msg_error"].format(dst_mailbox))
                                    self.__log_print("\n" + self.__messages["except_error"].format(e))
                                    continue

                                # Preserved original message flags when copying to target email
                                flags = src_mail.fetch(src_msg, "(FLAGS)")[1][0]
                                flags = re.findall(r'\\\w+', flags.decode().upper())
                                if "\\RECENT" in flags:
                                    flags.remove("\\RECENT")
                                if flags:
                                    flags = ' '.join(flags)
                                    dst_data = dst_mail.search(None, 'HEADER Message-ID "{}"'.format(message_id))[1]
                                    if len(dst_data[0].split()) > 0:
                                        dst_mail.store(dst_data[0].split()[-1], "+FLAGS", flags)
                            else:
                                self.__log_print(self.__messages["get_src_msg_error"].format(src_mailbox))
                                self.__log_print(f"src_result: {src_result}\nsrc_data: {src_data}")
                        else:
                            self.__log_print(self.__messages["dst_msg_exists"].format(dst_mailbox))
                    else:
                        self.__log_print(self.__messages["msg_id_not_found"])
                        self.__log_print(f"header: {header}")
            else:
                self.__log_print(self.__messages["src_folder_empty"].format(src_mailbox))

if __name__ == '__main__':
    SyncImapEmail()
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

# Python module imports
import sys
import os
import re
import json
import imaplib
from datetime import datetime
from locale import getlocale
from pprint import pprint
from socket import gaierror
from time import mktime, sleep
from email import message_from_bytes
from email.utils import parseaddr, parsedate_to_datetime

# Third-party module imports
from argparse import ArgumentParser
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError, TransportError
from google_auth_oauthlib.flow import InstalledAppFlow
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

CODE = 'UTF-8'
CR = '\r'
LF = '\n'

# Emoji unicode codes
EMOJI = [
    '\U0001F3C1 ', # Checkered flag
    '\U0001F4AC ', # Speech Bubble
    '\U0001F4B2 ', # Dollar symbol
    '\U0001F4CC ', # Marker pin
    '\U0001F4EB ', # Mailbox with raised flap
    '\U0001F4EC ', # Open mailbox with raised flap
    '\U0001F4E5 ', # Input box with down arrow
    '\U0001F4E7 ', # Letter Envelope
    '\U0001F49B ', # Yellow heart
    '\U0001F510 ', # Locked padlock with key
    '\U0001F557 ', # Clock showing 10 o'clock
    '\U0001F6AB '  # Prohibition sign
]
if sys.platform == 'win32':
    EMOJI = ['' for i in range(len(EMOJI))]

# Default language code
LANGUAGE_DEFAULT = 'en_us'

# Default total reconnection attempts
ATTEMPTS_RECONN = 5

# Default timeout to try to reconnect
TIMEOUT_RECONN = 30

# The maximum allowable limit of the timeout
TIMEOUT_MAX = 300

# Version script
VERSION = '1.0.1'

class SyncImapEmail:
    """The script copies all messages from one email to another using the IMAP protocol.

       Includes the following features and supports:
           - Authentication security: TLS, STARTTLS, SSL, and OAuth2 (Gmail);
           - Message record: Saves the tasks in a text file for process verification;
           - Multi-language: multiple languages for user's choice.
    """

    # Dictionary for messages
    _msg = {
        "argparse_description": ("The script copies all messages from one email to another using"
                                 " the IMAP protocol."),
        "argparse_help": "# Show this help message and exit.",
        "argparse_version": "# Show script version number and exit.",
        "argparse_debug": "# Enables debugging and displays details with exception errors.",
        "argparse_language": "# Set language code for messages.",
        "argparse_gen_tokens": "# Just generate the tokens without starting the migration.",
        "argparse_no_logs": "# Message log will not be saved.",
        "argparse_timeout": "# Set reconnection attempt timeout. Default: {} second(s)",
        "argparse_attempts": "# Set the total reconnection attempts. Default: {} attempt(s)",
        "auth_server_email": "Authenticating with email and password on the mail server...",
        "auth_server_token": "Authenticating with OAUTH2 token on mail server...",
        "auth_server_error": "Error authenticating to mail server.",
        "auth_server_verify": "Verify that the email and password are correct.",
        "append_dst_message": "Sending message to folder {} on destination server...",
        "append_dst_message_error": ("Error trying to add message to folder {} on destination"
                                     " server."),
        "clock_timeout_second": "Time left: {} seconds...",
        "conn_fail_reconn": "Connection failed. Reconnecting in {} seconds. (Attempt: {}/{})...",
        "connect_server": "Connecting to mail server...",
        "connect_server_error": "Error connecting to the mail server.",
        "connect_server_verify": "Verify that the email configuration is correct:",
        "create_dst_folder": "Creating folder {} on destination server...",
        "create_dst_folder_error": "Error trying to create folder {} on destination server.",
        "cred_copy_file": ("Copy the credentials.json.default, rename it to credentials.json"
                           " and set the credentials."),
        "cred_json_error": "The credentials.json file is not formatted correctly.",
        "cred_not_found": "The credentials.json file was not found.",
        "donate_dev": "If this script was helpful, please help with a donation.",
        "except_error": "Exception error: {}",
        "fetch_src_folder": "Downloading message from folder {} on source server...",
        "fetch_src_error": "Error trying to fetch message from folder {} on source server.",
        "flags_src_error": "Error trying to get message flags from origin server.",
        "flags_add_dst_error": "Error trying to add flags to message on destination server.",
        "folder_src_empty": "The folder {} is empty on the source server.",
        "header_src_error": "Error trying to get message header from origin server.",
        "lang_found": "The language set is: {} (english United States).",
        "lang_incomplete": "The translation of the lang/{}.json file is incomplete.",
        "lang_json_error": "The lang/{}.json file is not formatted correctly.",
        "lang_not_found": "The lang/{}.json file was not found. The default language set is: {}.",
        "limit_reconn_timeout": "The maximum allowable timeout limit is {}.",
        "list_src_folders": "Getting the list of folders on the source server...",
        "list_src_folders_error": "Error trying to get list of folders on source server.",
        "list_dst_folders": "Getting the list of folders on the destination server...",
        "list_dst_folders_error": "Error trying to get list of folders on destination server.",
        "log_check": "Check the log file if there were no errors during the migration process.",
        "log_filename": "Log file name: {}",
        "message_dst_exists": "Message already exists in folder {} on destination server.",
        "messageid_not_found": "Message-ID not found in header.",
        "migrate_start": "Starting migration of email <{}>...",
        "migrate_finish": "Finished migrating email <{}>.",
        "migrate_success": "Completed the email migration process.",
        "nodename_serv_error": "Error trying to access host address \"{}\".",
        "nodename_serv_verify": "Verify that your Internet connection is working.",
        "oauth_app_url": "Visit the URL to authorize this script:",
        "oauth_code": "Enter the authorization code: ",
        "oauth_create_token": "Creating OAUTH2 token from email: <{}>",
        "oauth_invalid_grant": "Incorrect authorization code.",
        "oauth_not_found": "The oauth_client_secret.json file was not found.",
        "oauth_required": "You will need the Google Cloud credentials file to proceed.",
        "script_interrupted": "Script interrupted by the user.",
        "search_src_msgs": "Getting list of messages from folder {} on source server.",
        "search_src_msgs_error": ("Error trying to get list of messages from folder {} on source"
                                  " server."),
        "select_src_folder": "Selecting folder {} from source server...",
        "select_src_folder_error": "Error trying to select folder {} on source server.",
        "select_dst_folder": "Selecting folder {} of destination server...",
        "select_dst_folder_error": "Error trying to select folder {} on destination server.",
        "start_conn_server_src": "Start connection and authentication with source server.",
        "start_conn_server_dst": "Start connection and authentication with destination server."
    }

    @property
    def attempts(self) -> int:
        """Property for getting and setting the `_attempts` attribute."""
        return self._attempts

    @attempts.setter
    def attempts(self, value: int):
        if isinstance(value, int):
            self._attempts = value

    @property
    def timeout(self) -> int:
        """Property for getting and setting the `_timeout` attribute."""
        return self._timeout

    @timeout.setter
    def timeout(self, value: int):
        if isinstance(value, int):
            if value > TIMEOUT_MAX:
                self._timeout = TIMEOUT_MAX
                print(self._msg['limit_reconn_timeout'].format(TIMEOUT_MAX))
            else:
                self._timeout = value

    @property
    def debug(self) -> bool:
        """Property for getting and setting the `_debug` attribute."""
        return self._debug

    @debug.setter
    def debug(self, value: bool):
        if isinstance(value, bool):
            self._debug = value

    def __init__(self, language = getlocale()[0], auto_start = True, no_logs = False):
        """Construction method for initial preparation of the class.

            - language: set language code for messages;
            - auto_start: starts the migration automatically;
            - no_logs: message log will not be saved.
        """

        # Checks if you want to save the log file and sets the name to the current date
        if '--no-logs' not in sys.argv and not no_logs:
            now = datetime.now()
            self._log_filename = f"log_{now.strftime('%Y%m%d_%H%M%S')}.txt"

        # Check which language will be set
        lang_hidden = True
        if '--language' in sys.argv:
            lang_index = sys.argv.index('--language')
            if lang_index < len(sys.argv) - 1:
                language = sys.argv[lang_index + 1]
                if not any(re.match(r'^(-h|--(h|he|hel|help))$', arg) for arg in sys.argv):
                    lang_hidden = False
        elif not language or not os.path.exists(f'lang/{language.lower()}.json'):
            language = LANGUAGE_DEFAULT
        language = language.lower()
        if language != LANGUAGE_DEFAULT:
            self._set_language(language, lang_hidden)

        if __name__ == '__main__':
            self._parse_arguments()
        else:
            self._parser_args = None

        self._debug = False
        self._timeout = TIMEOUT_RECONN
        self._attempts = ATTEMPTS_RECONN
        self._mail = {}
        if not auto_start:
            return

        try:
            credentials = self.load_credentials()
            if not credentials:
                return

            self.start(credentials)
        except KeyboardInterrupt:
            self._log_print(LF + EMOJI[11] + self._msg['script_interrupted'])
            sys.exit()

    def _set_language(self, language: str, hidden_msg = False):
        """Set language and load messages.

            - language: the language that will be used for displaying messages;
            - hidden_msg: if the language does not exist, it will hide the error message.
        """

        try:
            error_msg = ''
            with open(f'lang/{language.lower()}.json', 'r', encoding = CODE) as file:
                messages = json.load(file)
            messages_old = self._msg.copy()
            self._msg.update(messages)
            if hidden_msg:
                return
            if not set(messages_old.keys()).issubset(set(messages.keys())):
                print(LF + EMOJI[1] + self._msg['lang_incomplete'].format(language))
            print(LF + EMOJI[1] + self._msg['lang_found'].format(language))
        except json.decoder.JSONDecodeError:
            error_msg = self._msg['lang_json_error'].format(language)
        except FileNotFoundError:
            error_msg = self._msg['lang_not_found'].format(language, LANGUAGE_DEFAULT)
        if not hidden_msg and error_msg:
            print(LF + EMOJI[11] + error_msg)

    def _parse_arguments(self):
        """Defines the arguments parser for ease of use on the command line."""

        parser = ArgumentParser(add_help = False,
                            description = self._msg['argparse_description'])
        parser.add_argument('-h', '--help', action = 'help',
                            help = self._msg['argparse_help'])
        parser.add_argument('-v', '--version', action = 'version', version = VERSION,
                            help = self._msg['argparse_version'])
        parser.add_argument('--debug', action = 'store_true',
                            help = self._msg['argparse_debug'])
        parser.add_argument('--language', metavar = 'CODE',
                            help = self._msg['argparse_language'])
        parser.add_argument('--gen-tokens', action = 'store_true',
                            help = self._msg['argparse_gen_tokens'])
        parser.add_argument('--no-logs', action = 'store_true',
                            help = self._msg['argparse_no_logs'])
        parser.add_argument('--timeout', metavar = 'N_SECOND',
                            help = self._msg['argparse_timeout'].format(TIMEOUT_RECONN))
        parser.add_argument('--attempts', metavar = 'NUMBER',
                            help = self._msg['argparse_attempts'].format(ATTEMPTS_RECONN))
        self._parser_args = parser.parse_args()

    def _log_print(self, message: str, use_pprint = False):
        """Print the values in sys.stdout and append to the log file.

            - message: the text message from stdout;
            - use_pprint: to use the `pprint` command instead of `print`.
        """

        if use_pprint:
            pprint(message)
            sys.stdout.flush()
        else:
            print(message, flush = True)
        if not hasattr(self, '_log_filename'):
            return
        if use_pprint:
            message = repr(message)
        with open(self._log_filename, 'a', encoding = CODE) as file:
            file.write(message + LF)

    def _imap_conn(self, host: str, port: int, security: str):
        """Connect via IMAP on host and port with some security.

            - host: IMAP server address;
            - port: IMAP server port number;
            - security: type of security (STARTTLS, SSL/TLS or OAUTH2).
        """

        if security and security.upper() in ('SSL', 'TLS', 'SSL/TLS', 'OAUTH2'):
            port = int(port) if port else imaplib.IMAP4_SSL_PORT
            rtn = imaplib.IMAP4_SSL(host, port)
        else:
            port = int(port) if port else imaplib.IMAP4_PORT
            rtn = imaplib.IMAP4(host, port)
            if security and security.upper() == 'STARTTLS':
                rtn.starttls()
        return rtn

    def _auth_server(self, cred: dict):
        """Connect and authenticate the server with the credentials.

            - cred: the email credential.
        """

        # Connect to IMAP server
        try:
            self._log_print(EMOJI[9] + self._msg['connect_server'])
            imap = self._imap_conn(cred.get('server'), cred.get('port'), cred.get('security'))
        except gaierror:
            self._log_print(LF + EMOJI[11] + self._msg['nodename_serv_error']
                            .format(cred.get('server')))
            self._log_print(LF + EMOJI[1] + self._msg['nodename_serv_verify'])
        except ConnectionRefusedError as error:
            self._log_print(LF + EMOJI[11] + self._msg['connect_server_error'])
            if self._debug:
                self._log_print(LF + EMOJI[3] + self._msg['except_error'].format(error))
            self._log_print(LF + EMOJI[1] + self._msg['connect_server_verify'])
            self._log_print(cred, use_pprint= True)

        if not 'imap' in locals():
            return 'NO'

        # Authenticate a connection to IMAP server
        if cred.get('security', '').upper() == 'OAUTH2':
            oauth2 = True
            token, token_file = self.generate_token(cred['email'])
            auth_string = f"user={cred['email']}\1auth=Bearer {token}\1\1"
            self._log_print(EMOJI[9] + self._msg['auth_server_token'])
        else:
            oauth2 = False
            self._log_print(EMOJI[9] + self._msg['auth_server_email'])
        try:
            if oauth2:
                imap.authenticate('XOAUTH2', lambda x: auth_string)
            else:
                imap.login(cred.get('email'), cred.get('password', ''))
        except imaplib.IMAP4.error as error:
            self._log_print(LF + EMOJI[11] + self._msg['auth_server_error'])
            if self._debug:
                self._log_print(LF + EMOJI[3] + self._msg['except_error'].format(error))
            if oauth2:
                os.remove(token_file)
            else:
                self._log_print(LF + EMOJI[1] + self._msg['auth_server_verify'])
            return 'NO'

        return 'OK', imap

    def _connect(self):
        """Make email connections."""

        for key, mail in self._mail.items():
            self._log_print(EMOJI[9] + self._msg[f'start_conn_server_{key}'])
            status, data = self._auth_server(mail['cred'])
            if status != 'OK':
                self._disconnect()
                return False
            mail['imap'] = data

        return True

    def _reconnect(self):
        """Try to reconnect with the mails servers."""

        for attempt in range(1, self._attempts + 1):
            self._log_print(LF + EMOJI[11] + self._msg['conn_fail_reconn']
                            .format(self._timeout, attempt, self._attempts))
            for i in range(self._timeout):
                text = (CR + EMOJI[10] + self._msg['clock_timeout_second']
                        .format(self._timeout - i))
                print(f'{text: <20}', end = '', flush = True)
                sleep(1)
            print(f'{CR: <40}', end = '', flush = True)

            error_reconn = False
            for mail in self._mail.items():
                status, data = self._auth_server(mail[1]['cred'])
                if status != 'OK':
                    error_reconn = True
                    break
                mail[1]['imap'] = data
            if not error_reconn:
                return

        sys.exit(1)

    def _disconnect(self):
        """Close any open sessions and log out."""

        if self._mail['src'].get('imap'):
            if self._mail['src']['imap'].state == 'SELECTED':
                self._mail['src']['imap'].close()
            self._mail['src']['imap'].logout()

        if self._mail['dst'].get('imap'):
            if self._mail['dst']['imap'].state == 'SELECTED':
                self._mail['dst']['imap'].close()
            self._mail['dst']['imap'].logout()

    def _get_allmessages(self, src_mailbox: str):
        """Get all messages in the source mailbox.
        
            - src_mailbox: the source email mailbox.
        """

        while True:
            try:
                if self._mail['src']['imap'].state != 'SELECTED':
                    self._mail['src']['imap'].select(src_mailbox)
                self._log_print(EMOJI[1] + self._msg['search_src_msgs'].format(src_mailbox))
                status, data = self._mail['src']['imap'].search(None, 'ALL')
                break
            except (imaplib.IMAP4.abort, TimeoutError):
                self._reconnect()
            except imaplib.IMAP4.error as error:
                status, data = 'NO', error
                break
        if status != 'OK':
            self._log_print(LF + EMOJI[11] + self._msg['search_src_msgs_error']
                            .format(src_mailbox))
            if self._debug:
                self._log_print(LF + EMOJI[3] + self._msg['except_error'].format(data))
            data = None
        elif not data[0]:
            self._log_print(EMOJI[1] + self._msg['folder_src_empty'].format(src_mailbox))
            data = None
        else:
            data = data[0].split(b' ')
        return data

    def _find_foldername(self, src_mailbox: str):
        """Gets the mailbox folder name of the destination server.
        
            - src_mailbox: the source email mailbox.
        """

        label_default = '|'.join(['Sent', 'Drafts', 'Junk', 'Trash', 'Archive'])
        label_default = re.search(fr'[\\|\.]+({label_default})', src_mailbox)
        if label_default:
            label_default = label_default.group(1)
            for dst_mailbox in self._mail['dst']['all_mailboxes']:
                if re.search(fr'[\\|\.]{label_default}', dst_mailbox):
                    foldername = dst_mailbox.split(
                        f'"{self._mail["dst"]["separator"]}"')[-1].strip()
        else:
            foldername = src_mailbox
            if (self._mail['dst']['prefix'] != self._mail['src']['prefix']
                and foldername.upper() != 'INBOX'):
                if self._mail['src']['prefix']:
                    foldername = foldername.replace(self._mail['src']['prefix'], '')
                else:
                    foldername = foldername.strip('"')
                    foldername = f'"INBOX.{foldername}"'
            if self._mail['src']['separator'] != self._mail['dst']['separator']:
                foldername = foldername.replace(self._mail['src']['separator'],
                                                self._mail['dst']['separator'])
        if self._mail['dst']['separator'] == '/':
            foldername = foldername.replace('INBOX/', '')
        if (self._mail['dst']['imap'].host.find('gmail.com') == -1
            and foldername.find('[Gmail]') != -1):
            foldername = foldername.replace(f'[Gmail]{self._mail["dst"]["separator"]}', '')
        return foldername

    def _get_mailboxes_info(self):
        """Gets mailboxes, separator and prefix used in folders."""

        for key, mail in self._mail.items():
            while True:
                try:
                    self._log_print(EMOJI[1] + self._msg[f'list_{key}_folders'])
                    status, data = mail['imap'].list()
                    break
                except (imaplib.IMAP4.abort, TimeoutError):
                    self._reconnect()
                except imaplib.IMAP4.error as error:
                    status, data = 'NO', error
                    break
            if status != 'OK':
                self._log_print(LF + EMOJI[11] + self._msg[f'list_{key}_folders_error'])
                if self._debug:
                    self._log_print(LF + EMOJI[3] + self._msg['except_error'].format(data))
                return False

            mail['all_mailboxes'] = [mailbox.decode() for mailbox in data]
            mail['separator'] = re.search('"(/|.)"', mail['all_mailboxes'][0]).group(1)

            # Checks if mailboxes are prefixed with 'INBOX.'.
            prefix = 'INBOX.'
            for mailbox in mail['all_mailboxes']:
                mailbox = mailbox.split(f'"{mail["separator"]}"')[-1].strip()
                if mailbox.upper() == 'INBOX':
                    continue
                if mailbox.find(prefix) == -1:
                    prefix = None
                    break
            mail['prefix'] = prefix

        return True

    def _set_src_mailbox(self, src_mailbox: str):
        """Select mailbox on source server.
        
            - src_mailbox: the source email mailbox.
        """

        while True:
            try:
                self._log_print(EMOJI[1] + self._msg['select_src_folder'].format(src_mailbox))
                status, data = self._mail['src']['imap'].select(src_mailbox)
                break
            except (imaplib.IMAP4.abort, TimeoutError):
                self._reconnect()
            except imaplib.IMAP4.error as error:
                status, data = 'NO', error
                break
        if status != 'OK':
            self._log_print(LF + EMOJI[11] + self._msg['select_src_folder_error']
                            .format(src_mailbox))
            if self._debug:
                self._log_print(LF + EMOJI[3] + self._msg['except_error'].format(data))
        return bool(status == 'OK')

    def _set_dst_mailbox(self, dst_mailbox: str):
        """Select mailbox on destination server.
        
            - dst_mailbox: the destination email mailbox.
        """

        while True:
            # Select mailbox on destination server
            try:
                self._log_print(EMOJI[1] + self._msg['select_dst_folder'].format(dst_mailbox))
                data = self._mail['dst']['imap'].select(dst_mailbox)
            except (imaplib.IMAP4.abort, TimeoutError):
                self._reconnect()
                continue
            except imaplib.IMAP4.error as error:
                self._log_print(EMOJI[11] + self._msg['select_dst_folder_error']
                                .format(dst_mailbox))
                if self._debug:
                    self._log_print(LF + EMOJI[3] + self._msg['except_error'].format(error))
                break

            if data[0] == 'OK':
                return True

            # Create the same mailbox on the destination server
            try:
                self._log_print(EMOJI[1] + self._msg['create_dst_folder'].format(dst_mailbox))
                self._mail['dst']['imap'].create(dst_mailbox)
            except (imaplib.IMAP4.abort, TimeoutError):
                self._reconnect()
            except imaplib.IMAP4.error as error:
                self._log_print(EMOJI[11] + self._msg['create_dst_folder_error']
                                .format(dst_mailbox))
                if self._debug:
                    self._log_print(LF + EMOJI[3] + self._msg['except_error'].format(error))
                break

        return False

    def _fetch_header(self, src_mailbox: str, message):
        """Fetch message header only.
        
            - src_mailbox: the source email mailbox;
            - message: the message uid of the source mailbox.
        """

        while True:
            try:
                if self._mail['src']['imap'].state != 'SELECTED':
                    self._mail['src']['imap'].select(src_mailbox)
                status, data = self._mail['src']['imap'].fetch(message, '(BODY.PEEK[HEADER])')
                break
            except (imaplib.IMAP4.abort, TimeoutError):
                self._reconnect()
            except imaplib.IMAP4.error as error:
                status, data = 'NO', error
                break
        if status != 'OK':
            self._log_print(EMOJI[11] + self._msg['header_src_error'])
            if self._debug:
                self._log_print(LF + EMOJI[3] + self._msg['except_error'].format(data))
            data = None
        else:
            data = message_from_bytes(data[0][1])
        return data

    def _message_exists(self, dst_mailbox: str, header):
        """Checks if the message already exists in the recipient.
        
            - dst_mailbox: the destination email mailbox;
            - header: the header of the source mailbox.
        """

        # Checks with the Message-ID if the message already exists.
        msg_id = re.search(r'[\r\n\s]*\<?([^\<\>]+)\>?',
                           header.get('Message-ID', ''), re.IGNORECASE)
        if msg_id:
            msg_id = msg_id.group(1)
            self._log_print(LF + EMOJI[7] + f'Message-ID: <{msg_id}>')
            while True:
                try:
                    if self._mail['dst']['imap'].state != 'SELECTED':
                        self._mail['dst']['imap'].select(dst_mailbox)
                    status, data = (self._mail['dst']['imap']
                                    .search(None, f'HEADER Message-ID "{msg_id}"'))
                    break
                except (imaplib.IMAP4.abort, TimeoutError):
                    self._reconnect()
                except imaplib.IMAP4.error:
                    status = 'NO'
                    break
            if status == 'OK' and data[0]:
                self._log_print(EMOJI[4] + self._msg['message_dst_exists'].format(dst_mailbox))
                return True
        else:
            # If the Message-ID does not exist, use the
            # search criteria with From, To and SentOn
            self._log_print(LF + EMOJI[1] + self._msg['messageid_not_found'])
            msg_from = parseaddr(header['From'])[1]
            msg_to = parseaddr(header['To'])[1]
            msg_senton = parsedate_to_datetime(header['Date']).strftime('%d-%b-%Y')
            search_criteria = f'FROM "{msg_from}" TO "{msg_to}" SENTON "{msg_senton}"'
            while True:
                try:
                    if self._mail['dst']['imap'].state != 'SELECTED':
                        self._mail['dst']['imap'].select(dst_mailbox)
                    status, data = self._mail['dst']['imap'].search(None, search_criteria)
                    break
                except (imaplib.IMAP4.abort, TimeoutError):
                    self._reconnect()
                except imaplib.IMAP4.error:
                    status = 'NO'
                    break
            if status == 'OK' and data[0]:
                self._log_print(EMOJI[4] + self._msg['message_dst_exists'].format(dst_mailbox))
                return True
        return False

    def _fetch_message(self, src_mailbox: str, message):
        """Fetch the entire source message.
        
            - src_mailbox: the source email mailbox;
            - message: the message uid of the source mailbox.
        """

        while True:
            try:
                self._log_print(EMOJI[6] + self._msg['fetch_src_folder'].format(src_mailbox))
                if self._mail['src']['imap'].state != 'SELECTED':
                    self._mail['src']['imap'].select(src_mailbox)
                status, data = self._mail['src']['imap'].fetch(message, '(BODY.PEEK[])')
                break
            except (imaplib.IMAP4.abort, TimeoutError):
                self._reconnect()
            except imaplib.IMAP4.error as error:
                status, data = 'NO', error
                break
        if status != 'OK':
            self._log_print(EMOJI[11] + self._msg['fetch_src_error'].format(src_mailbox))
            if self._debug:
                self._log_print(LF + EMOJI[3] + self._msg['except_error'].format(data))
            data = None
        else:
            data = data[0][1]
        return data

    def _append_message(self, dst_mailbox: str, received: str, message: str):
        """Append source message on destination server.
        
            - dst_mailbox: the destination email mailbox;
            - received: the date the message was received;
            - message: the message body.
        """

        while True:
            try:
                self._log_print(EMOJI[5] + self._msg['append_dst_message'].format(dst_mailbox))
                if self._mail['dst']['imap'].state != 'SELECTED':
                    self._mail['dst']['imap'].select(dst_mailbox)
                status, data = self._mail['dst']['imap'].append(dst_mailbox, None,
                                                                received, message)
                break
            except (imaplib.IMAP4.abort, TimeoutError):
                self._reconnect()
            except imaplib.IMAP4.error as error:
                status, data = 'NO', error
                break
        if status != 'OK':
            if any(b'[OVERQUOTA]' in msg for msg in data):
                status = 'OVERQUOTA'
            self._log_print(EMOJI[11] + self._msg['append_dst_message_error'].format(dst_mailbox))
            if self._debug:
                self._log_print(LF + EMOJI[3] + self._msg['except_error'].format(data))
        return status

    def _fetch_flags(self, src_mailbox: str, message):
        """Get the message flags from the source email.
        
            - src_mailbox: the source email mailbox;
            - message: the message uid of the source mailbox.
        """

        while True:
            try:
                if self._mail['src']['imap'].state != 'SELECTED':
                    self._mail['src']['imap'].select(src_mailbox)
                status, data = self._mail['src']['imap'].fetch(message, '(FLAGS)')
                break
            except (imaplib.IMAP4.abort, TimeoutError):
                self._reconnect()
            except imaplib.IMAP4.error as error:
                status, data = 'NO', error
                break
        if status != 'OK':
            self._log_print(EMOJI[11] + self._msg['flags_src_error'].format(src_mailbox))
            if self._debug:
                self._log_print(LF + EMOJI[3] + self._msg['except_error'].format(data))
            flags = None
        else:
            flags = re.findall(r'\\\w+', data[0].decode().upper())
            if '\\RECENT' in flags:
                flags.remove('\\RECENT')
        return flags

    def _store_flags(self, dst_mailbox: str, flags: str):
        """Stores the flags from the original message to the destination email message.
        
            - dst_mailbox: the destination email mailbox;
            - flags: the flags obtained from the source message.
        """

        while True:
            try:
                if self._mail['dst']['imap'].state != 'SELECTED':
                    self._mail['dst']['imap'].select(dst_mailbox)
                status, data = self._mail['dst']['imap'].search(None, 'ALL')
                if status == 'OK':
                    self._mail['dst']['imap'].store(data[0].split()[-1], '+FLAGS', flags)
                break
            except (imaplib.IMAP4.abort, TimeoutError):
                self._reconnect()
            except imaplib.IMAP4.error as error:
                status, data = 'NO', error
                break
        if status != 'OK':
            self._log_print(EMOJI[11] + self._msg['flags_add_dst_error'].format(dst_mailbox))
            if self._debug:
                self._log_print(LF + EMOJI[3] + self._msg['except_error'].format(data))

    def _migrate(self, src_cred: dict, dst_cred: dict):
        """Migrate all folders along with messages from source email to destination.

            - src_cred: the source email credential;
            - dst_cred: the destination email credential.
        """

        self._mail = {'src': {'cred': src_cred}, 'dst': {'cred': dst_cred}}
        self._log_print(LF + EMOJI[0] + self._msg['migrate_start'].format(
            self._mail['src']['cred']['email']))

        if not self._connect() or not self._get_mailboxes_info():
            return

        # Loop through all source mailboxes
        break_all_loop = False
        for src_mailbox in self._mail['src']['all_mailboxes']:
            if break_all_loop:
                break

            # Mailboxes that are not copied
            if re.search(r'\\[Noselect|All|Flagged]', src_mailbox):
                continue

            src_mailbox = src_mailbox.split(f'"{self._mail["src"]["separator"]}"')[-1].strip()
            if self._set_src_mailbox(src_mailbox):
                allmessages = self._get_allmessages(src_mailbox)
                if not allmessages:
                    continue
                self._mail['src']['all_messages'] = allmessages
                dst_mailbox = self._find_foldername(src_mailbox)
                if not self._set_dst_mailbox(dst_mailbox):
                    continue
            else:
                continue

            # Loop through all messages in the source mailbox
            for message in self._mail['src']['all_messages']:
                if break_all_loop:
                    break

                header = self._fetch_header(src_mailbox, message)
                if not header or self._message_exists(dst_mailbox, header):
                    continue

                body_message = self._fetch_message(src_mailbox, message)
                if body_message:
                    # Get the date the original message was received
                    try:
                        received = parsedate_to_datetime(header['Date'])
                        received = mktime(received.timetuple())
                        received = imaplib.Time2Internaldate(received)
                    except (TypeError, ValueError):
                        received = None

                    status = self._append_message(dst_mailbox, received, body_message)
                    if status == 'OK':
                        flags = self._fetch_flags(src_mailbox, message)
                        if flags:
                            flags = ' '.join(flags)
                            self._store_flags(dst_mailbox, flags)
                    elif status == 'OVERQUOTA':
                        break_all_loop = True

        if not break_all_loop:
            self._log_print(LF + EMOJI[0] + self._msg['migrate_finish']
                            .format(self._mail['src']['cred']['email']))

        self._disconnect()

    def load_credentials(self) -> list:
        """Load JSON credentials file."""

        try:
            with open('credentials.json', 'r', encoding = CODE) as file:
                credentials = json.load(file)
            return credentials
        except json.decoder.JSONDecodeError:
            print(EMOJI[11] + self._msg['cred_json_error'])
        except FileNotFoundError:
            print(EMOJI[11] + self._msg['cred_not_found'])
            print(EMOJI[1] + self._msg['cred_copy_file'])
        return None

    def generate_token(self, email: str):
        """Check OAUTH2 credential and create/refresh email token.

            - email: email address that needs OAuth2 authentication.
        """

        # If modifying these scopes, delete the files token_<email>.json.
        scopes = ['https://mail.google.com/']
        if not os.path.exists('oauth_client_secret.json'):
            self._log_print(LF + EMOJI[1] + self._msg['oauth_not_found'])
            self._log_print(EMOJI[1] + self._msg['oauth_required'])
            self._log_print('https://cloud.google.com/docs/authentication/client-libraries')
            sys.exit()
        creds = None
        token_filename = 'token_{}.json'.format(re.sub(r'[^\w._-]+', '_', email))
        if os.path.exists(token_filename):
            try:
                creds = Credentials.from_authorized_user_file(token_filename, scopes)
            except ValueError:
                os.remove(token_filename)
        # If there are no (valid) credentials available, let the user log in.
        while True:
            if creds and creds.valid:
                # Save the credentials for the next run
                with open(token_filename, 'w', encoding = CODE) as token:
                    token.write(creds.to_json())
                return creds.token, token_filename
            if not creds:
                self._log_print(LF + EMOJI[1] + self._msg['oauth_create_token'].format(email))
                flow = InstalledAppFlow.from_client_secrets_file('oauth_client_secret.json',
                                                                 scopes)
                prompt_msg = LF + self._msg['oauth_app_url'] + LF + '{url}'
                code_msg = LF + self._msg['oauth_code']
                try:
                    creds = flow.run_console(authorization_prompt_message = prompt_msg,
                                             authorization_code_message = code_msg)
                except InvalidGrantError:
                    self._log_print(LF + EMOJI[11] + self._msg['oauth_invalid_grant'])
                    continue
            if not creds.valid:
                try:
                    creds.refresh(Request())
                except TransportError:
                    self._log_print(LF + EMOJI[11] + self._msg['nodename_serv_error']
                                    .format(creds.token_uri))
                    self._log_print(LF + EMOJI[1] + self._msg['nodename_serv_verify'])
                    return None
                except RefreshError:
                    creds = None

    def start(self, credentials: list):
        """Start the migration process.

            - credentials: the complete list of credentials of the source and destination emails.
        """

        for creds in credentials:
            for cred in creds.items():
                if cred[1].get('security', '').upper() == 'OAUTH2':
                    self.generate_token(cred[1]['email'])

        # Check if there are arguments passed on the command line
        if self._parser_args:
            pargs = self._parser_args
            if pargs.gen_tokens:
                return

            if pargs.timeout and pargs.timeout.isdigit():
                timeout = int(pargs.timeout)
                if timeout > TIMEOUT_MAX:
                    self._timeout = TIMEOUT_MAX
                    print(self._msg['limit_reconn_timeout'].format(TIMEOUT_MAX))
                else:
                    self._timeout = timeout

            if pargs.attempts and pargs.attempts.isdigit():
                self._attempts = int(pargs.attempts)

            if pargs.debug:
                self._debug = True

        for credential in credentials:
            self._migrate(credential['src'], credential['dst'])

        self._log_print(LF + EMOJI[1] + self._msg['migrate_success'])
        if hasattr(self, '_log_filename'):
            self._log_print(LF + EMOJI[1] + self._msg['log_check'])
            self._log_print(self._msg['log_filename'].format(self._log_filename))

        self._log_print(LF + EMOJI[8] + self._msg['donate_dev'] + LF)
        self._log_print(EMOJI[2] + 'BTC: bc1qv4pcwyj388w2cztk4qcqa2yllrmhmvpa8nvl3y')
        self._log_print(EMOJI[2] + 'BCH: qqndwpqzlz7h909e4lzelpn53733q3y34ysqez3ems')
        self._log_print(EMOJI[2] + 'DOGE: DQYEEyAFrxn3iiJoL4Qphoqh1fb7822GwN')
        self._log_print(EMOJI[2] + 'DOT: 14SLApTGYovrW1HvdFER5heqF1RWQHYG1AVagKDdjwDzzcYv')
        self._log_print(EMOJI[2] + 'LTC: ltc1qr9fs9zz4wmqx5xhdm6l6andz8h9plk0wnj74nc')
        self._log_print(EMOJI[2] + 'ZEC: t1S2YxATvCYr5TrTykUXSZ9vC3SWRphTWrF')

if __name__ == '__main__':
    SyncImapEmail()

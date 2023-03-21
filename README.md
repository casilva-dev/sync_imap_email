![Sync Email Image](https://cdn-icons-png.flaticon.com/128/9197/9197904.png)
# SyncImapEmail

[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)

This project is a Python script that automates the email message migration process. It downloads all messages from each source email and sends them to the destination emails, making the task of migrating multiple email accounts significantly easier.

## How to use

Download SyncImapEmail from the Git repository, create the "credentials.json" file and add the email settings:

```json
[
    {
        "src": {
            "email": "email@domain1.com",
            "password": "password",
            "server": "imap.domain1.com",
            "port": 143,
            "security": "STARTTLS"
        },
        "dst": {
            "email": "email@domain2.com",
            "password": "password",
            "server": "mail.domain2.com",
            "port": 993,
            "security": "SSL/TLS"
        }
    },
    ...
]
```

The script can be used in two different ways:

1. **Docker**

    Start Docker, if it is not already running, and run the following command:

    ```bash
    docker build -t sync_imap_email .
    docker run -it --name my_container sync_imap_email
    ```

    Docker will start the container to run the script. After the migration is complete, the log file name will be displayed. Copy the container log file to your local computer.

    ```bash
    docker cp my_container:/log_20230319_190012.txt .
    ```

2. **Manual**

    To run the script manually in your computer's terminal, you need to install Python (version 3.6 or higher) and its dependencies.

    - ***Linux:***

        ```bash
        sudo apt-get install python3 python3-pip
        pip3 install google-auth google-auth-oauthlib==0.8.0
        ```

    - ***MacOS:***

        ```zsh
        brew install python3
        pip3 install google-auth google-auth-oauthlib==0.8.0
        ```

    - ***Windows:***

        To install Python on Windows, you need to download the installer from the [official website](https://www.python.org/downloads/). After installation, open Command Prompt and install dependencies.

        ```cmd
        pip install google-auth google-auth-oauthlib==0.8.0
        ```

    After installing the necessary packages, run the script:

    ```bash
    python3 sync_imap_email.py
    ```

    If an error occurs, make sure you are running the script with Python version 3.6 or higher:

    ```bash
    python3 --version
    python --version
    ```

## Contribution

We encourage everyone's contribution! Here are instructions to get started:

1. Fork the project.
2. Create your branch for the new feature (`git checkout -b new-feature`).
3. Commit your changes (`git commit -am 'Adding new functionality'`).
4. Push the branch (`git push origin new-feature`).
5. Create a new Pull Request for the main project.

Please check before submitting your pull request that the code follows the project's coding guidelines, including formatting standards and automated testing.

## License

This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).
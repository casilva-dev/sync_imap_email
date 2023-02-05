# Use the base image with Python 3.8 installed
FROM python:3.8

# Install dependency modules
RUN pip install chardet google-auth google-auth-oauthlib

# Copies files from the local SyncImapEmail folder to the container
COPY . /

# Run sync_imap_email.py with Python 3.8
CMD ["python3.8", "sync_imap_email.py"]
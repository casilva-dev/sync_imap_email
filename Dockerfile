# Use the base image with Python 3.8 installed
FROM python:3.8

# Install the module chardet
RUN pip install chardet

# Copy the sync_imap_email.py file from the local machine to the container
COPY sync_imap_email.py /

# Copy the credentials.json file from the local machine to the container
COPY credentials.json /

# Run script.py with Python 3.8
CMD ["python3.8", "sync_imap_email.py"]
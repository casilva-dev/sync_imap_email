# Use the base image with Python installed
FROM python:3

# Install dependency modules
RUN pip install google-auth google-auth-oauthlib==0.8.0

# Copy the sync_imap_email.py file from the local machine to the container
COPY sync_imap_email.py /

# Copy JSON files with credentials from local machine to container
COPY *.json /

# Run sync_imap_email.py
CMD ["python", "sync_imap_email.py"]
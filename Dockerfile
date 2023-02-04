# Use the base image with Python 3.8 installed
FROM python:3.8

# Install dependency modules
RUN pip install chardet google-auth google-auth-oauthlib

# Copy the sync_imap_email.py file from the local machine to the container
COPY sync_imap_email.py /

# Copy the credentials.json file from the local machine to the container
RUN if [ -f "credentials.json" ]; then \
    cp credentials.json /; \
fi

# Copy the oauth_client_secret.json file from the local machine to the container
RUN if [ -f "oauth_client_secret.json" ]; then \
    cp oauth_client_secret.json /; \
fi

# Run sync_imap_email.py with Python 3.8
CMD ["python3.8", "sync_imap_email.py"]
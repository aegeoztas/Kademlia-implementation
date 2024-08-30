# Python base image
FROM python:3.10-slim

# Set arguent

ARG PATH_TO_CONFIG_INI_FILE=./configuration/config.ini
ARG PATH_TO_PUBLIC_KEY_PEM_FILE


# Set the working directory
WORKDIR /DHT5

# Copy the DHT5 directory content inside the container
COPY ./dht /DHT5/dht
COPY ./configuration/ /DHT5/configuration
COPY ./requirements.txt /DHT5



COPY $PATH_TO_CONFIG_INI_FILE /DHT5/configuration/config.ini


RUN if [ -n "PATH_TO_CONFIG_INI_FILE" ]; then \
        echo "Path to config.ini file is given: $PATH_TO_CONFIG_INI_FILE. Initiate copy to the container"; \
        COPY PATH_TO_CONFIG_INI_FILE /DHT5/configuration/ \
    else \
        echo "No path for config.ini file given. Using default path."; \
        COPY ./configuration/config.ini /DHT5/configuration/config.ini \
    fi


# Define ARG and ENV
ARG PATH_TO_PUBLIC_KEY=""
ENV PUBLIC_KEY_PATH=$PATH_TO_PUBLIC_KEY


# Conditional key handling
RUN if [ -n "$PUBLIC_KEY_PATH" ]; then \
        echo "Path to public key is provided: $PUBLIC_KEY_PATH"; \
        cp "$PUBLIC_KEY_PATH" /DHT5/configuration/public_key; \
    else \
        echo "No path to public key provided. Generating new key pair."; \
        ssh-keygen -t rsa -b 4096 -f $KEY_DIR/id_rsa -N ""; \
        mv $KEY_DIR/id_rsa.pub $KEY_DIR/public_key; \
        rm $KEY_DIR/id_rsa; \
    fi




# Ensure the required Python packages are installed (if any)
RUN pip install --no-cache-dir -r requirements.txt




# Make the Python files executable
#RUN chmod +x script1.py script2.py
CMD python3

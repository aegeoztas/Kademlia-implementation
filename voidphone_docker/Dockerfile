# Set the base image
FROM python:3.10-slim

# Install necessary tools
RUN apt-get update && apt-get install -y openssl

# Set working directory
WORKDIR /DHT5

# Arguments to control the build process

ARG PATH_TO_PUT_CONFIG_INI_FILE=./configuration/config_5.ini
ARG PATH_TO_GET_CONFIG_INI_FILE=./configuration/config_1.ini

# Copy the public key if the argument is true, otherwise generate a new key

# Copy configuration files
COPY $PATH_TO_PUT_CONFIG_INI_FILE /DHT5/configuration/config_5.ini
COPY $PATH_TO_GET_CONFIG_INI_FILE /DHT5/configuration/config_1.ini


COPY requirements.txt /DHT5/
COPY ./voidphone_docker/client.py /DHT5/

# Install required Python packages
RUN pip install --no-cache-dir -r /DHT5/requirements.txt

# Default command to run the client script
CMD ["python3", "/DHT5/client.py"]
# Set the base image
FROM python:3.10-slim

# Install necessary tools
RUN apt-get update && apt-get install -y openssl

# Set working directory
WORKDIR /DHT5

# Arguments to control the build process

ARG PATH_TO_DHT1_CONFIG_INI_FILE=./configuration/config_1.ini
ARG PATH_TO_DHT2_CONFIG_INI_FILE=./configuration/config_2.ini
ARG PATH_TO_DHT3_CONFIG_INI_FILE=./configuration/config_3.ini
ARG PATH_TO_DHT4_CONFIG_INI_FILE=./configuration/config_4.ini
ARG PATH_TO_DHT5_CONFIG_INI_FILE=./configuration/config_5.ini

# Copy the public key if the argument is true, otherwise generate a new key

# Copy configuration files
COPY $PATH_TO_DHT1_CONFIG_INI_FILE /DHT5/configuration/config_1.ini
COPY $PATH_TO_DHT2_CONFIG_INI_FILE /DHT5/configuration/config_2.ini
COPY $PATH_TO_DHT3_CONFIG_INI_FILE /DHT5/configuration/config_3.ini
COPY $PATH_TO_DHT4_CONFIG_INI_FILE /DHT5/configuration/config_4.ini
COPY $PATH_TO_DHT5_CONFIG_INI_FILE /DHT5/configuration/config_5.ini



COPY requirements.txt /DHT5/
COPY ./voidphone_docker/client.py /DHT5/

# Install required Python packages
RUN pip install --no-cache-dir -r /DHT5/requirements.txt

# Default command to run the client script
CMD ["python3", "/DHT5/client.py"]
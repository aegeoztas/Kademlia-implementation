
# Parameters to set if a public key will be provided to the dockerfile.
# If no public key is provided, a random public key is generated.
# Usage if user wants to use its own public key:

# docker build -t dht5 --build-arg USE_OWN_KEY=true --build-arg PATH_TO_KEY=./configuration/public_key.pem .

# Usage if user wants to use a random public key:

# docker build -t dht5 --build-arg USE_OWN_KEY=true --build-arg PATH_TO_KEY=./configuration/public_key.pem .

ARG USE_OWN_KEY=false
ARG PATH_TO_KEY

FROM python:3.10-slim AS build_with_own_key_true
ONBUILD WORKDIR /DHT5
ONBUILD COPY PATH_TO_PUBLIC_KEY /DHT5/configuration/public_key.pem

FROM python:3.10-slim AS build_with_own_key_false
RUN echo "No public key provided, a public key will be generated"
ONBUILD WORKDIR /DHT5

FROM build_with_own_key_${USE_OWN_KEY}

# A path to a config.ini file can be passed as parameters. If the parameter is not set, the default path will be used.
# Usage:
# docker build -t dht5 (... other parameters...) --build-arg PATH_TO_CONFIG_INI_FILE=/specified/path/config.ini
ARG PATH_TO_CONFIG_INI_FILE=./configuration/config.ini
COPY $PATH_TO_CONFIG_INI_FILE /DHT5/configuration/config.ini

# We install openssl in order to be able to generate key
RUN apt-get update && apt-get install -y openssl

# If the key was not provided, a key is generated.
RUN if [ ! -f /DHT5/configuration/public_key.pem ];  then \
        echo "Key file not found. Generating a new key." && \
        openssl genpkey -algorithm RSA -out /DHT5/configuration/private_key.pem && \
        openssl rsa -pubout -in /DHT5/configuration/private_key.pem -out /DHT5/configuration/public_key.pem; \
    else \
        echo "Key file already exists."; \
    fi


# Copy of the required elements inside the container
COPY ./dht /DHT5/dht
COPY ./configuration/ /DHT5/configuration
COPY ./requirements.txt /DHT5

# Ensure the required Python packages are installed (if any)
RUN pip install --no-cache-dir -r requirements.txt

# Expose the ports of the two listening processes. Need to be set accordingly with the config.ini file
# API process
EXPOSE 8889
# DHT Kademlia process
EXPOSE 8890


# Make the Python files executable
#RUN chmod +x script1.py script2.py
CMD ["python3", "dht/servers.py"]

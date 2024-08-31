#docker build --no-cache -t dht .


#docker build --no-cache -t dht --build-arg PATH_TO_PUBLIC_KEY_PEM_FILE=./configuration/public_key.pem .

docker build --no-cache -t dht2 --build-arg PATH_TO_CONFIG_INI_FILE=./configuration/config.ini .

#docker build --no-cache -t dht2 --build-arg PATH_TO_CONFIG_INI_FILE=./configuration/config2.ini .


docker run -it --network host dht2


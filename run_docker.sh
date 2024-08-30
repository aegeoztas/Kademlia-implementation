#docker build --no-cache -t dht .
docker build --no-cache -t dht --build-arg PATH_TO_PUBLIC_KEY_PEM_FILE=./configuration/public_key.pem .

docker run -it --network host dht


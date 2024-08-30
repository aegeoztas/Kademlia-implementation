#docker build --no-cache -t dht .
docker build --no-cache -t dht --build-arg PATH_TO_PUBLIC_KEY_PEM_FILE=./configuration/public_key.pem .

docker run -it -p 8889:8889 -p 8890:8890 dht


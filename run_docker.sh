#docker build --no-cache -t dht .

# run_client_docker.sh

docker build --no-cache -t dht2 --build-arg PATH_TO_CONFIG_INI_FILE=./configuration/config.ini .

docker run -d -it -p 8889:8889 -p 8890:8890  dht2


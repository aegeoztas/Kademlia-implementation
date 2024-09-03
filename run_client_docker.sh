#docker build --no-cache -t dht .

# run_client_docker.sh

docker build --no-cache -t dht_client -f voidphone_docker/Dockerfile .

docker run -d -it --network host -p 8850:8850 dht_client

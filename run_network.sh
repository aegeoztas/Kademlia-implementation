#!/bin/bash

for i in {1..5}
do
    docker build --no-cache -t dht$i --build-arg PATH_TO_CONFIG_INI_FILE=./config_${i}.ini .
    docker run -d -it --name dht_node_$i dht$i
done

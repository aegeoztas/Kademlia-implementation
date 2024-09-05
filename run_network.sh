#!/bin/bash
# run_network.sh
declare -a api_ports=("8881" "8882" "8883" "8884" "8885")
declare -a p2p_ports=("8891" "8892" "8893" "8894" "8895")


for i in {1..5}
do
    docker build --no-cache -t dht$i --build-arg PATH_TO_CONFIG_INI_FILE=./configuration/config_${i}.ini .
    docker run -d -it --network host -p ${api_ports[$i-1]}:${api_ports[$i-1]} -p ${p2p_ports[$i-1]}:${p2p_ports[$i-1]} --name dht_node_$i dht$i
done

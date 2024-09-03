import subprocess

from generate_config_file import generate_config_file

"""
the objective of this python file is to launch a network of kademlia peers all connected to another for testing.

"""

def generate_network_config(ip_1="176.17.0.2",
                            ip_2="176.17.0.3",
                            ip_3="176.17.0.4",
                            ip_4="176.17.0.5",
                            ip_5="176.17.0.6"):


    """
    ip_1="127.0.0.2",
    ip_2="127.0.0.3",
    ip_3="127.0.0.4",
    ip_4="127.0.0.5",
    ip_5="127.0.0.6
    declare -a api_ports=("8881" "8882" "8883" "8884" "8885")
declare -a p2p_ports=("8891" "8892" "8893" "8894" "8895")
    """
    ip = "127.0.0.1"

    api_addresses = [ip+":8881", ip+":8882", ip+":8883", ip+":8884", ip+":8885"]
    p2p_addresses = [ip+":8891", ip+":8892", ip+":8893", ip+":8894", ip+":8895"]

    for i in range(5):
        known_peer_index = (i - 1) % 5  # Point to the previous node as a known peer (in a circular fashion)
        generate_config_file(api_addresses[i], p2p_addresses[i], p2p_addresses[known_peer_index], f'configuration\config_{i + 1}.ini')


if __name__ == "__main__":
    generate_network_config()

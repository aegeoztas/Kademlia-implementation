import subprocess

from generate_config_file import generate_config_file

"""
the objective of this python file is to launch a network of kademlia peers all connected to another for testing.

"""

def generate_network_config(ip_1="172.17.0.2",
                            ip_2="172.17.0.3",
                            ip_3="172.17.0.4",
                            ip_4="172.17.0.5",
                            ip_5="172.17.0.6"):

    api_addresses = [ip_1+":8889", ip_2+":8889", ip_3+":8889", ip_4+":8889", ip_5+":8889"]
    p2p_addresses = [ip_1+":8890", ip_2+":8890", ip_3+":8890", ip_4+":8890", ip_5+":8890"]

    for i in range(5):
        known_peer_index = (i + 1) % 5  # Point to the next node as a known peer (in a circular fashion)
        generate_config_file(api_addresses[i], p2p_addresses[i], p2p_addresses[known_peer_index], f'config_{i + 1}.ini')


if __name__ == "__main__":
    generate_network_config()

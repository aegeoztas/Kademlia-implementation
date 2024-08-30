import argparse
def generate_config_file(api_address, p2p_address, known_peer_address, filename):
    # Content to be written in the config file
    config_content = f"""[DEFAULT]
hostkey = ./configuration/public_key.pem

[dht]
K = 20
ALPHA = 20
MIN_TTL = 10
MAX_TTL = 3600
TIME_OUT = 5
api_address = {api_address}
p2p_address = {p2p_address}
known_peer_address = {known_peer_address}
"""

    # Writing the content to the specified file
    with open(filename, 'w') as file:
        file.write(config_content)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-api", "--api_address",type =str, required = True)
    parser.add_argument("-p2p", "--p2p_address",type =str, required = True)
    parser.add_argument("-k", "--known_peer_address",type =str, required = True)
    parser.add_argument("-f", "--filename",type =str, required = True)
    args = parser.parse_args()
    generate_config_file(args.api_address, args.p2p_address, args.known_peer_address, args.filename)

# messages.py 
# This class serves as the definition for the messages numbers. 

# Gossip
GOSSIP_ANNOUNCE = 500
GOSSIP_NOTIFY = 501
GOSSIP_NOTIFICATION = 502
GOSSIP_VALIDATION = 503
# reserved until 519 for gossip 

# NSE
NSE_QUERY = 520 
NSE_ESTIMATE = 521
# reserved until 539 for NSE

# RPS
RPS_QUERY = 540 
RPS_PEER = 541
# reserved until 559 for RPS

# Onion
ONION_TUNNEL_BUILD = 560
ONION_TUNNEL_READY = 561
ONION_TUNNEL_INCOMING = 562
ONION_TUNNEL_DESTROY = 563
ONION_TUNNEL_DATA = 564
ONION_ERROR = 565
ONION_COVER = 566
# reserved until 599 for Onion

# Onion Auth 
AUTH_SESSION_START = 600
AUTH_SESSION_HS1 = 601
AUTH_SESSION_INCOMING_HS1 = 602
AUTH_SESSION_HS2 = 603
AUTH_SESSION_INCOMING_HS2 = 604
AUTH_LAYER_ENCRYPT = 605
AUTH_LAYER_DECRYPT = 606
AUTH_LAYER_ENCRYPT_RESP = 607
AUTH_LAYER_DECRYPT_RESP = 608
AUTH_SESSION_CLOSE = 609 
AUTH_ERROR = 610 
AUTH_CIPHER_ENCRYPT = 611
AUTH_CIPHER_ENCRYPT_RESP = 612
AUTH_CIPHER_DECRYPT = 613
AUTH_CIPHER_DECRYPT_RESP = 614
# reserved until 649  for Onion Auth 

# DHT
DHT_PUT = 650 
DHT_GET = 651
DHT_SUCCESS = 652
DHT_FAILURE = 653
# reserved until 679 for DHT 

ENROLL_INIT = 680
ENROLL_REGISTER = 681
ENROLL_SUCCESS = 682
ENROLL_FAILURE = 683
# reserved until 689 for ENROLL 

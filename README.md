# P2PSecDHT

##  Docker file 

to prepare the docker image for a local node it is    


## launcing a peer network
to launch a peer network of 5 kademlia peers ready for connection you can run
> python prepare_network.py

> run_network.sh

this will prepare 5 differnet config files and run 5 different dht-5 implementation instances using ip addressses 127.0.0.2-6
After this running the bash script run_network.sh will build and run 5 different peers for furthrer testing. 
## Timeline 
1. <del>Registration: 30. April 23:59 CEST</del>
2. <del>Initial Report: 21. May 23:59 CEST</del>
3. Midterm Report: 02. July 23:59 CEST
4. Written exam: not fixed yet
5. Project Deadline: 02. September 23:59 CEST

## Tasks 
- write final report / documentation
- write tests showing functionality of the implementation
- make a working Dockerfile with exposed API and peer to peer connection
- we are not using encryption for the messages
- ⁠the data is not stored encrypted in the local storage and anyone could could get the plaintext of the data
- ⁠no authenticity since we are not verifying public key
- 
***

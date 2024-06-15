import time

# Time to live default value : TODO import the constant from configuration file
TTL = 40


class LocalHashTable:
    """
    A Local_hash_table represent the local storage of a peer. It is a hash table, and the values have time to live.
    The keys of the values are in the same key space as the node IDs.
    """

    def __init__(self):
        self.hash_table = {}
        self.ttl = TTL

    def put(self, key, value, ttl=None):
        """
        The put function is used to add a value to the local hash table.
        The ttl value is optional. If it is not specified, the ttl value
        will be taken from the file configuration.
        :param key: the key used to retrieve the data value
        :param value: the value to be stored
        :param ttl: the time in second for a value to be kept in the hash table
        :return: void
        """

        # Definition of the expiration time of the key-value pair
        if not ttl:
            expiration_time = time.time() + self.ttl
        else:
            expiration_time = time.time() + ttl

        # Insertion of the value and logging
        self.hash_table[key] = (value, expiration_time)
        print(f"[+] Local hash table: A value has been inserted or updated in the local hash table. \
        Key={key}, value={value} , ttl={ttl}")

    def get(self, key):
        """
        The function get will return the value associated with the key in the local hash table, if it exists
         and if the time to live has not expired.
        :param key: the key used to retrieve the data value
        :return: void
        """
        value, expiration_time = self.hash_table.get(key, (None, None))
        if not value or not expiration_time:
            return None
        else:
            if expiration_time < time.time():
                self.hash_table.pop(key)
                return None
            else:
                return value

    def remove_expired_values(self):
        """
        This function deletes all values with an expired expiry time.
        :return: void
        """
        filtered_hash_table = {key: (value, expiration_time) for key, (value, expiration_time)
                               in self.hash_table.items() if expiration_time > time.time()}

        self.hash_table = filtered_hash_table

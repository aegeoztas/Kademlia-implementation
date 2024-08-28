import time

from dht.local_hash_table import LocalHashTable

class TestLocalHashTable:
    def test_init(self):
        empty: LocalHashTable = LocalHashTable()
        assert(len(empty.hash_table) == 0)

    def test_put_and_retrieve(self):
        table: LocalHashTable = LocalHashTable()
        key = 1
        value = 2
        ttl = 10 # seconds
        table.put(key, value, ttl)
        assert(table.get(key) == value)

    def test_put_and_retrieve_failed_due_to_time(self):
        table: LocalHashTable = LocalHashTable()
        key = 1
        value = 2
        ttl = 1  # seconds
        table.put(key, value, ttl)
        time.sleep(ttl + 2)
        assert (not table.get(key))
        assert (len(table.hash_table) == 0)

    def test_absent_value(self):
        table: LocalHashTable = LocalHashTable()
        key = 1
        value = 2
        ttl = 10  # seconds
        table.put(key, value, ttl)
        assert (not table.get(3))
        assert (len(table.hash_table) == 1)

    def test_filtered(self):
        table: LocalHashTable = LocalHashTable()
        table.put(50, 50, 50)
        for i in range(10):
            table.put(i*2, i, 2)

        assert(len(table.hash_table)==11)
        time.sleep(3)
        table.remove_expired_values()
        assert(len(table.hash_table)==1)
        assert(table.get(50) == 50)


"""
Simple hash table implementation using open addressing with linear probing.
Stores employee records (dicts). For simplicity we store whole record in slot.
"""

from typing import List, Optional

class HashTable:
    def __init__(self, size: int = 20):
        self.size = size
        self.table: List[Optional[dict]] = [None] * size

    def hash_function(self, emp_id: int) -> int:
        return emp_id % self.size

    def insert(self, record: dict) -> int:
        """
        Inserts or replaces a record with same id.
        Returns final index used.
        """
        emp_id = int(record["id"])
        idx = self.hash_function(emp_id)

        for i in range(self.size):
            pos = (idx + i) % self.size
            slot = self.table[pos]
            if slot is None:
                # empty slot - place record
                self.table[pos] = record.copy()
                return pos
            else:
                # if same id, replace
                if int(slot.get("id")) == emp_id:
                    self.table[pos] = record.copy()
                    return pos
                # else continue probing
                continue
        # table full, raise or overwrite the original idx (we'll overwrite first slot)
        self.table[idx] = record.copy()
        return idx

    def get(self, emp_id: int):
        """Return record and steps trace if found else (None, trace)"""
        idx = self.hash_function(emp_id)
        trace = []
        for i in range(self.size):
            pos = (idx + i) % self.size
            trace.append({"index": pos, "slot": self.table[pos]})
            slot = self.table[pos]
            if slot is None:
                # empty slot - stop searching
                return None, trace
            if int(slot.get("id")) == emp_id:
                return slot, trace
        return None, trace

    def as_list(self):
        """Return serializable list representation of table (indexes)"""
        out = []
        for i, slot in enumerate(self.table):
            if slot is None:
                out.append(None)
            else:
                out.append({"index": i, "id": slot.get("id"), "name": slot.get("name"), "attendance_percentage": slot.get("attendance_percentage")})
        return out

    def flatten(self):
        """Return list of stored records (preserves order in table)"""
        return [slot for slot in self.table if slot is not None]

    def clear(self):
        self.table = [None] * self.size


def rebuild_hashtable_from_list(hash_table: HashTable, records: List[dict]):
    """
    Insert a list of records into the given hash_table (clears first).
    """
    hash_table.clear()
    for r in records:
        hash_table.insert(r)

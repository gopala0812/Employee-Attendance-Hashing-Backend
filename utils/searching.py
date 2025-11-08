"""
Searching utilities.
- search_by_id uses hash table's get method and returns (record, trace)
- search_by_name performs case-insensitive substring match over flattened records
"""

from typing import Tuple, List, Optional

def search_by_id(hash_table, emp_id: int) -> Tuple[Optional[dict], List[dict]]:
    record, trace = hash_table.get(emp_id)
    return record, trace

def search_by_name(hash_table, name: str) -> Tuple[List[dict], List[dict]]:
    """
    Linear search by name (case-insensitive).
    Returns (list_of_matches, steps_trace)
    steps_trace includes which records were checked (id and name)
    """
    name_lower = name.strip().lower()
    checked = []
    matches = []
    for slot in hash_table.flatten():
        checked.append({"id": slot.get("id"), "name": slot.get("name")})
        if name_lower in str(slot.get("name", "")).lower():
            matches.append(slot)
    return matches, checked

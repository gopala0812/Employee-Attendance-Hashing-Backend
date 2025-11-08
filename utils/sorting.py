"""
Sorting utilities.
"""

def sort_employees_by_percentage(records: list, order: str = "asc") -> list:
    """
    Sort by 'attendance_percentage'. order : 'asc' or 'desc'
    Returns a new sorted list.
    """
    reverse = (order == "desc")
    return sorted(records, key=lambda x: x.get("attendance_percentage", 0), reverse=reverse)

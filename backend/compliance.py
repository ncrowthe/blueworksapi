"""
Compliance checking helpers for Blueworks Live process nodes.

Ported verbatim from bwl_search.py (lines 64–136).  All Tkinter / UI
references have been removed.  These functions are pure Python — no HTTP calls.
"""


def check_node_compliance(node: dict, required_fields: list) -> bool:
    """Check that all required metadata fields exist and are non-empty on the node."""
    if not isinstance(node, dict):
        return False
    for field in required_fields:
        # Check exact field name, lowercase-first camelCase, and all lowercase
        val = (
            node.get(field)
            if node.get(field) is not None
            else (
                node.get(field[:1].lower() + field[1:])
                if node.get(field[:1].lower() + field[1:]) is not None
                else node.get(field.lower())
            )
        )
        if not val:
            return False
    return True


def has_mandatory_metadata(process: dict, required_fields: list) -> bool:
    """
    Return True if the process carries all of the given required_fields.

    Traverses the process hierarchy to find the root activity node:
    1. Via items mapping: items[processId]["rootActivityID"] -> items[rootId]
    2. Direct nesting: process[processId]["rootActivityID"]
    3. Direct process dictionary
    """
    if not isinstance(process, dict):
        return False

    if not required_fields:
        return True

    process_id = process.get("processId") or process.get("id")
    items = process.get("items")
    target_node = None

    # 1. Look up via items dictionary (standard BWL process JSON)
    if isinstance(items, dict):
        proc_node = items.get(process_id, {}) if process_id else {}
        root_id = proc_node.get("rootActivityID")

        # Fallback: find rootActivityID across items if processId didn't match directly
        if not root_id:
            for item in items.values():
                if isinstance(item, dict) and "rootActivityID" in item:
                    root_id = item.get("rootActivityID")
                    break

        if root_id and isinstance(items.get(root_id), dict):
            target_node = items[root_id]

    # 2. Look up via nested processId -> rootActivityID dict
    if target_node is None and process_id and isinstance(process.get(process_id), dict):
        proc_node = process[process_id]
        root_node = proc_node.get("rootActivityID")
        if isinstance(root_node, dict):
            target_node = root_node
        else:
            target_node = proc_node

    # 3. Look up rootActivityID directly on the process dict
    if target_node is None and isinstance(process.get("rootActivityID"), dict):
        target_node = process["rootActivityID"]

    # 4. Fallback to process dictionary itself
    if target_node is None:
        target_node = process

    return check_node_compliance(target_node, required_fields)

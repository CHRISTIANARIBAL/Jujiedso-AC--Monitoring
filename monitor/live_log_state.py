
import threading

_lock = threading.Lock()
_active_lookups = {}


def update_active_lookup(ac_id, lookup):
    """Store the latest active-session lookup for one AC."""
    with _lock:
        _active_lookups[ac_id] = dict(lookup)


def get_active_lookup(ac_id):
    """Return a snapshot of the latest lookup for one AC."""
    with _lock:
        return dict(_active_lookups.get(ac_id, {}))


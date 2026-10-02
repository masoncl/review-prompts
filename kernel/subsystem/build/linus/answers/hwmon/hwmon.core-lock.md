- `pec_store()`: holds the lock around
  `->write(hdev, hwmon_chip, hwmon_chip_pec, 0, val)` and around the update of
  `client->flags`.
- `pec_show()`: takes no lock and calls no driver code.
- Every call the core makes to `->read`, `->read_string` or `->write` is under
  the lock; `is_visible` is the only `struct hwmon_ops` member the core calls
  without it.
- `hwmon_notify_event()`: does not take the core lock in its own body, but
  see "Nesting the core lock" for `hwmon_temp`.

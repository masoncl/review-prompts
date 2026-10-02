- `raw_request`: mandatory and the only callback tested at registration;
  `hid_add_device()` logs "transport driver missing .raw_request()" and
  returns `-EINVAL` before it calls `parse`.
- `__hid_hw_raw_request()`: has no NULL test of its own and never returns an
  errno for a missing callback; it relies on the `hid_add_device()` test.
- `start`: called only from `hid_hw_start()`, not from `hid_connect()`.
- `request` missing: `hid_hw_request()` calls `__hid_request()` in
  `drivers/hid/hid-core.c`, which builds the buffer and uses `raw_request`.
  There is no __hid_hw_request() in this tree.
- `idle` missing: `hid_hw_idle()` returns 0.
- `may_wakeup` missing: `hid_hw_may_wakeup()` returns `device_may_wakeup()` of
  `hdev->dev.parent`, or `false` when there is no parent.
- `struct hid_ll_driver` has no member named sched_inputs.
- `Documentation/hid/hid-transport.rst`: calls only `raw_request` mandatory
  and only `request` optional; it gives no status for `start`, `stop`,
  `open`, `close` or `parse`, which the core calls unchecked.

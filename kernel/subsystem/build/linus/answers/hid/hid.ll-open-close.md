- `Documentation/hid/hid-transport.rst` says "->open() calls are nested for
  each client that opens the HID device"; `hid_hw_open()` never nests them,
  so a transport sees one `open` and one `close` and needs no counter.
- `hdev->ll_open_count` is an `unsigned int` and `hid_hw_close()` decrements
  it with no test for zero; a close without a successful `hid_hw_open()`
  wraps the count, and the next `hid_hw_open()` does not call `open`.
- `hid_hw_open()` can fail before it counts: `mutex_lock_killable()` returns
  an error with `ll_open_count` unchanged, so that caller must not call
  `hid_hw_close()`.

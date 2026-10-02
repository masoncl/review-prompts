- Count bound: needed although `struct_size()` saturates, because
  `expected_len` is a `u16` and would truncate; see `load_link_keys()` in
  `net/bluetooth/mgmt.c`.
- `u8` counts: `add_adv_patterns_monitor()` has no count bound, computes
  the size in a `size_t`, and requires `len > sizeof(*cp)`, so a count of
  zero is rejected.
- Per-element validation is not all-or-nothing in most handlers.
  - `load_irks()`: checks every element first and rejects the whole command.
  - `load_link_keys()` and `load_long_term_keys()`: clear the old keys, then
    skip a bad element with `continue`, and still reply success.
  - `load_conn_param()` and `load_conn_subrate()`: skip a bad element with
    `continue`, and still reply success.
- `load_conn_subrate()`: one more handler with the bound and the exact
  `struct_size()` comparison.

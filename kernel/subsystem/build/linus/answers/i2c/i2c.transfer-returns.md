- `__i2c_transfer()`: returns the callback's value unchanged, so a callback
  that returns 0 or a positive count below `num` hands exactly that to the
  caller of `i2c_transfer()`; the core neither converts it to an errno nor
  rounds it up.
- `i2c_transfer_buffer_flags()`: passes any value other than 1 through, so
  `i2c_master_send()` and `i2c_master_recv()` can return 0.
- SMBus block helpers that take a length: can also fail with `-EINVAL` from
  the core before the adapter is called; see "SMBus block transfers".
- The rest is as models expect; see `i2c_transfer_buffer_flags()` in
  `drivers/i2c/i2c-core-base.c` and the helpers in
  `drivers/i2c/i2c-core-smbus.c`.

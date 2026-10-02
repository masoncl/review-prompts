- `__i2c_smbus_xfer()` starts with `__i2c_check_suspended()`: `-ESHUTDOWN`,
  neither the callback nor the emulation runs.
- Callback choice in atomic mode (`i2c_in_atomic_xfer_mode()`):
  - `smbus_xfer_atomic` set: it is called.
  - `smbus_xfer_atomic` NULL, `master_xfer_atomic` set: the native callback is
    skipped and the transaction is emulated, even if `smbus_xfer` is set.
  - both NULL: the non-atomic `smbus_xfer` is called if set, as outside
    atomic mode.
- Fallback to `i2c_smbus_xfer_emulated()`: only when the native callback
  returned `-EOPNOTSUPP` and `master_xfer` is non-NULL; with `master_xfer`
  NULL the `-EOPNOTSUPP` is returned.
- The fallback test runs after the retry loop; a native `-EAGAIN` that
  outlasts the retries is returned, not emulated.
- `I2C_FUNC_SMBUS_PEC`: the core never tests it. With `I2C_CLIENT_PEC` set the
  emulation adds and checks PEC whatever the adapter advertises, except for
  `I2C_SMBUS_QUICK` and `I2C_SMBUS_I2C_BLOCK_DATA`, and the native callback
  just receives the flag.
- Emulated block read with PEC: the read message reaches the adapter with
  `len` 2 and `I2C_CLIENT_PEC` still set in its `flags`.
- `i2c_smbus_check_pec()` takes the byte at the final `msg->len - 1` as the
  PEC, so the adapter must leave `msg->len` at count byte + data + PEC;
  for example `aspeed_i2c_master_irq()` in `drivers/i2c/busses/i2c-aspeed.c`
  tests `I2C_CLIENT_PEC` to do so.

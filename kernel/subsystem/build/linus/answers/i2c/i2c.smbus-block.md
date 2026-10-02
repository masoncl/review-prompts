- `__i2c_smbus_xfer()` checks the caller's length itself: `data->block[0]` of
  0 or above `I2C_SMBUS_BLOCK_MAX` returns `-EINVAL`.
- The check covers `I2C_SMBUS_I2C_BLOCK_DATA` in both directions,
  `I2C_SMBUS_BLOCK_PROC_CALL`, and `I2C_SMBUS_BLOCK_DATA` writes; an
  `I2C_SMBUS_BLOCK_DATA` read is exempt because `block[0]` is output there.
- The check runs after `__i2c_check_suspended()` and before the tracepoints,
  the native callback and the emulation, so the adapter never sees such a
  length on either path.
- It also covers callers that skip the helpers: `i2c_smbus_xfer()`, the
  `I2C_SMBUS` ioctl in `drivers/i2c/i2c-dev.c`, and direct callers of
  `__i2c_smbus_xfer()`.

| Helper | Length above 32 | Length 0 |
|---|---|---|
| `i2c_smbus_write_block_data()` | clamped to 32, returns 0 on success | `-EINVAL` |
| `i2c_smbus_read_i2c_block_data()` | clamped to 32 | `-EINVAL` |
| `i2c_smbus_write_i2c_block_data()` | clamped to 32, returns 0 on success | `-EINVAL` |

- The helpers do not test for 0 themselves; the `-EINVAL` in the table comes
  from `__i2c_smbus_xfer()`.
- `i2c_smbus_xfer_emulated()`: static, one caller, `__i2c_smbus_xfer()`; the
  lengths its own "Invalid block ... size" tests reject have already been
  rejected, so those tests are not what a caller hits.
- Device-announced length, emulated path: after the transfer the core tests
  only `msg[1].buf[0] > I2C_SMBUS_BLOCK_MAX` (`-EPROTO`).
- An announced count of 0 passes the core, and
  `i2c_smbus_read_block_data()` then returns 0, unless the adapter's transfer
  callback rejected it; for example `readbytes()` in
  `drivers/i2c/algos/i2c-algo-bit.c` returns `-EPROTO` for 0.

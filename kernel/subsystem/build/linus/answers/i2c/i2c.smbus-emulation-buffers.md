- `msgbuf0` and `msgbuf1` in `i2c_smbus_xfer_emulated()`: on-stack arrays, of
  `I2C_SMBUS_BLOCK_MAX+3` and `I2C_SMBUS_BLOCK_MAX+2` bytes; every message
  starts out pointing at them, unflagged.
- Heap buffer with `I2C_M_DMA_SAFE`, from `i2c_smbus_try_get_dmabuf()`:

| Transaction | Message re-pointed |
|---|---|
| `I2C_SMBUS_BLOCK_DATA` read | `msg[1]` |
| `I2C_SMBUS_BLOCK_DATA` write | `msg[0]` |
| `I2C_SMBUS_BLOCK_PROC_CALL` | `msg[0]` and `msg[1]` |
| `I2C_SMBUS_I2C_BLOCK_DATA` read | `msg[1]` |
| `I2C_SMBUS_I2C_BLOCK_DATA` write | `msg[0]` |

- `msg[0]` of a block read: the command byte stays in `msgbuf0` on the stack,
  unflagged.
- Allocation failure in `i2c_smbus_try_get_dmabuf()`: no error is returned;
  the message keeps its stack array without the flag and `__i2c_transfer()`
  runs as usual.

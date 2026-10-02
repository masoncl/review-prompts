- `i2c_check_for_quirks()`: one caller, `__i2c_transfer()`. The atomic
  callback is chosen after the check, so atomic transfers are checked too.
- `I2C_AQ_NO_CLK_STRETCH` and `I2C_AQ_NO_REP_START`: `i2c_check_for_quirks()`
  tests neither, and no code in this tree reads either flag; adapter drivers
  only set them.
- `max_comb_1st_msg_len`, `max_comb_2nd_msg_len`, `I2C_AQ_COMB_WRITE_FIRST`,
  `I2C_AQ_COMB_READ_SECOND`, `I2C_AQ_COMB_SAME_ADDR`: tested only when
  `I2C_AQ_COMB` is set and `num == 2`.
- In that same case `max_read_len` and `max_write_len` are not tested.
- `I2C_AQ_COMB` with `num` above 2: fails as "too many messages", whatever
  `max_num_msgs` says.
- `I2C_M_RECV_LEN` message: only the `len` the caller passed is compared with
  `max_read_len`; the bytes the device adds are not.
- Mux and ATR children: `i2c_mux_add_adapter()` and `i2c_atr_add_adapter()`
  copy the parent's `quirks` pointer, so a transfer on a child is checked on
  the child and again on the parent.

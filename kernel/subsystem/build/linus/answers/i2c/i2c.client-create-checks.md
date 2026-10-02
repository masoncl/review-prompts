- `i2c_check_addr_validity()` is the only address validity test: 7-bit 0x00 or
  above 0x7f, and 10-bit above 0x3ff, give -EINVAL.
- Reserved 7-bit addresses (0x01-0x07, 0x78-0x7f) are accepted without a
  warning; `i2c_new_client_device()` does not call
  `i2c_check_7bit_addr_validity_strict()`.
- `I2C_CLIENT_TEN` on an adapter without `I2C_FUNC_10BIT_ADDR`: accepted;
  `drivers/i2c/i2c-core-base.c` never tests that bit.
- `i2c_lock_addr()`: -EBUSY when the same number is being instantiated on the
  same adapter; it returns without the "Failed to register" message.
- `i2c_lock_addr()` covers every request without `I2C_CLIENT_TEN`,
  `I2C_CLIENT_SLAVE` included, and keys on the raw `addr`, not the encoded
  one.
- `i2c_lock_addr()` bit is held until `device_register()` returns, so across a
  synchronous driver probe of the new client.
- `i2c_check_addr_busy()` upward: only clients attached directly to each
  ancestor adapter, for as long as `i2c_parent_is_i2c_adapter()` finds a
  parent adapter.
- `i2c_check_addr_busy()` downward: the clients of the adapter and,
  recursively, of its child adapters; `i2c_check_mux_children()` descends only
  into a child whose `dev->type` is `i2c_adapter_type`, so an adapter that
  hangs under a client device, as the ATR channels of
  `drivers/misc/ti_fpc202.c` do, is not reached.
- Sibling branches of a mux are not checked; the same address on two channels
  is accepted.
- Without `CONFIG_I2C_MUX`, `i2c_parent_is_i2c_adapter()` returns NULL and
  there is no upward walk.

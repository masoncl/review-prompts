- `master_xfer` and `master_xfer_atomic`: still members of
  `struct i2c_algorithm` in `include/linux/i2c.h`, each in an anonymous union
  with `xfer` and `xfer_atomic`, the same way `reg_slave` and `unreg_slave`
  pair with `reg_target` and `unreg_target`.
- The core calls and tests through the old spellings only: `master_xfer` and
  `master_xfer_atomic` in `__i2c_transfer()`, `__i2c_lock_bus_helper()` and
  `__i2c_smbus_xfer()`; `reg_slave` and `unreg_slave` in
  `i2c_slave_register()` and `i2c_slave_unregister()`.
- `i2c_mux_add_adapter()` and `i2c_atr_new()`: test the parent through
  `master_xfer` and fill the child through `xfer`.
- Searching for the new spelling finds no call site; every direct call of the
  callback in this tree, inside or outside `drivers/i2c`, is spelled
  `master_xfer` or `master_xfer_atomic`.
- Adapter drivers here use either spelling in their initialisers; both are
  valid.

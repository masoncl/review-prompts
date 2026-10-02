- `I2C_MUX_LOCKED` passed to `i2c_mux_alloc()`: makes the mux mux-locked;
  without it `mux_locked` starts as 0, which is parent-locked.
- `mux_locked` in `struct i2c_mux_core`: this is what `i2c_mux_add_adapter()`
  reads. `i2c_mux_gpio_probe()`, `i2c_mux_pinctrl_probe()` and `i2c_mux_probe()`
  in `drivers/i2c/muxes/i2c-mux-gpmux.c` call `i2c_mux_alloc()` with flags 0
  and then set the field directly, so a search for `I2C_MUX_LOCKED` does not
  find every mux-locked mux.
- Lock held by a mux-locked mux: `mux_lock` in the parent's
  `struct i2c_adapter`. `struct i2c_mux_core` has no lock of its own.
- Parent's `mux_lock`: taken first by both kinds, so a transfer through any
  mux child of the same parent, of either kind, is locked out for the whole
  select, transfer, deselect.
- Lock held by a parent-locked mux: the parent's `mux_lock` plus the parent
  locked with `I2C_LOCK_SEGMENT` (see the table in "Bus locks"). This reaches
  the root's bus lock only when every adapter between the mux and the root is
  a parent-locked child.
- Parent-locked mux below a mux-locked one: the lock chain stops at a
  `mux_lock` and the root is not locked, so traffic to devices directly on
  the root can run between select and the transfer.
- Parent-locked select that calls into gpio, pinctrl or regmap: any transfer
  those cause on the locked parent must be unlocked too, or it deadlocks; see
  PL2 in `Documentation/i2c/i2c-topology.rst`. `i2c_mux_gpio_probe()` avoids
  this by choosing mux-locked when every GPIO sits behind the same root
  adapter as the mux.

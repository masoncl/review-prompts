- Drivers install their own `struct i2c_lock_operations` too, by setting
  `lock_ops` before they register the adapter; search for `lock_ops = &`. For
  example `i2c_gpio_lock_ops` in `drivers/i2c/busses/i2c-gpio.c` and
  `drm_dp_i2c_lock_ops` in `drivers/gpu/drm/display/drm_dp_helper.c`.
- `i2c_atr_lock_ops` in `drivers/i2c/i2c-atr.c`: set on each ATR child
  adapter; takes only the `lock` mutex of `struct i2c_atr`, ignores the flag
  and never locks the parent, so `I2C_LOCK_ROOT_ADAPTER` on an ATR child does
  not lock the root adapter.
- `bus_lock` is not the bus lock of every adapter: `drm_dp_i2c_lock_ops`
  takes `hw_mutex` of `struct drm_dp_aux`, `gmbus_lock_ops` and
  `i2c_atr_lock_ops` take a mutex of their own. Code outside an adapter's own
  lock ops has to lock through `i2c_lock_bus()`.
- What each flag takes, per lock ops:

| `lock_ops` | `I2C_LOCK_SEGMENT` | `I2C_LOCK_ROOT_ADAPTER` |
|---|---|---|
| `i2c_adapter_lock_ops` (default) | own `bus_lock` | own `bus_lock` |
| `i2c_mux_lock_ops` (mux-locked child) | parent's `mux_lock` only | parent's `mux_lock`, then `i2c_lock_bus()` on the parent with the same flag |
| `i2c_parent_lock_ops` (parent-locked child) | parent's `mux_lock`, then `i2c_lock_bus()` on the parent with the same flag | parent's `mux_lock`, then `i2c_lock_bus()` on the parent with the same flag |

- Flag test: among the lock ops in `drivers/i2c/`, only `i2c_mux_lock_ops`
  tests the flag; `i2c_parent_lock_ops` forwards it unchanged and the others
  ignore it.
- Mux child's own `bus_lock`: taken by neither mux lock ops.

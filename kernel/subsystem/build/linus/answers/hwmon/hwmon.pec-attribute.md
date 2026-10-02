- `pec_store()`: does not call `i2c_check_functionality()`; that check is made
  once, in `hwmon_pec_register()`.
- Finding the hwmon device: `device_find_child()` on the client device with
  `hwmon_match_device()`; `-ENODEV` if there is none; the reference is dropped
  with `put_device()` on both exits.

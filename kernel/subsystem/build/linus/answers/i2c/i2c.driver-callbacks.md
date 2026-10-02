- Models have the helpers right; see `i2c_client_get_device_id()` and
  `i2c_get_match_data()` in `drivers/i2c/i2c-core-base.c`.
- Client without a firmware node (sysfs `new_device`, board info) bound
  through `of_match_table` (`CONFIG_OF`): `i2c_of_match_device()` falls back
  to `i2c_of_match_device_sysfs()` in `drivers/i2c/i2c-core-of.c`, which
  compares `client->name` with the compatible strings, with and without the
  vendor prefix.
- For such a client `i2c_get_match_data()` never returns the
  `of_match_table` `.data`: `device_get_match_data()` gives NULL, so the result
  is the `id_table` `driver_data` for that name, or NULL when `id_table` is
  absent or lacks the name.

- Empty description: `__hwmon_create_attrs()` returns `ERR_PTR(-EINVAL)` when
  the total from `hwmon_num_channel_attrs()` is 0, and registration fails.
- What is counted: set bits in the raw config words (`hweight32()`), before
  any template or visibility test.
- Description whose bits are all hidden or have no name (for example only
  `HWMON_C_REGISTER_TZ`): count is non-zero, registration succeeds, no file is
  generated.

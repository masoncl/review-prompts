- `__hwmon_device_register()` stores the caller's pointer (`hwdev->name =
  name`); it makes no copy and changes no character.
- Name that fails the test: `dev_warn()` "is not a valid name attribute, please
  fix", then registration proceeds with the name unchanged.
- `hwmon_is_bad_char()` in `include/linux/hwmon.h`: true for `-`, `*`, space,
  `\t`, `\n` only; `/` and other whitespace pass.
- `__hwmon_device_register()` does not call `hwmon_is_bad_char()`; it uses
  `strpbrk(name, "-* \t\n")` and also warns on an empty string.
- The two character lists are separate; `hwmon_is_bad_char()` is used only by
  `__hwmon_sanitize_name()`.
- `hwmon_sanitize_name()` and `devm_hwmon_sanitize_name()`: do not repair an
  empty string; NULL input gives `ERR_PTR(-EINVAL)`.
- Unsanitised `dev_name()` of the parent as name: memory-safe while the parent
  lives, but triggers the warning when it holds `-`.
- **Unsafe usage**: a name string that is freed or goes out of scope while the
  hwmon device is registered; `name_show()` reads `hwdev->name` on each read
  and `hwmon_dev_release()` never frees it.
  - Safe: a string literal or a field that lives as long as the parent
    binding, such as `client->name` in `lm90_probe()`.
  - Safe: `devm_hwmon_sanitize_name()` on the parent before the devm
    registration on the same device, as `m10bmc_hwmon_probe()` does; devres
    frees it after `devm_hwmon_release()`.
  - Safe: `hwmon_sanitize_name()` with `kfree()` after
    `hwmon_device_unregister()`, as `sfp_hwmon_remove()` in
    `drivers/net/phy/sfp.c` does.

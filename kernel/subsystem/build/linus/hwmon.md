# Hardware Monitoring Subsystem

## Main structures

### Objects and how they relate

- `struct hwmon_ops` callbacks: only `is_visible` receives `drvdata`; `read`,
  `read_string` and `write` receive the hwmon class `struct device *`, and
  reach the driver data with `dev_get_drvdata()`.
- `hwmon_energy64`: the `long *val` given to `read` points at an `s64`, and the
  driver casts it back; see `ina238_read()` in `drivers/hwmon/ina238.c` for
  the cast.
- `struct hwmon_thermal_data`: exists only for a channel that
  `devm_thermal_of_zone_register()` attached to a zone; on `-ENODEV` the
  channel is skipped and registration still succeeds, see
  `hwmon_thermal_add_sensor()`.
- `hwmon_device_register_for_thermal()`: the bridge in the other direction,
  exported in namespace `HWMON_THERMAL` and called only from
  `drivers/thermal/thermal_hwmon.c`. The hwmon device has no
  `struct hwmon_chip_info` and no groups, its parent is a thermal zone's
  `struct device`, and the files are added later with `device_create_file()`.
- `struct thermal_hwmon_device` in `drivers/thermal/thermal_hwmon.c`: one
  hwmon device shared by every thermal zone of the same type; its parent is
  the zone that created it. `thermal_remove_hwmon_sysfs()` for the parent
  zone unregisters the hwmon device and removes the files of every zone; for
  another zone it removes only that zone's files.
- `struct hwmon_chip_info` and `name`: the core stores both pointers without
  copying, and each `struct hwmon_device_attribute` stores the ops pointer.
  The table need not be static; `lm90_probe()` in `drivers/hwmon/lm90.c`
  builds it inside its driver data.

## Where to look

**Core files**

- `drivers/hwmon/` has exactly three subdirectories: `drivers/hwmon/occ/`,
  `drivers/hwmon/peci/` and `drivers/hwmon/pmbus/`; each has its own `Kconfig`
  and `Makefile`.
- `drivers/hwmon/occ/`: `common.c` and `sysfs.c` link into one module,
  `occ-hwmon-common`, under `CONFIG_SENSORS_OCC`; `common.h` is its header.
- `drivers/hwmon/peci/`: has no shared C file; `common.h` holds two structs
  and two inline helpers.
- `CONFIG_SENSORS_PECI`: builds no object; its only use in a Makefile is
  `obj-$(CONFIG_SENSORS_PECI) += peci/` in `drivers/hwmon/Makefile`.
- `hwmon_lock()` and `hwmon_unlock()`: defined and exported in
  `drivers/hwmon/hwmon.c`; `DEFINE_GUARD()` in `include/linux/hwmon.h` makes
  `guard(hwmon_lock)(dev)` available.
- `CONFIG_HWMON_DEBUG_CHIP`: no C file tests it; its only use is
  `ccflags-$(CONFIG_HWMON_DEBUG_CHIP) := -DDEBUG` in `drivers/hwmon/Makefile`,
  and none of the three subdirectory `Makefile`s sets ccflags.

**Documentation files**

- `Documentation/ABI/testing/sysfs-class-hwmon`: the authority on the unit and
  the RO/RW mode of the standard attributes it lists; it is in the
  `MAINTAINERS` entry "HARDWARE MONITORING".
- `Documentation/hwmon/sysfs-interface.rst`: gives the names, the channel
  numbering, the alarm semantics and how to interpret written values; it gives
  a `Unit:` line for only four power and energy entries and points to the ABI
  file for the rest.
- Attribute spelling differs between the two: `in[0-*]_min` in
  `sysfs-interface.rst`, `/sys/class/hwmon/hwmonX/inY_min` in the ABI file.
- `Documentation/hwmon/hwmon-kernel-api.rst`: its copy of `struct hwmon_ops`
  lists only `is_visible`, `read` and `write`; `visible` and `read_string` are
  described only in the kerneldoc in `include/linux/hwmon.h`.
- There is no writing-drivers.rst under `Documentation/hwmon/`;
  `hwmon-kernel-api.rst` and `submitting-patches.rst` cover that ground.
- `Documentation/hwmon/` is flat: drivers under `drivers/hwmon/pmbus/`,
  `drivers/hwmon/occ/` and `drivers/hwmon/peci/` are documented there too, for
  example `Documentation/hwmon/occ.rst`.
- Per-driver file name: not always the source file name; for example
  `Documentation/hwmon/inspur-ipsps1.rst` documents
  `drivers/hwmon/pmbus/inspur-ipsps.c`.

**Shared helper code**

- Finding the shared C files: search `drivers/hwmon/` for `EXPORT_SYMBOL`;
  header-only `drivers/hwmon/lm75.h` and `drivers/hwmon/peci/common.h` do not
  show up in that search.
- `drivers/hwmon/max1111.c`: the one hit that is a chip driver, not a helper;
  it exports `max1111_read_channel()` for `arch/arm/mach-pxa/sharpsl_pm.c`.
- Core plus bus front ends in `drivers/hwmon/` itself:

  | Core | Header | Symbol | Front ends |
  |---|---|---|---|
  | `adt7x10.c` | `adt7x10.h` | `CONFIG_SENSORS_ADT7X10` | `adt7410.c`, `adt7310.c` |
  | `ltc2947-core.c` | `ltc2947.h` | `CONFIG_SENSORS_LTC2947` | `ltc2947-i2c.c`, `ltc2947-spi.c` |
  | `nct6775-core.c` | `nct6775.h` | `CONFIG_SENSORS_NCT6775_CORE` | `nct6775-platform.c`, `nct6775-i2c.c` |

- `CONFIG_SENSORS_NCT6775`: builds module `nct6775` from `nct6775-platform.c`;
  there is no nct6775.c.
- No shared code exists for Aquacomputer devices;
  `drivers/hwmon/aquacomputer_d5next.c` is a single self-contained driver.
- `drivers/hwmon/lm75.h`: holds two static inline functions,
  `LM75_TEMP_TO_REG()` and `LM75_TEMP_FROM_REG()`, and the constants
  `LM75_TEMP_MIN`, `LM75_TEMP_MAX` and `LM75_SHUTDOWN`; there is no
  LM75_TEMP_MIN_FROM_REG.
- `drivers/hwmon/lm75.c`: uses only the three constants from `lm75.h`; the two
  conversion functions are used by other drivers, found by searching for
  `#include "lm75.h"`, for example `w83781d.c` and `nct6775-core.c`.
- `drivers/hwmon/lm75.h`: has no include guard.
- `drivers/hwmon/sch56xx-common.c`: a module with its own `module_init()`;
  `sch56xx_init()` probes the Super-I/O at 0x4e, then 0x2e, and registers the
  platform device named "sch5627" or "sch5636" that the chip driver binds to.
- `drivers/hwmon/sch56xx-common.c`: owns no lock; `sch56xx_read_virtual_reg()`,
  `sch56xx_write_virtual_reg()`, `sch56xx_read_virtual_reg16()` and
  `sch56xx_read_virtual_reg12()` take none.
- `devm_regmap_init_sch56xx()` and `sch56xx_watchdog_register()`: take a
  `struct mutex *` from the chip driver; the regmap bus callbacks and the
  watchdog ops lock that mutex around each mailbox access.

## Hwmon devices in other subsystems

**Drivers outside the directory**

- `HARDWARE MONITORING` in `MAINTAINERS`: has a content pattern,
  `K: (devm_)?hwmon_device_(un)?register(|_with_groups|_with_info)`; this is
  what sends out-of-directory patches to the hwmon list.
- `F:` lines of that entry: cover only docs, bindings, `drivers/hwmon/`,
  `include/linux/hwmon*.h` and `include/trace/events/hwmon*.h`; no file under
  `drivers/acpi/` or any other subsystem is listed.
- Other entries with `L: linux-hwmon@vger.kernel.org`: none covers an
  out-of-directory file that registers a hwmon device; the only paths outside
  `Documentation/` and `drivers/hwmon/` are `include/linux/f75375s.h`,
  `include/dt-bindings/thermal/lm90.h` and `drivers/gpio/gpio-ltc4283.c`.
- `K:` matching in `scripts/get_maintainer.pl`: unanchored, so
  `hwmon_device_register_for_thermal()` and `hwmon_device_unregister()` both
  match.
- `K:` on a patch: tested against the lines before the first `---`/`+++`
  file line (commit message included) and, after it, only against lines that
  start with `+` or `-`; a name that appears only in context lines does not
  match.
- `K:` with `get_maintainer.pl -f <file>`: not applied unless
  `--keywords-in-file` is given; the default is off.
- Finding the callers: search the tree for the `K:` regex; all callers outside
  `drivers/hwmon/` are under `drivers/`, except those under
  `sound/soc/codecs/`.
- No register call exists under `drivers/net/ethernet/wangxun/`,
  `drivers/mfd/`, `drivers/infiniband/` or `drivers/iio/`.
- `drivers/w1/w1.c`: a bus core that registers the hwmon device for slave
  drivers that supply `chip_info`; the slave file has no register call, so a
  patch to it does not match `K:`.

**Build dependencies**

- `include/linux/hwmon.h`: has no test of `CONFIG_HWMON` and no stub; every
  function except the inline `hwmon_is_bad_char()` is a plain prototype in
  every configuration.
- Unreachable hwmon core (`HWMON=n`, or `HWMON=m` with a built-in caller): an
  unguarded call compiles and fails at link time.
- Registration functions in `drivers/hwmon/hwmon.c`: return a device or an
  `ERR_PTR()`, never `NULL`.
- `#ifdef CONFIG_HWMON` in C: true only for `HWMON=y`, because `=m` defines
  `CONFIG_HWMON_MODULE` instead (`include/linux/kconfig.h`).
- `#ifdef CONFIG_HWMON` with no Kconfig dependency: links in every
  configuration, as `MARVELL_10G_PHY` and `drivers/net/phy/marvell10g.c` do;
  the cost is that a modular driver with `HWMON=m` gets no hwmon device.
- `ifdef CONFIG_HWMON` in a Makefile: true for `m` as well, unlike the C form.
- `drivers/net/phy/aquantia/Makefile`: builds `aquantia_hwmon.o` even when the
  driver is built in and `HWMON=m`; this links only because
  `drivers/net/phy/aquantia/aquantia_hwmon.c` wraps its whole body in
  `#if IS_REACHABLE(CONFIG_HWMON)`.
- `if (IS_REACHABLE(CONFIG_HWMON))` as a C condition around the call: valid
  with no stub, because the prototypes are unconditional; see
  `drivers/regulator/tps65185.c`.
- `NXP_TJA11XX_PHY`: `depends on HWMON`, so hwmon is mandatory there and
  `drivers/net/phy/nxp-tja11xx.c` has no guard.
- `depends on HWMON || !HWMON` (`MLX5_CORE`) and `depends on HWMON = n || HWMON`
  (`TOUCHSCREEN_ADS7846`): same effect as `depends on HWMON || HWMON=n`.
- `select HWMON`: used in this tree by drivers that need hwmon
  unconditionally, for example `DRM_AMDGPU`; `TXGBE` uses
  `select HWMON if TXGBE=y`.
- `drivers/acpi/fan.h`: the guarded functions are
  `devm_acpi_fan_create_hwmon()` and `acpi_fan_notify_hwmon()`; there is no
  acpi_fan_create_hwmon().
- `struct acpi_fan` field `hdev`: exists only under
  `IS_REACHABLE(CONFIG_HWMON)`, so only `drivers/acpi/fan_hwmon.c` may touch it.
- Registration failure: the tree has both policies. `acpi_fan_probe()` and
  `mv3310_hwmon_probe()` return the error; `sfp_hwmon_probe()` and
  `drivers/regulator/tps65185.c` log it and continue.
- Compiled-out stub: must return 0 where the caller propagates the result, as
  the stub of `devm_acpi_fan_create_hwmon()` does.
- **Potentially unsafe usage**: guarding hwmon calls with
  `IS_ENABLED(CONFIG_HWMON)` in a tristate driver.
  - Unsafe: when Kconfig allows the driver to be `y` while `HWMON=m`; the
    guard is true and the built-in call has no definition to link against.
  - Safe: with `depends on HWMON || HWMON=n` on the driver, as `SFP` with
    `drivers/net/phy/sfp.c`; the dependency caps the driver at `m` when
    `HWMON=m`.
  - Safe: with `IS_REACHABLE(CONFIG_HWMON)` instead, which needs no Kconfig
    line, as `drivers/acpi/fan.h` does for `devm_acpi_fan_create_hwmon()`.
  - Safe: with a bool sub-option that has
    `depends on HWMON && !(REALTEK_PHY=y && HWMON=m)`, as `REALTEK_PHY_HWMON`,
    tested by `rtl822x_probe()`.
- **Potentially unsafe usage**: passing a stored hwmon device pointer to
  `hwmon_device_unregister()` or `hwmon_notify_event()`.
  - Unsafe: when registration may have been skipped or its failure ignored,
    so the pointer is `NULL` or an `ERR_PTR()`; both functions dereference it
    without a test.
  - Safe: test first, as `sfp_hwmon_remove()` does with `IS_ERR_OR_NULL()`.
  - Safe: fail the probe on registration failure and install the notifier
    afterwards, as `acpi_fan_probe()` does before `acpi_fan_notify_hwmon()` can
    run.
  - Safe: for the unregister, use `devm_hwmon_device_register_with_info()`,
    which adds the release action only after registration succeeded.

## Class device and attribute names

**Class device and parent**

- There is no hwmon_dev_name_is_valid() here; the name test is an inline
  `strpbrk()` in `__hwmon_device_register()`.
- `label` attribute: a `kstrdup()` copy of the `label` device property of the
  device passed in; a failing `device_property_read_string()` fails
  registration.
- NULL parent: `hwmon_device_register_with_groups()` and
  `hwmon_device_register()` do not test `dev`; the hwmon device then has no
  parent, for example in `drivers/platform/mips/cpu_hwmon.c`.
- `dev_get_drvdata()` on the hwmon device: returns the `drvdata` argument of
  the registration call; the core never copies the parent's driver data.
- `hwmon_device_unregister()` on a device whose name does not parse as
  `HWMON_ID_FORMAT`, such as the parent: `dev_dbg()` only; nothing is
  unregistered and no id is freed.

**Attribute bit macros**

- `hwmon_energy64` is a sensor type in `enum hwmon_sensor_types` with no
  attribute enum and no macros of its own; it is described with the
  `HWMON_E_` macros of `enum hwmon_energy_attributes`.
- `HWMON_CHANNEL_INFO(energy64, HWMON_E_INPUT)` is the correct form, for
  example in `drivers/hwmon/ina238.c`.
- `hwmon_curr` uses the prefix `HWMON_C_`, the same as `hwmon_chip`; no macro
  name is shared, but some differ by little.
- `HWMON_C_ALARM` and `HWMON_C_RESET_HISTORY` are curr bits;
  `HWMON_C_ALARMS` and `HWMON_C_CURR_RESET_HISTORY` are chip bits.
- A macro of another type whose bit number has no template in the described
  type: `hwmon_genattrs()` in `drivers/hwmon/hwmon.c` skips the bit; no
  attribute, no error, no message.

**Generated attribute names**

- `hwmon_attr_base()`: 0 for `hwmon_in` and `hwmon_intrusion`; 1 for every
  other type, `hwmon_pwm` and `hwmon_energy64` included.
- There is no hwmon_sensors prefix table; each template outside
  `hwmon_chip_attrs` is the whole name with one `%d`, such as "temp%d_input"
  in `hwmon_temp_attr_templates`.
- `hwmon_energy64`: `__templates[]` maps it to `hwmon_energy_attr_templates`,
  so its files are named `energy%d_...` exactly like those of `hwmon_energy`.
- Channel number: the position in `config[]` of one
  `struct hwmon_channel_info` plus the base; it restarts for every entry of
  `chip->info`.
- **Potentially unsafe usage**: a `hwmon_energy` and a `hwmon_energy64` entry
  in one `struct hwmon_chip_info`.
  - Unsafe: when both set the same `HWMON_E_` bit at the same `config[]`
    position and both are visible; the core does not check for duplicate
    names, `sysfs_add_file_mode_ns()` returns `-EEXIST` and
    `device_register()` fails.
  - Safe: when the bits at each position are disjoint, as in `ltc4282_info`
    in `drivers/hwmon/ltc4282.c`; the shared table in `__templates[]` is what
    makes the names equal.
- Name storage, for every type but `hwmon_chip`: `name[]` in
  `struct hwmon_device_attribute`, of `MAX_SYSFS_ATTR_NAME_LENGTH` (32)
  bytes; there is no MAX_SYSFS_ATTR_NAME_LEN and the name is not duplicated
  with `devm_kstrdup()`.
- Too-long name: `scnprintf()` cuts it at 31 characters; `hwmon_genattr()`
  ignores the return value and prints nothing.

**Chip feature bits**

- Only `HWMON_C_REGISTER_TZ` and `HWMON_C_PEC` produce no file on the hwmon
  device; every other enumerator of `enum hwmon_chip_attributes` has a string
  in `hwmon_chip_attrs`, `hwmon_chip_update_interval_us` included.
- `is_visible` is never asked about either bit; a driver that wants one off
  leaves it out of `config[0]` before registering, as `lm90_probe()` in
  `drivers/hwmon/lm90.c` does for `HWMON_C_PEC`.
- One condition in `__hwmon_device_register()` encloses both bits:
  `hdev->of_node` set, `chip->ops->read` set, and `chip->info[0]->type ==
  hwmon_chip`.
- `HWMON_C_PEC` without an `of_node` on the hwmon device, or without
  `ops->read`: ignored, no `pec` file, registration succeeds.
- `hdev->of_node`: the inherited node described under "Firmware node of the
  device"; `devm_thermal_of_zone_register()` looks up zones by that node.
- Thermal sensor id: the 0-based channel index, not the number in
  `temp%d_input`.
- `-ENODEV` from `devm_thermal_of_zone_register()`: `dev_info()` and the scan
  continues; any other error fails the registration.
- There is no hwmon_pec_attr_group; `hwmon_pec_register()` creates the one
  file `dev_attr_pec` on the I2C client with `device_create_file()`, and only
  when the adapter has `I2C_FUNC_SMBUS_PEC`; otherwise it returns 0 and
  creates nothing.
- `HWMON_C_PEC`, once the condition in `__hwmon_device_register()` holds, with
  a parent that `i2c_verify_client()` rejects: `hwmon_pec_register()` returns
  `-EINVAL` and the registration fails.
- `HWMON_C_PEC` when `IS_REACHABLE(CONFIG_I2C)` is false: the stub
  `hwmon_pec_register()` returns `-EINVAL`, with the same result.
- `pec_store()`: finds the hwmon device with `device_find_child()` and
  `is_hwmon_device()`, so it acts on the first hwmon child of the I2C client.
- `pec_store()` with no `ops->write`: skips the driver call and still changes
  `I2C_CLIENT_PEC` in `client->flags`.

## Registration

**Registration functions**

- `include/linux/hwmon.h` marks three functions deprecated by comment:
  `hwmon_device_register()`, `hwmon_device_register_with_groups()`,
  `devm_hwmon_device_register_with_groups()`.
- `hwmon_device_register_for_thermal()`: not marked in the header; the
  restriction is the kerneldoc in `drivers/hwmon/hwmon.c` plus
  `EXPORT_SYMBOL_NS_GPL()` in namespace "HWMON_THERMAL", which only
  `drivers/thermal/thermal_hwmon.c` imports.
- `hwmon_device_register()`: present, still has callers, calls `dev_warn()` on
  every call; the two with_groups functions print no deprecation message.
- NULL arguments in the other registration functions;
  `hwmon_device_register_with_info()` returns `-EINVAL` for NULL `dev` and for
  NULL `name`:

| Function | NULL `dev` | NULL `name` |
|---|---|---|
| `hwmon_device_register()` | accepted | always NULL, `name` file hidden |
| `hwmon_device_register_with_groups()` | accepted | `-EINVAL` |
| `devm_hwmon_device_register_with_groups()` | `-EINVAL` | `-EINVAL`, no fallback |
| `hwmon_device_register_for_thermal()` | `-EINVAL` | `-EINVAL` |

- `show`/`store` handlers in `groups` of a with_groups device: called without
  `lock` of `struct hwmon_device`; with no `chip`,
  `__hwmon_device_register()` installs `groups` as given and the core never
  takes the lock for that device.
- `name` and `label` class attributes: created for every variant by
  `hwmon_dev_attr_groups`; `hwmon_dev_attr_is_visible()` hides each when its
  string is NULL.
- `hwmon_lock()` and `hwmon_notify_event()`: usable on a device from any
  variant; `mutex_init()` runs for all in `__hwmon_device_register()`.
- devm_hwmon_device_unregister is not in this tree;
  `hwmon_device_unregister()` is the only unregister function, and a devm
  registration is undone only by devres.

**Argument checks**

- `chip == NULL`: `ERR_PTR(-EINVAL)` from `hwmon_device_register_with_info()`,
  and so from the devm form, whether or not `extra_groups` is given.
- `chip` non-NULL: `-EINVAL` unless `chip->ops`, `chip->info`, and one of
  `chip->ops->visible` or `chip->ops->is_visible` are set.
- NULL `name`, `hwmon_device_register_with_info()`: `ERR_PTR(-EINVAL)`.
- NULL `name`, `devm_hwmon_device_register_with_info()`: accepted; the name
  becomes `devm_hwmon_sanitize_name(dev, dev_name(dev))`, so it differs per
  instance.
- Failure of that sanitize call: returned through `ERR_CAST()`; PTR_ERR_CAST
  is not in this tree.
- In-tree caller that passes a NULL name to the devm form: for example
  `tja11xx_hwmon_register()` in `drivers/net/phy/nxp-tja11xx.c`.

**Device name rules**

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

**Device passed to callbacks**

- `pec_store()`: the sysfs file sits on the I2C client, yet `write` still
  receives the hwmon device, with `hwmon_chip` and `hwmon_chip_pec`.

**State before registration**

- `read` during registration: for a sensor with a matching zone,
  `thermal_of_zone_register()` ends in `thermal_zone_device_enable()`, which
  calls `hwmon_thermal_get_temp()` synchronously.
- `write` during registration: the same update calls
  `thermal_zone_set_trips()`, which calls `hwmon_thermal_set_trips()` only when
  the read succeeded and a trip moved `low` or `high` off `-INT_MAX` /
  `INT_MAX`; it then writes `hwmon_temp_min` and `hwmon_temp_max`.
- `hwmon_thermal_set_trips()`: tests the `HWMON_T_MIN` and `HWMON_T_MAX` config
  bits, not `is_visible`; `write` can get an attribute that `is_visible` hid
  or made read-only, and `-EOPNOTSUPP` from it is ignored.
- lm75_probe is not in this tree; `lm75_generic_probe()` in
  `drivers/hwmon/lm75.c` shows chip setup, then registration, then
  `devm_request_threaded_irq()` with the hwmon device as cookie.
- **Potentially unsafe usage**: a callback that uses the hwmon device pointer
  the driver stores from the return value.
  - Unsafe: when the callback dereferences the stored pointer or passes it to
    `hwmon_notify_event()` with no NULL test; it is unset until registration
    returns.
  - Safe: use the `dev` argument of the callback, which the core passes as the
    hwmon device, as `lm75_read()` does with `dev_get_drvdata(dev)`.
  - Safe: test the stored pointer first, as `lm90_update_alarms_locked()` does
    with `data->hwmon_dev`.

**Removal order**

- lm75_probe is not in this tree; `lm75_generic_probe()` in
  `drivers/hwmon/lm75.c` adds `lm75_remove()` with
  `devm_add_action_or_reset()` before the devm registration.
- `devm_hwmon_release()`: calls `hwmon_device_unregister()` for a device
  registered with a devm function; attached with `devres_add()` to the `dev`
  argument, so it runs when that device is unbound or deleted, which is the
  caller's unbind only if `dev` is the device the driver is bound to.
- Inside `device_del()`: `device_remove_attrs()` runs before
  `devres_release_all()`, so thermal zones and the `pec` file outlive the
  sysfs attributes; all are gone when `hwmon_device_unregister()` returns.
- **Unsafe usage**: calling `hwmon_notify_event()` or `hwmon_lock()` on the
  hwmon device after it is unregistered; `hwmon_dev_release()` has freed the
  `struct hwmon_device` both dereference.
  - Safe: IRQ requested with `devm_request_threaded_irq()` after the devm
    registration, so devres frees it first, as `lm75_generic_probe()` does.
  - Safe: work cancelled by a devm action added after the devm registration,
    as `lm90_stop_work()` added in `lm90_probe()`.
  - Safe: non-devm, remove what takes the lock and then unregister, as
    `corsairpsu_remove()` in `drivers/hwmon/corsair-psu.c` does with
    `debugfs_remove_recursive()` before `hwmon_device_unregister()`.

## Channel description

**Position of the chip entry**

- `__hwmon_device_register()`: does not search `info` for the chip entry; it
  tests `chip->info[0]->type == hwmon_chip` and reads only
  `chip->info[0]->config[0]`.
- Position-dependent flags: `HWMON_C_REGISTER_TZ` and `HWMON_C_PEC`, both
  tested in that one block; no other chip bit is read there.
- `hwmon_thermal_register_sensors()`: its loop starts at `info[1]`; it is
  reached only when `info[0]` is the chip entry.
- **Unsafe usage**: a `hwmon_chip` entry that carries `HWMON_C_REGISTER_TZ` or
  `HWMON_C_PEC` anywhere but `info[0]`; the flag is dropped, registration
  succeeds, nothing is logged.
  - Safe: chip entry first, as `lm75_info` in `drivers/hwmon/lm75.c`; the
    `info[0]` test in `__hwmon_device_register()` defines the requirement.
  - Safe: chip entry later that holds only bits named in `hwmon_chip_attrs[]`,
    as `nzxt_smart2_channel_info` in `drivers/hwmon/nzxt-smart2.c`;
    `__hwmon_create_attrs()` walks every entry.

**Attribute visibility**

- `visible` and `is_visible` both set: `hwmon_is_visible()` returns
  `ops->visible` and never calls `ops->is_visible()`; the callback runs only
  when `visible` is 0.
- First round of calls: from `hwmon_genattr()` under `__hwmon_create_attrs()`,
  before `device_register()`; the callback gets the `drvdata` passed to
  registration and the hwmon device is not registered yet.
- Second call: `hwmon_thermal_register_sensors()` asks again for
  `hwmon_temp_input` of each `hwmon_temp` channel that has `HWMON_T_INPUT`,
  after `device_register()`; any non-zero answer leads to
  `hwmon_thermal_add_sensor()`.
- Neither `visible` nor `is_visible` set: rejected with `-EINVAL` in
  `hwmon_device_register_with_info()`, not in `__hwmon_device_register()`.

**Missing callbacks**

- Empty description: `__hwmon_create_attrs()` returns `ERR_PTR(-EINVAL)` when
  the total from `hwmon_num_channel_attrs()` is 0, and registration fails.
- What is counted: set bits in the raw config words (`hweight32()`), before
  any template or visibility test.
- Description whose bits are all hidden or have no name (for example only
  `HWMON_C_REGISTER_TZ`): count is non-zero, registration succeeds, no file is
  generated.

**Bits without a name**

- Bit index at or beyond `__templates_size[type]`, or a NULL slot inside the
  table: `hwmon_genattrs()` skips it with `continue`; no error, no message, and
  `hwmon_genattr()` is not called for it.
- `hwmon_genattr()`: makes no test of `template`; its `-ENOENT` comes only
  from a mode of 0, so the skip in `hwmon_genattrs()` is the only guard against
  a NULL name.
- `hwmon_chip_attrs[]`: `hwmon_chip_register_tz` is a NULL hole inside the
  table and `hwmon_chip_pec` lies past its end; neither flag creates a file.
- `info->type` at or beyond `ARRAY_SIZE(__templates)`: `hwmon_genattrs()`
  returns `-EINVAL` and registration fails, unlike an unknown bit.

## Driver callbacks

**Callback calling context**

- Attributes passed in `extra_groups`: the core does not wrap them, so they
  run without the core lock (`lock` in `struct hwmon_device`) unless the
  driver takes `hwmon_lock()`.
- Lock order on the thermal paths: the `lock` of `struct thermal_zone_device`
  first, then the core lock.
- Thermal zones are registered only when all hold: `CONFIG_THERMAL_OF`,
  `chip->ops->read` set, `chip->info[0]->type == hwmon_chip` with
  `HWMON_C_REGISTER_TZ` in its first config word, an `of_node` on the
  parent or any ancestor, and per channel `HWMON_T_INPUT` set and visible;
  see `__hwmon_device_register()` and `hwmon_thermal_register_sensors()`.
- **Unsafe usage**: calling `hwmon_lock()` from inside `read`, `write` or
  `read_string`.
  - Unsafe: the core already holds the mutex, and `hwmon_lock()` is a plain
    `mutex_lock()`.
  - Safe: in code the core does not call, such as `shunt_resistor_store()` in
    `drivers/hwmon/ina2xx.c` or `lm90_update_alarms()` in
    `drivers/hwmon/lm90.c`.

**Callback error codes**

- `thermal_zone_set_trips()` in `drivers/thermal/thermal_trip.c`: only logs the
  error that `hwmon_thermal_set_trips()` returns.
- `pec_store()`: defined in `drivers/hwmon/hwmon.c`. It calls `write` first and
  changes `I2C_CLIENT_PEC` only after 0 or `-EOPNOTSUPP`; any other error is
  returned with the flag unchanged.
- `pec_store()` input: parsed with `kstrtobool()`; returns `-ENODEV` when the
  client has no hwmon child device.
- `-EAGAIN` from `read` of `hwmon_temp_input` on the thermal path:
  `thermal_zone_recheck()` in `drivers/thermal/thermal_core.c` retries without
  its `dev_info()` message and without lengthening the delay. Any other error
  lengthens the delay and can end in `thermal_zone_broken_disable()`.
- `-ENODATA`: `Documentation/hwmon/sysfs-interface.rst` specifies it for a read
  of a sensor disabled through its `_enable` attribute; `ltc4282_read()` does
  this.
- Default branch: `-EOPNOTSUPP` is the predominant code under `drivers/hwmon`,
  but no file under `Documentation/hwmon` states it, and some in-tree default
  branches return `-EINVAL` or `-ENOTSUPP`.
- **Potentially unsafe usage**: a `write` that returns a code other than
  `-EOPNOTSUPP` for an attribute it does not implement.
  - Unsafe: when the core writes the attribute on its own: `hwmon_chip_pec`
    with `HWMON_C_PEC` set, or `hwmon_temp_min` / `hwmon_temp_max` with
    `HWMON_T_MIN` / `HWMON_T_MAX` set on a channel that has a thermal zone.
    `pec_store()` then fails and `hwmon_thermal_set_trips()` returns the error.
  - Safe: `lm90_chip_write()` in `drivers/hwmon/lm90.c` sets `HWMON_C_PEC`,
    does not handle `hwmon_chip_pec` and returns `-EOPNOTSUPP` from its default
    branch, which `pec_store()` ignores.
  - Safe: when the core writes nothing the driver lacks. `lm75_write()` in
    `drivers/hwmon/lm75.c` returns `-EINVAL` from its default branches, but
    `lm75_info` sets neither `HWMON_C_PEC` nor `HWMON_T_MIN`, and
    `lm75_write_temp()` handles `hwmon_temp_max`.

**64-bit energy values**

- Pointer type: `s64 *`, not `u64 *`. `hwmon_attr_show()` passes the address of
  an `s64` and prints it with `%lld`, so a value above `S64_MAX` prints
  negative.
- The 64-bit pointer is selected by channel type, not by attribute: every
  non-string attribute declared under `HWMON_CHANNEL_INFO(energy64, ...)` gets
  it on read, `hwmon_energy_enable` included.
- `drivers/hwmon/ltc4282.c` and `drivers/hwmon/ltc4283.c`: declare
  `HWMON_E_ENABLE` under `energy` and `HWMON_E_INPUT` under `energy64`. Both
  produce `energy1_` names because both types use
  `hwmon_energy_attr_templates`.
- `val64` in `hwmon_attr_show()`: not initialised, so a store of fewer than 64
  bits prints uninitialised stack in the remaining bits.

**String attributes**

- `is_string_attr()`: also matches `hwmon_energy64` with `hwmon_energy_label`.
- `hwmon_chip`, `hwmon_pwm` and `hwmon_intrusion`: have no string attribute;
  there is no hwmon_chip_label in this tree.
- `hwmon_attr_show_string()`: holds the hwmon mutex from before `read_string`
  until after `sysfs_emit()`. A string that is changed only by callbacks or
  under `hwmon_lock()` cannot change between the return and the print.
- A string changed or freed by code that does not hold the hwmon mutex: still
  unsafe, for example from an interrupt thread or a work item.
- `s` in `hwmon_attr_show_string()`: not initialised. A `read_string` that
  returns 0 without storing to `*str` makes the core print through a garbage
  pointer.

**Invalid written values**

- The rule is stated only in the section "sysfs attribute writes
  interpretation" of `Documentation/hwmon/sysfs-interface.rst`.
  `Documentation/hwmon/submitting-patches.rst` does not contain it.
- The section names only these cases: continuous, "tempX_max or inX_max", clamp
  with `clamp_val()`; not continuous, "tempX_type" and a fan divider with
  values 2, 4, 8, return `-EINVAL`.
- `pwmX`: not named by the section, and drivers do both.
  `drivers/hwmon/adt7470.c` clamps with `clamp_val()`;
  `drivers/hwmon/pwm-fan.c`, `drivers/hwmon/amc6821.c` and
  `drivers/hwmon/nct7904.c` return `-EINVAL` outside 0 to 255.
- `update_interval` and `samples`: drivers such as `ina238_write_chip()` and
  `lm95234_chip_write()` pick the closest supported value with
  `find_closest()` and return success. The section does not state this.

**Range of written values**

- From `pec_store()`: `write` for `hwmon_chip_pec` receives 0 or 1.
- Wording of `Documentation/hwmon/sysfs-interface.rst`, section "sysfs
  attribute writes interpretation": "do not multiply the result, and only
  add/subtract if it has been divided before the add/subtract".
- Division before the clamp is allowed: Example1 of that section divides by
  1000 and then calls `clamp_val()`.
- `DIV_ROUND_CLOSEST()` before a clamp: not safe, it adds or subtracts half
  the divisor first. `ina238_write_power_max()` clamps to `LONG_MAX / 2`
  before it.
- Scale factor known only at run time: clamp twice, as `ina238_write_in()`
  does. The first clamp, in sysfs units, keeps the multiplication from
  overflowing; the second, to `S16_MIN` / `S16_MAX`, fits the result to the
  register.
- `clamp_val()` with run-time bounds where `lo > hi`: returns `hi` or `lo`, not
  a value in a range. The check in `__clamp_once()` in
  `include/linux/minmax.h` catches only bounds known at build time.

**Conversion arithmetic**

- `LM75_TEMP_TO_REG()` and `LM75_TEMP_FROM_REG()` in `drivers/hwmon/lm75.h`:
  static inline functions, not macros. They do not use `DIV_ROUND_CLOSEST()`;
  the write side adds 250 or -250 by sign and divides by 500.
- Shifts of negative values: used by in-tree conversions after the clamp, for
  example `LM75_TEMP_TO_REG()`, `lm75_write_temp()` and
  `ina238_temp_to_reg()`. The top-level `Makefile` sets
  `-fno-strict-overflow`.
- `DIV_ROUND_CLOSEST()`: expands to plain `/`, so a 64-bit operand can fail to
  link on a 32-bit build. Use one of:

| Helper | Dividend | Divisor |
|---|---|---|
| `DIV_S64_ROUND_CLOSEST()` | `s64` | converted to `s32` |
| `DIV_U64_ROUND_CLOSEST()` | `u64` | converted to `u32` |
| `DIV_ROUND_CLOSEST_ULL()` | `unsigned long long` | 32-bit, uses `do_div()` |
| `DIV64_U64_ROUND_CLOSEST()` | `u64` | `u64` |

- A divisor wider than 32 bits passed to the first two helpers: truncated
  silently by the assignment inside the macro.
- A negative dividend passed to `DIV_ROUND_CLOSEST_ULL()`: converted to
  unsigned, so the result is wrong; `DIV_S64_ROUND_CLOSEST()` is the signed
  form, as in `ina228_read_voltage()`.
- Read side: a result computed in 64 bits that can exceed `LONG_MAX` must be
  clamped before the store to `*val`, as `ina238_read_power()` does.
- Product that can exceed 64 bits: `mul_u64_u64_div_u64()` as in
  `ltc4283_read_energy()`, or `check_mul_overflow()` with a fallback as in
  `ltc4282_read_energy()`.
- `FIELD_PREP()` with a run-time value: masks it silently;
  `__BF_FIELD_CHECK_MASK()` in `include/linux/bitfield.h` checks only
  build-time constants.
- `Documentation/hwmon/submitting-patches.rst`: says to avoid calculations in
  macros and macro-generated functions; one reason it gives is that such
  macros may evaluate their arguments several times.

## Locking

**Lock held by the core**

- `pec_store()`: holds the lock around
  `->write(hdev, hwmon_chip, hwmon_chip_pec, 0, val)` and around the update of
  `client->flags`.
- `pec_show()`: takes no lock and calls no driver code.
- Every call the core makes to `->read`, `->read_string` or `->write` is under
  the lock; `is_visible` is the only `struct hwmon_ops` member the core calls
  without it.
- `hwmon_notify_event()`: does not take the core lock in its own body, but
  see "Nesting the core lock" for `hwmon_temp`.

**Driver use of the core lock**

- In-tree callers of `hwmon_lock()` or the guard: all register with info;
  none registers with groups.
- Guard: `DEFINE_GUARD(hwmon_lock, struct device *, ...)` in
  `include/linux/hwmon.h`, so `guard(hwmon_lock)(dev)` and
  `scoped_guard(hwmon_lock, dev)` both work; there is no try or interruptible
  variant.
- `hwmon_lock()` and `hwmon_unlock()`: do not check their argument. They have
  no NULL test and, unlike `hwmon_notify_event()`, no `is_hwmon_device()`
  test, so a parent device or an unset pointer is not caught;
  `to_hwmon_device()` is applied to it and, given the parent device, they
  lock unrelated memory.
- `extra_groups` show/store functions: the sysfs `dev` argument is already the
  hwmon device, so passing it straight to the guard is correct, as
  `heater_enable_store()` in `drivers/hwmon/sht4x.c` does.
- debugfs, cooling-device and interrupt code: the core passes it no hwmon
  device; it must use the pointer that registration returned, as
  `kb9002_fw_version_show()` in `drivers/hwmon/kb9002.c` does with
  `data->hwmon_dev`.

**Drivers with their own mutex**

- `drivers/hwmon/lm90.c`: has no mutex of its own; `struct lm90_data` holds
  none. Comments there that name an update_lock in the client mean the core
  lock.
- A driver registered with info may still keep its own mutex, taken inside
  the callbacks (core lock outer, driver mutex inner). For example
  `drivers/hwmon/adt7470.c` shares `data->lock` between
  `adt7470_temp_write()`, `adt7470_update_thread()`, its extra attributes and
  `adt7470_pwm_write_waveform()`; removing it there is not a cleanup.

**Nesting the core lock**

- **Unsafe usage**: calling `hwmon_notify_event()` with type `hwmon_temp`
  while the core lock is held (inside a callback or under `hwmon_lock()`).
  With an enabled thermal zone attached to that channel,
  `hwmon_thermal_notify()` calls `thermal_zone_device_update()`, which
  reaches `hwmon_thermal_get_temp()` and takes the same lock again.
  - Safe: schedule a work item under the lock and send the event from the
    work item without the lock, as `lm90_report_alarms()` does for
    `report_work`.
  - Safe: call it from a handler that holds no lock, as
    `lm75_alarm_handler()` does.
- **Unsafe usage**: `cancel_work_sync()` or `cancel_delayed_work_sync()`
  under the core lock, on a work item that itself takes the core lock.
  - Safe: drop the lock first; `lm90_stop_work()` leaves its
    `scoped_guard(hwmon_lock, ...)` before it cancels `alert_work`.
  - Safe: under the lock use `cancel_delayed_work()`, as
    `lm90_update_alarms_locked()` does.

**Interrupt handlers and work items**

- `lm90_irq_thread()`: does not call `hwmon_notify_event()`. Under the lock,
  `lm90_update_alarms_locked()` sends no event; it schedules `report_work`, and
  `lm90_report_alarms()` sends the events from the work item, without the core
  lock (see "Nesting the core lock").
- `lm90_stop_work()`: the devm action that cancels `alert_work` and
  `report_work`. `lm90_restore_conf()` only writes back the conversion rate
  and config registers.
- `lm90_probe()` order: registration, store `data->hwmon_dev`, add
  `lm90_stop_work()`, request the IRQ. Teardown therefore frees the IRQ,
  stops the work, and only then unregisters the hwmon device.
- **Potentially unsafe usage**: cancelling at teardown a work item that the
  callbacks can schedule.
  - Unsafe: when the hwmon device is still registered at that point and
    nothing stops a callback from scheduling the work again; the work then
    runs after the driver data is freed.
  - Safe: set a flag under the core lock before cancelling and test it where
    the work is scheduled. `lm90_stop_work()` sets `data->shutdown`;
    `lm90_update_alarms_locked()` returns 0 when it is set, and `lm90_alert()`
    tests it before `schedule_delayed_work()`.

**Cached readings**

- `lm90_update_device()` after a failed read: `data->valid` is false (cleared
  before the first read), `data->last_updated` is unchanged, and
  `data->temp[]` can hold a mix of old and new values.
- Only `data->valid` protects readers from that mix, so every callback that
  uses the cache must call `lm90_update_device()` first and return its error;
  all four callers do, the two write helpers included.
- Write paths do not invalidate the cache: `data->valid` is written only in
  `lm90_update_device()`. `lm90_set_temp()`, `lm90_set_temphyst()`,
  `lm90_set_temp_offset()` and `lm90_set_convrate()` update the cached copy
  themselves.
- The limits that `lm90_update_limits()` reads are re-read from the chip only
  while `data->valid` is false, so a write to one of them that skips the
  cached copy stays invisible until a refresh fails.
- `data->alarms`: a bit is cleared by `lm90_temp_read()` when the matching
  alarm attribute is read, and `data->current_alarms` is ORed back in;
  `lm90_report_alarms()` only updates `data->reported_alarms`. The read
  callback therefore writes cached state and relies on the core lock.

## Events, thermal zones and PEC

**Firmware node of the device**

- `__hwmon_device_register()`: the walk starts at the driver's device and
  follows `parent` upward until a device has an `of_node`, not one level.
- Only `of_node` is tested and copied; the assignment is to `hdev->of_node`
  directly.
- `drivers/hwmon/hwmon.c` does not call `device_set_node()` and does not set
  `fwnode`; an ACPI or software node of the parent is not inherited.
- `label`: read with `device_property_present()` and
  `device_property_read_string()` on the driver's device, before the walk; an
  ancestor's `label` is not used.
- `hdev->of_node` NULL: `HWMON_C_REGISTER_TZ` and `HWMON_C_PEC` are both
  ignored without a message and registration succeeds.

**Event notification**

- `dev` that is not a hwmon class device (for example the parent): `WARN()`
  and `-EINVAL` before anything is notified; see `is_hwmon_device()`.
- Return value: 0 or `-EINVAL` only; the attribute name is built in stack
  arrays, so there is no `-ENOMEM`.
- Uevent: sent with `kobject_uevent_env()`, `KOBJ_CHANGE` and one variable
  `NAME=<attribute name>`; its result is dropped.
- Thermal: `hwmon_thermal_notify()` runs for every `attr` of type
  `hwmon_temp`, for example `hwmon_temp_max_alarm`, not only
  `hwmon_temp_input`.
- `channel`: not checked against the chip info.
- `templates[attr]`: not tested for NULL; only the two range checks on `type`
  and `attr` exist.

**Conditions for thermal zones**

- `CONFIG_THERMAL_OF`: tested with `IS_ENABLED()` at the top of
  `hwmon_thermal_register_sensors()` and of `hwmon_thermal_notify()`; there is
  one definition of each, no separate stub.
- No `IS_REACHABLE()` test guards the thermal code; `CONFIG_THERMAL` is `bool`
  in `drivers/thermal/Kconfig`.
- `chip->ops->read` NULL or `hdev->of_node` NULL: the test in
  `__hwmon_device_register()` fails, `HWMON_C_REGISTER_TZ` is ignored and
  registration succeeds with no zones.

**Thermal zone operations**

- `hwmon_thermal_ops`: sets `.get_temp` and `.set_trips` only.
- Locking: `hwmon_thermal_get_temp()` and `hwmon_thermal_set_trips()` hold
  `hwdev->lock` across the driver callback, the same mutex the sysfs paths
  take.
- `hwmon_thermal_set_trips()` lock order: the two early `return 0` cases (no
  `write`, no `hwmon_temp` entry) come before the lock is taken.
- `hwmon_thermal_set_trips()` gate: `HWMON_T_MIN` and `HWMON_T_MAX` in
  `config[tdata->index]` of the first `hwmon_temp` entry; it does not call
  `hwmon_is_visible()`.
- `low` and `high`: passed to `write` unchanged, including the `-INT_MAX` and
  `INT_MAX` that `__thermal_zone_device_update()` starts from; the core does
  not clamp them.
- `write` error in `hwmon_thermal_set_trips()`: `-EOPNOTSUPP` is ignored; any
  other non-zero value is returned at once, so a failed `hwmon_temp_min` write
  skips the `hwmon_temp_max` write.

**PEC attribute**

- `pec_store()`: does not call `i2c_check_functionality()`; that check is made
  once, in `hwmon_pec_register()`.
- Finding the hwmon device: `device_find_child()` on the client device with
  `hwmon_match_device()`; `-ENODEV` if there is none; the reference is dropped
  with `put_device()` on both exits.

**Context for notification**

- Sleeping points: `kernfs_find_and_get_ns()` under `sysfs_notify()` does
  `down_read()`; `kobject_uevent_env()` allocates with `GFP_KERNEL`;
  `thermal_zone_device_update()` takes the zone mutex.
- **Unsafe usage**: calling `hwmon_notify_event()` from a hard interrupt
  handler or any other atomic context; it sleeps at the points above.
  - Safe: from a threaded handler requested with a NULL primary handler, as
    `adt7x10_irq_handler()` is in `adt7x10_probe()`.
  - Safe: from a work item, as `lm90_report_alarms()`.
- **Unsafe usage**: a notifier that can still run while the hwmon device is
  unregistered; `hwmon_thermal_notify()` walks `hwdev->tzdata` with no lock
  and `hwmon_thermal_remove_sensor()` does `list_del()` on it.
  - Safe: stop the work and the interrupt first; in `lm90_probe()` the
    `lm90_stop_work()` devm action and the devm IRQ are added after the devm
    registration, so both are released before `devm_hwmon_release()`
    unregisters the hwmon device.

## Sysfs interface

**Units of values**

- `Documentation/ABI/testing/sysfs-class-hwmon`: holds the `Unit:` lines; some
  entries have none, for example `pwmY` and the alarm flags.
- Name prefix: does not fix the unit; for example `powerY_accuracy` is in
  percent and `powerY_average_interval` in milliseconds.
- `update_interval_us`: microsecond; the ABI entry says a driver that has it
  should also implement `update_interval`.
- Temperature files of chips that measure through a thermistor and an ADC and
  report the measurement as a voltage: hold millivolt, not millidegree
  Celsius; see "Temperatures" in `Documentation/hwmon/sysfs-interface.rst`.
- `hwmon_energy64`: is in `enum hwmon_sensor_types`; it creates the same
  `energy%d_input` file in microJoule and uses the `HWMON_E_INPUT` bits.
- Names with no stated unit: for example `power%d_min` and `power%d_lcrit` in
  `hwmon_power_attr_templates` have no entry in
  `Documentation/ABI/testing/sysfs-class-hwmon` or in
  `Documentation/hwmon/sysfs-interface.rst`.
- `hwmon_thermal_get_temp()` and `hwmon_thermal_set_trips()` in
  `drivers/hwmon/hwmon.c`: pass `hwmon_temp_input`, `hwmon_temp_min` and
  `hwmon_temp_max` values between the driver and thermal with no scaling.

**Alarm and fault attributes**

- `hwmon_attr_show()` in `drivers/hwmon/hwmon.c`: prints the value the callback
  stored; the callback itself has to reduce a status bit to 0 or 1.
- `intrusionY_alarm`: RW in `Documentation/ABI/testing/sysfs-class-hwmon`; it
  sticks until 0 is written, and writing another value is unsupported.
- Regular alarm flags: the `intrusionY_alarm` ABI entry describes them as
  clearing themselves when read.
- Rule that drivers do not compare readings with thresholds: stated in the
  introduction of `Documentation/hwmon/sysfs-interface.rst`, with the reason
  that violations between readings are then caught; nothing in
  `drivers/hwmon/hwmon.c` checks it.
- `pmbus_get_boolean()` in `drivers/hwmon/pmbus/pmbus_core.c`: when the
  boolean has both sensors, compares the reading with the limit, but returns
  1 only if the chip's status bit is also set.
- Fault attribute set to 1: `Documentation/hwmon/sysfs-interface.rst` says only
  that the measurement for that channel should not be trusted; it does not
  require the read of the input attribute to fail.
- `-ENODATA`: named by `Documentation/hwmon/sysfs-interface.rst` and
  `Documentation/ABI/testing/sysfs-class-hwmon` only in the enable entries,
  such as `tempY_enable`, for the read of a sensor that is disabled;
  `tmp421_read()` in `drivers/hwmon/tmp421.c` does this.
- Invalid reading of an enabled sensor: neither document names an error code.
- Error from the callback: `hwmon_attr_show()` returns it unchanged as the
  result of the read.
- Alarm and fault names: the two documents list different sets. The channel
  alarms such as `in[0-*]_alarm`, and `temp[1-*]_fault`, are only in the
  "Alarms" section of `Documentation/hwmon/sysfs-interface.rst`; `inY_fault`,
  `humidityY_fault` and the humidity alarms are only in
  `Documentation/ABI/testing/sysfs-class-hwmon`.

**Attribute permissions**

- "Attribute access" in `Documentation/hwmon/sysfs-interface.rst`: states the
  rule in words, with no octal mode: standard attributes are world readable,
  and writeable ones are writeable only for privileged users.
- RO, RW and WO tags per attribute: in
  `Documentation/ABI/testing/sysfs-class-hwmon`;
  `Documentation/hwmon/sysfs-interface.rst` defines the three abbreviations
  and tags only a few entries.
- Octal modes: `Documentation/hwmon/hwmon-kernel-api.rst` gives 0, 0444 and
  0644 as typical `is_visible` results.
- 0200: named by `Documentation/hwmon/hwmon-kernel-api.rst` only for
  `SENSOR_DEVICE_ATTR_WO()` and `SENSOR_DEVICE_ATTR_2_WO()` in
  `include/linux/hwmon-sysfs.h`.
- Mode with read bits and no matching callback: `hwmon_genattr()` returns
  `-EINVAL` and the registration fails; there is no warning.
- Matching read callback: `read_string` for an attribute that
  `is_string_attr()` matches (the label of each type), `read` for any other.
- Mode with write bits and no `write`: `hwmon_genattr()` returns `-EINVAL`.
- `visible` in `struct hwmon_ops`, in-tree example: `.visible = 0444` in
  `drivers/hwmon/i5500_temp.c`; "Attribute visibility" says how the core uses
  the member.
- Mode bits outside 0664: `create_files()` in `fs/sysfs/group.c` prints a
  `WARN()` and drops them, so 0666 becomes 0664.

**Non-standard attributes**

- `Documentation/hwmon/submitting-patches.rst` on a non-standard attribute:
  create one only if really needed, discuss it on the mailing list first, and
  give a detailed explanation of why it is needed.
- "Standard": `Documentation/hwmon/submitting-patches.rst` defines it as
  specified in `Documentation/hwmon/sysfs-interface.rst`.
- Coverage: neither `Documentation/hwmon/sysfs-interface.rst` nor
  `Documentation/ABI/testing/sysfs-class-hwmon` lists every name in the
  template tables of `drivers/hwmon/hwmon.c`; for example `curr%d_label` and
  `power%d_label` are in neither.
- Documentation of a new attribute:
  `Documentation/hwmon/submitting-patches.rst` asks only that the driver's own
  file under `Documentation/hwmon/` exists and is up to date; no sentence
  requires an entry in `Documentation/ABI/testing/sysfs-class-hwmon` or in
  `Documentation/hwmon/sysfs-interface.rst`.
- debugfs: `Documentation/hwmon/submitting-patches.rst` does not mention it.
- Chip-specific sysfs attributes: `Documentation/hwmon/hwmon-kernel-api.rst`
  gives the `extra_groups` argument of `hwmon_device_register_with_info()` for
  them; `__hwmon_device_register()` puts those groups on the hwmon class
  device, next to the generated attributes.
- Deprecated attributes: `Documentation/hwmon/sysfs-interface.rst` calls only
  `alarms` and `beep_mask` deprecated; `temp[1-*]_type`, `temp[1-*]_crit` and
  `fan[1-*]_div` are standard.
- `alarms`: the core still generates it for `HWMON_C_ALARMS`, and for example
  `drivers/hwmon/lm83.c` sets that bit.
- `beep_mask`: has no template in `drivers/hwmon/hwmon.c`.

**Documentation and the code**

- Invalid name: `Documentation/hwmon/hwmon-kernel-api.rst` says it "will be
  rejected"; `__hwmon_device_register()` only calls `dev_warn()` for an empty
  name or one that contains `-`, `*`, space, tab or newline, and registers the
  device.
- NULL name: the document says the name is then derived from the parent; only
  `devm_hwmon_device_register_with_info()` does that, through
  `devm_hwmon_sanitize_name()` on `dev_name()`.
- `hwmon_sanitize_name()` and `devm_hwmon_sanitize_name()`: return `ERR_PTR()`
  on failure, never NULL; the document does not say so.
- `is_visible`: the document calls it mandatory;
  `hwmon_device_register_with_info()` accepts ops with either `visible` or
  `is_visible` set.
- `struct hwmon_channel_info` listing: shows `u32 *config`; the header has
  `const u32 *config`.
- Sensor types table: lists `hwmon_energy64`, lacks `hwmon_intrusion`; the
  prefix table has no row for `HWMON_INTRUSION_ALARM` and
  `HWMON_INTRUSION_BEEP`.
- NULL `dev` or `chip`: the document states that both must not be NULL, and
  `hwmon_device_register_with_info()` returns `-EINVAL` for either.
- `HWMON_C_REGISTER_TZ` and `HWMON_C_PEC`: the document does not give the
  conditions. `__hwmon_device_register()` honours them only if
  `chip->info[0]` has type `hwmon_chip`, `chip->ops->read` is set, and the
  parent or one of its ancestors has an `of_node`.
- `HWMON_C_REGISTER_TZ` without `CONFIG_THERMAL_OF`:
  `hwmon_thermal_register_sensors()` returns 0 and registers nothing.
- Device-level `label`: the document does not mention it;
  `__hwmon_device_register()` creates it from the firmware property "label" of
  the parent, and fails the registration if the property is present but cannot
  be read as a string.
- `val` of the write callback: the document does not say how it is produced;
  `hwmon_attr_store()` parses with `kstrtol()` in base 10 and returns its error
  before the callback runs, so a string that is not a number never reaches the
  driver as 0.

## I2C chip detection

**Detect functions and probed addresses**

- Addresses allowed by `Documentation/hwmon/submitting-patches.rst`: 0x18-0x1f,
  0x28-0x2f, 0x48-0x4f, 0x58, 0x5c, 0x73 and 0x77; of 0x58-0x5f only 0x58 and
  0x5c are in the set.
- The address list is hwmon policy, not enforced by code: the only address
  range test `i2c_detect_address()` makes before it probes is
  `i2c_check_7bit_addr_validity_strict()`, which accepts 0x08-0x77.
- An entry outside 0x08-0x77: `i2c_detect_address()` returns the error and
  `i2c_detect()` stops, so later entries in the list are not probed on that
  adapter.
- `i2c_default_probe()` runs before `->detect()`: it sends an SMBus quick
  write to the address when the adapter has `I2C_FUNC_SMBUS_QUICK`, except in
  0x30-0x37 and 0x50-0x5f where it uses a receive byte, and under
  `CONFIG_X86` at 0x73 on an `I2C_CLASS_HWMON` adapter with
  `I2C_FUNC_SMBUS_READ_BYTE_DATA`, where it reads a byte; on an adapter with
  `I2C_FUNC_SMBUS_QUICK` any other listed address is therefore written to
  even when detect only reads.
- **Potentially unsafe usage**: listing an address outside the documented set.
  - Unsafe: listed unconditionally; the doc says such probing is known to
    cause trouble with non-hwmon chips, and the device has to be instantiated
    explicitly instead.
  - Safe: `drivers/hwmon/spd5118.c` lists 0x50-0x57 but sets `.detect` and
    `.address_list` only under `CONFIG_SENSORS_SPD5118_DETECT`;
    `spd5118_detect()` only reads, and `i2c_default_probe()` does not quick
    write in that range.
- **Potentially unsafe usage**: writing a chip register in the detect function.
  - Unsafe: before the ID checks have passed, or where a later check can
    still return `-ENODEV`; the doc warns the chip may not be what the driver
    believes and the write may misconfigure it.
  - Safe: after enough reads that detection is certain to succeed, as the
    doc allows; `w83795_detect()` in `drivers/hwmon/w83795.c` writes the bank
    select only after the vendor ID and device ID checks, and has no failure
    return after the write.
- **Potentially unsafe usage**: printing from the detect function.
  - Unsafe: a message above debug level on a mismatch path, such as "chip
    not found/supported"; the doc forbids it because detect runs for every
    driver that lists an address where a chip answered.
  - Safe: debug messages, and a message after a successful detection, both
    allowed by the doc; `w83795_detect()` uses `dev_dbg()` on each mismatch
    and one `dev_info()` on success.
- Detect return value other than 0 or `-ENODEV`: `i2c_detect()` stops scanning
  the remaining addresses for that driver on that adapter, and
  `i2c_do_add_adapter()` discards the error; a failed read is therefore
  turned into `-ENODEV`, as in `nct7802_detect()`.
- Client passed to detect: `i2c_detect()` allocates it zeroed and sets only
  `adapter` and `addr`, so `client->dev` and `client->name` are empty;
  `w83795_detect()` logs through `&adapter->dev`.
- When to provide detect: the doc's condition is "if and only if a chip can be
  detected reliably"; it does not make the absence of a firmware description
  a condition, it only says explicit instantiation is always better.
- Adapters that run detection are not only PC SMBus hosts: for example
  `drivers/i2c/busses/i2c-gpio.c` sets `I2C_CLASS_HWMON` unconditionally;
  search `drivers/` for `I2C_CLASS_HWMON` for the rest.
- There is no I2C_CLIENT_AUTO flag here: `i2c_detect_address()` links
  `client->detected` onto `driver->clients`, and `i2c_do_del_adapter()`
  unregisters those clients when the driver or the adapter goes away.

## PMBus core

**PMBus files**

- `struct pmbus_platform_data` and the `PMBUS_SKIP_STATUS_CHECK`-style flags:
  defined in `include/linux/pmbus.h`, not in `drivers/hwmon/pmbus/pmbus.h`.
- `struct pmbus_sensor`, `struct pmbus_boolean`, `struct pmbus_label`,
  `struct pmbus_data`: private to `drivers/hwmon/pmbus/pmbus_core.c`; a chip
  driver cannot reach them.
- Regulator, debugfs, thermal and interrupt code: all inside `pmbus_core.c`;
  the regulator part is under `#if IS_ENABLED(CONFIG_REGULATOR)`. There is no
  separate regulator file.
- `pmbus_do_probe()`: stores the `struct pmbus_driver_info` pointer
  (`data->info = info`), it does not copy. The struct must live as long as the
  device.
- The info is written during `pmbus_do_probe()`: `identify` receives it
  non-const, and with `PMBUS_USE_COEFFICIENTS_CMD` `pmbus_init_coefficients()`
  fills `m[]`, `b[]`, `R[]`. A static info is shared by every device the
  driver binds.
- Second hand-over channel: the chip driver sets `dev->platform_data` to a
  `struct pmbus_platform_data` before `pmbus_do_probe()`; the core reads it
  with `dev_get_platdata()` into `data->flags`. See `pmbus_probe()` in
  `drivers/hwmon/pmbus/pmbus.c`.
- Client data: `pmbus_do_probe()` calls `i2c_set_clientdata()` with its own
  `struct pmbus_data`. A chip driver embeds the info in its private struct and
  recovers it with `pmbus_get_driver_info()` plus `container_of()`, as
  `to_isl68137_data()` does.
- `struct pmbus_driver_info` members that are easy to miss: the
  `write_byte_data` callback, the `ieee754` value of
  `enum pmbus_data_format`, and `have_pmbus_revision` with `pmbus_revision`
  for chips without `PMBUS_REVISION`.
- `pmbus_do_probe()` returns `-ENODEV` when `info` is NULL, when the adapter
  lacks byte/word SMBus functionality, or when `info->pages` is outside
  1..`PMBUS_PAGES` after `identify` ran. `pages` may be 0 on entry only if
  `identify` sets it.
- `Documentation/hwmon/pmbus-core.rst`: does not describe `pmbus_lock()`,
  `write_byte_data`, `groups` or the delay fields. Take the API from
  `drivers/hwmon/pmbus/pmbus.h`.
- There is no pmbus_do_remove here; what the core sets up is device-managed,
  except its debugfs files, which sit in `client->debugfs` and go when the
  I2C core removes that directory. A chip driver needs `remove` only for what
  it started itself.

**PMBus registration path**

- `pmbus_do_probe()` calls `devm_hwmon_device_register_with_groups()`, not
  `devm_hwmon_device_register_with_info()`.
- `drivers/hwmon/pmbus/` contains no `struct hwmon_chip_info`,
  `struct hwmon_channel_info` or `struct hwmon_ops`. A patch that adds
  `is_visible`/`read`/`write` ops to a PMBus chip driver has nothing to attach
  them to.
- Attribute type: `struct sensor_device_attribute` embedded in the private
  sensor, boolean, label and samples structs. `index` is -1 for all but
  booleans, where it packs page, register and status mask; see
  `pb_reg_to_index()`.
- Zero attributes found: `pmbus_do_probe()` returns `-ENODEV` and registers
  no hwmon device.
- Thermal zones: registered by the PMBus core itself, not by the hwmon core.
  `pmbus_add_sensor()` calls `pmbus_thermal_add_sensor()` for each
  `PSC_TEMPERATURE` sensor of type "input".
- Thermal ordering: the zone exists before the hwmon device does.
  `pmbus_thermal_get_temp()` reports 0 and touches no register while
  `data->hwmon_dev` is NULL.
- Callbacks in a chip driver's `info->groups`: `dev` is the hwmon device. The
  client is `to_i2c_client(dev->parent)`, as in `isl68137_avs_enable_show()`.
  The hwmon device's drvdata is the core's private `struct pmbus_data`.
- `pec` attribute: created with `device_create_file()` on the I2C client
  device in `pmbus_init_common()`, only when `I2C_CLIENT_PEC` ended up set. It
  is not part of the hwmon groups.

**PMBus locking**

- `pmbus_lock()`: exists, exported, non-interruptible `mutex_lock()` on
  `update_lock`.
- `DEFINE_GUARD(pmbus_lock, ...)` in `drivers/hwmon/pmbus/pmbus.h`:
  `guard(pmbus_lock)(client)` and `scoped_guard(pmbus_lock, client)` are the
  forms the core uses at every lock site.
- `pmbus_lock_interruptible()`: has no guard class; pair it with
  `pmbus_unlock()` by hand.
- Exported accessors take no lock: for example `pmbus_set_page()`,
  `pmbus_read_word_data()`, `pmbus_write_byte()`, `pmbus_update_byte_data()`,
  `pmbus_update_fan()`, `pmbus_clear_faults()`,
  `pmbus_check_word_register()`.
- Exported entry points that take the lock themselves:
  `pmbus_check_and_notify_faults()` and the functions in
  `pmbus_regulator_ops`.
- Probe-time calls run without the lock: `pmbus_do_probe()` holds nothing
  around `pmbus_init_common()` (which calls `identify`) and
  `pmbus_find_attributes()`. A callback therefore runs unlocked from those
  two functions and locked at run time.
- Nothing asserts the lock: `drivers/hwmon/pmbus/` has no
  `lockdep_assert_held()`. A missing lock fails silently as a wrong-page
  access.
- hwmon core lock: `hwmon_attr_show()`, `hwmon_attr_show_string()` and
  `hwmon_attr_store()` in `drivers/hwmon/hwmon.c` hold the hwmon device's
  mutex around `struct hwmon_ops` callbacks. PMBus attributes are plain group
  attributes and never pass through them.
- `hwmon_lock()`: locks that same hwmon-device mutex, a different mutex from
  `update_lock`. Nothing in `drivers/hwmon/pmbus/` calls it, and holding it
  does not exclude the PMBus core.
- `drivers/hwmon/pmbus/ucd9000.c`: contains no call to the lock helpers; it is
  not an example of the locking pattern.
- **Unsafe usage**: taking `update_lock` from code the core runs with the
  lock held.
  - Unsafe: `pmbus_lock()`, `pmbus_lock_interruptible()`,
    `pmbus_check_and_notify_faults()` or a `pmbus_regulator_ops` function
    called from a `struct pmbus_driver_info` read/write callback. The mutex
    is not recursive and `pmbus_show_sensor()` already holds it; the task
    deadlocks.
  - Safe: a callback calls the unlocked accessors, as
    `ibm_cffps_read_word_data()` does.
  - Safe: `pmbus_check_and_notify_faults()` from a context that holds no
    PMBus lock, as `mpq8646_alarm_poll_work()` does.
- **Potentially unsafe usage**: reaching the chip from a chip driver's own
  entry point (sysfs group, debugfs, GPIO, LED, nvmem, work item) without
  `update_lock`, once `pmbus_do_probe()` has returned.
  - Unsafe: on a chip with more than one page or with phases:
    `pmbus_set_page()` skips the PAGE write when `currpage` matches, and
    reads and writes `currpage`/`currphase` unlocked. A concurrent core
    access lands on the wrong page.
  - Safe: bracket the whole sequence with the lock, as
    `isl68137_avs_enable_store_page()` (interruptible, result checked) and
    `adm1266_gpio_get()` (guard) do.
  - Safe: one `i2c_smbus_read_byte_data()`-style transfer on a chip whose
    info has `pages` 1 and no `phases`, as `ipsps_mode_show()` in
    `drivers/hwmon/pmbus/inspur-ipsps.c`; `pmbus_set_page()` writes PAGE
    only when `info->pages > 1`.
- **Unsafe usage**: calling `pmbus_lock()`, `pmbus_lock_interruptible()` or
  `pmbus_unlock()` before `pmbus_do_probe()`.
  - Unsafe: the helpers dereference `i2c_get_clientdata()`, which is NULL
    until `pmbus_do_probe()` sets it.
  - Safe: lock only after `pmbus_do_probe()` succeeded, as
    `adm1266_probe()` does when it calls `adm1266_rtc_set()`.

## Changing the core

**Adding an attribute**

- Table names: there is no hwmon_attr_templates or __hwmon_attr_templates
  array; the per-type tables are gathered in `__templates` and their sizes
  in `__templates_size`, both in `drivers/hwmon/hwmon.c`.
- `__templates` and `__templates_size`: two separate arrays indexed by
  `enum hwmon_sensor_types`; a new type needs an entry in each, and nothing
  checks that they agree.
- Build-time checks: `drivers/hwmon/hwmon.c` has no `BUILD_BUG_ON()` and no
  `static_assert()` that ties an enumeration to its table.
- Errors from `hwmon_genattr()` other than `-ENOENT`: fail the whole
  registration.
- Sensor type inside `__templates` with a `__templates_size` entry of 0:
  every bit of that type is skipped.
- `hwmon_chip_attrs`: holds complete file names, not formats;
  `hwmon_genattr()` uses the string as the name for `hwmon_chip`.
- `hwmon_notify_event()`: indexes the same two arrays; returns `-EINVAL`
  for an index at or beyond the size, and passes a NULL slot to
  `scnprintf()` as the format without a test.
- `is_string_attr()`: must list a new label attribute for each type that
  has it; `hwmon_energy64` has its own line.
- Attribute missing from `is_string_attr()`: is shown by `hwmon_attr_show()`
  through `ops->read` as a number.
- `hwmon_energy64`: shares `enum hwmon_energy_attributes`, the macros
  `HWMON_E_ENABLE`, `HWMON_E_INPUT` and `HWMON_E_LABEL`, and
  `hwmon_energy_attr_templates` with `hwmon_energy`; a new energy
  attribute applies to both types.
- `hwmon_attr_show()`: passes the address of an `s64`, cast to `long *`,
  for `hwmon_energy64`; a new type wider than `long` needs the same
  handling there.
- Limit: 32 attributes per type, since `config` in
  `struct hwmon_channel_info` is `const u32 *`.
- `enum hwmon_power_attributes`: has 31 values, so one bit is left.
- `hwmon_max`: must stay the last value of `enum hwmon_sensor_types`;
  drivers size arrays by it, for example `ps_type_attrs` in
  `drivers/power/supply/power_supply_hwmon.c`.
- `Documentation/ABI/testing/sysfs-class-hwmon`: holds the full description
  of the attributes it lists, each under a `What:` line.
- `Documentation/hwmon/hwmon-kernel-api.rst`: has a table of sensor types
  and a table of macro prefixes, and no list of attributes; it changes for
  a new type, not for a new attribute.

**Unwinding a failed registration**

- Label `free_hwmon`: calls `hwmon_dev_release(hdev)` directly, then falls
  into `ida_remove`; there are no separate `kfree()` calls in the unwind.
- Label `ida_remove`: every failure path after `ida_alloc()` ends there;
  `hwmon_dev_release()` does not call `ida_free()`.

| Failure | Frees device and attributes | `goto` label |
|---|---|---|
| `kzalloc_obj()` of the device | nothing to free | `ida_remove` |
| `kzalloc_objs()` of `hwdev->groups` | `hwmon_dev_release()`, direct | `free_hwmon` |
| `__hwmon_create_attrs()` | `hwmon_dev_release()`, direct | `free_hwmon` |
| `"label"` property read or `kstrdup()` | `hwmon_dev_release()`, direct | `free_hwmon` |
| `device_register()` | `put_device()`, which runs the release | `ida_remove` |
| `hwmon_thermal_register_sensors()` | `device_unregister()` | `ida_remove` |
| `hwmon_pec_register()` | `device_unregister()` | `ida_remove` |

- `__hwmon_create_attrs()` failure: it has already called
  `hwmon_free_attrs()` on its array if it allocated one, and
  `hwdev->group.attrs_const` is assigned only on success, so the direct
  release does not free the attributes a second time.
- `hwmon_dev_release()`: reads `hwdev->group.attrs_const`, not
  `hwdev->group.attrs`; the two are a union in `struct attribute_group`.
- `dev_set_name()`: allocates the kobject name, which
  `hwmon_dev_release()` does not free; a failure path added after it cannot
  use `free_hwmon`.

**Finding the id at removal**

- The parse of `dev_name()` against `HWMON_ID_FORMAT` is the only test:
  `hwmon_device_unregister()` does not call `is_hwmon_device()` and does
  not compare `dev->class` with `hwmon_class`.
- **Unsafe usage**: calling `hwmon_device_unregister()` on a device from
  `devm_hwmon_device_register_with_info()` or
  `devm_hwmon_device_register_with_groups()`; `devm_hwmon_release()` calls
  it again on the same pointer, after `device_unregister()` dropped the
  reference and `hwmon_dev_release()` may have freed the device.
  - Safe: register with `hwmon_device_register_with_info()` and unregister
    once by hand, as `arctic_fan_probe()` and `arctic_fan_remove()` in
    `drivers/hwmon/arctic_fan_controller.c` do; only the devm functions add
    `devm_hwmon_release()`.

**Attribute memory**

- `hwmon_free_attrs()`: makes no test of ownership; it does not look at the
  `show` callback or at the name.
- Ownership is by location: `hwmon_dev_release()` passes only
  `hwdev->group.attrs_const` to `hwmon_free_attrs()`.
- `hwdev->group`: the one group the core builds; it is embedded in
  `struct hwmon_device`, not allocated, and freed with the device.
- `hwmon_free_attrs()`: applies `to_hwmon_attr()` and `kfree()` to every
  entry, so every pointer in that array must come from `hwmon_genattr()`.
- `hwmon_free_attrs()`: dereferences the array without a NULL test;
  `hwmon_dev_release()` tests `hwdev->group.attrs_const` before the call.
- Attribute name: points into the `name` buffer of
  `struct hwmon_device_attribute`, except for `hwmon_chip`, where it points
  at the static string in `hwmon_chip_attrs`.
- Allocation calls: `kzalloc_obj()` in `hwmon_genattr()`, `kzalloc_objs()`
  for the array in `__hwmon_create_attrs()` and for `hwdev->groups` in
  `__hwmon_device_register()`; the core does not call `kzalloc()` or
  `kcalloc()` for these.
- Field names: the core writes `attrs_const` in `struct attribute_group`
  and `show_const` and `store_const` in `struct device_attribute`, not
  `attrs`, `show` and `store`.

## Conventions

**Conventions for new code**

These are conventions that the maintainers of the hardware monitoring subsystem
ask of new code. Existing code may differ. A kernel tree cannot supply all of
them, so they are kept by hand and inserted as they are.

- Code must follow the guidelines in
  `Documentation/hwmon/submitting-patches.rst`.
- Enum values in this subsystem are traditionally lowercase. Uppercase is
  permitted, but not mandatory.
- Hardware monitoring is an API in Linux, not just a physical layout. Hardware
  monitoring drivers should reside in the `drivers/hwmon/` directory.
- In a new driver, registering hardware monitoring devices from outside
  `drivers/hwmon/` violates layering and increases driver complexity.
- If the main functionality of a chip is not hardware monitoring (such as
  network interface controllers, DRM controllers, or platform specific
  multi-function devices), its hardware monitoring functionality should be
  implemented as an auxiliary device driver, and that hardware monitoring
  driver should reside in `drivers/hwmon/`.
- A hardware monitoring device that supports secondary functionality (such as
  GPIO or LED) should be implemented as a hardware monitoring driver. The
  secondary functionality should be implemented as an auxiliary device, with
  its driver residing in the directory of the appropriate subsystem.
- New drivers must use `hwmon_device_register_with_info()` or
  `devm_hwmon_device_register_with_info()` to register with the hardware
  monitoring subsystem.
- Drivers should use `hwmon_lock()` and `hwmon_unlock()` for the locking that
  the driver itself must implement: the locking for interrupt handling, and
  the locking for attributes registered by any means other than the `info`
  parameter of those two registration functions.

## Model gaps

### Other mistakes models make

- Models take the comment above `hwmon_match_device()` in
  `drivers/hwmon/hwmon.c` at its word; it still describes a single mutex
  for PEC. `pec_store()` takes `hwdev->lock` of the hwmon child, and the
  file defines no global mutex.
- Models expect non-const sysfs handler arguments in the core.
  `hwmon_attr_show()`, `hwmon_attr_show_string()`, `hwmon_attr_store()` and
  `pec_store()` take `const struct device_attribute *`, and
  `hwmon_dev_attr_group` sets `is_visible_const`; see
  `include/linux/device.h` and `include/linux/sysfs.h`.
- Models do not know `HWMON_C_UPDATE_INTERVAL_US`. It is in
  `include/linux/hwmon.h` and creates `update_interval_us`.
- Models take every `hwmon_lock` to be the core helper. Several drivers have
  a private mutex member of that name, for example in
  `drivers/hwmon/da9052-hwmon.c` and `drivers/hwmon/occ/common.h`.
- Models take PMBus to get events from the hwmon core. It notifies through
  `pmbus_notify()`, which calls `sysfs_notify()` and `kobject_uevent()`; it
  does not call `hwmon_notify_event()`.

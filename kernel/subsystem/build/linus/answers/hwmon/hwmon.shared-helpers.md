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

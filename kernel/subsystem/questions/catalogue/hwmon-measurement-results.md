# What the hwmon measurement found

Three models were asked the 66 questions in `hwmon-measurement.md` with no
sources. A checker that had the sources then corrected each answer against a
mainline tree (kernel 7.3.0-rc5). The readers are labelled A, B and C. Which
models they were does not matter here.

- Reader A needed 263 corrections, and the check rewrote 18% of its answers.
- Reader B needed 225 corrections, and the check rewrote 25% of its answers.
- Reader C needed 282 corrections, and the check rewrote 45% of its answers.

The hand-written guide was never checked against current sources, so
differences between it and the built guide are expected. The section "Where
the hand-written guide is stale" lists them.

All three readers know the shape of the subsystem: the two registration
functions for new drivers, the channel description, the callbacks, and that
the core creates the sysfs files. What they get wrong is the detail a review
depends on: when the core holds its lock, which conditions switch on thermal
zones and the `pec` attribute, what the code does with a bad name or a stray
bit, and what the documents say as opposed to what the readers remember them
saying.

A kernel name in backticks exists in the tree. A kernel name without backticks
does not.

## What all three readers got wrong

- **Calling `hwmon_notify_event()` with the core lock held.** Readers A and B
  said that this is safe. Reader C said that the notify path takes no core
  lock. For a `hwmon_temp` channel with a thermal zone attached,
  `hwmon_notify_event()` calls `hwmon_thermal_notify()`, which calls
  `thermal_zone_device_update()`, which reaches `hwmon_thermal_get_temp()`.
  That function takes the lock of the hwmon device, so the caller deadlocks.
- **The conditions for thermal zones and for `pec`.** Each reader gave a
  different, incomplete set. Reader A named a test of
  `IS_REACHABLE(CONFIG_THERMAL)` and a global mutex called hwmon_pec_mutex.
  Reader B said that `pec` needs a `write` callback and that the parent device
  must have a device tree node. Reader C said that the position of the
  `hwmon_chip` entry does not matter. In the tree one test in
  `__hwmon_device_register()` guards both `HWMON_C_REGISTER_TZ` and
  `HWMON_C_PEC`: the hwmon device has an `of_node`, the driver has a `read`
  callback, and `info[0]` has the type `hwmon_chip`. The `of_node` comes from
  the nearest ancestor that has one. `hwmon_thermal_register_sensors()` also
  needs `CONFIG_THERMAL_OF`, and registers a channel only if the channel has
  `HWMON_T_INPUT` and is visible.
- **What `pec_store()` does.** No reader had the order right. `pec_store()`
  calls `write` only if the driver has one, under the lock of the hwmon
  device. It ignores `-EOPNOTSUPP`, and it changes the flags of the I2C client
  after the call. `hwmon_pec_register()` returns 0 and creates no file when the
  adapter lacks `I2C_FUNC_SMBUS_PEC`, and returns `-EINVAL` when the parent is
  not an I2C client.
- **A NULL name.** Readers B and C said that both registration functions
  reject a NULL name. Reader A said that only
  `hwmon_device_register_with_groups()` accepts one.
  `hwmon_device_register_with_info()` and `hwmon_device_register_with_groups()`
  return `ERR_PTR(-EINVAL)`. `devm_hwmon_device_register_with_info()` derives a
  name with `devm_hwmon_sanitize_name()`.
- **devm_hwmon_device_unregister.** Every reader named it in at least one
  answer. No such function exists in the tree. `devm_hwmon_release()` is the
  release function of the managed registration.
- **What `hwmon_notify_event()` checks.** No reader had the first test:
  `is_hwmon_device()` under `WARN()`, which returns `-EINVAL`. The function
  then checks the range of the type and of the attribute, and returns 0.
- **Names in the core that changed.** Every reader wrote `container_of()` for
  `to_sensor_dev_attr()`, and `kzalloc()` and `kcalloc()` for the allocations
  of the core. Readers A and B wrote `attrs` for the member of the attribute
  group. The tree has `container_of_const()`, `kzalloc_obj()`,
  `kzalloc_objs()` and `attrs_const`.
- **Which written values a driver limits.** Readers A and B put `pwm` values
  among the values that a driver limits to the nearest supported value, and
  reader C gave examples that the document does not name.
  `Documentation/hwmon/sysfs-interface.rst` names only continuous settings
  such as `tempX_max` and `inX_max`, and `pwm_fan_write()` returns `-EINVAL`
  for a value out of range.
- **What the documents say.** Every reader attributed a rule to the hwmon
  documents that they do not hold. Readers A and B said that
  `Documentation/hwmon/submitting-patches.rst` has a rule on the range of
  written values, and it has none. Every reader said that chip-specific values
  go in debugfs, and no document says so. Every reader said that a new
  attribute name must be added to the sysfs documents, and no hwmon document
  says so. The documents name `-ENODATA` only for a sensor that is disabled
  through its enable attribute, and readers A and C gave that code for any
  reading that is not valid.
- **Where the kernel API document differs from the code.** All three were weak
  on `hwmon.doc-versus-code`, and readers B and C guessed. The document says
  that a bad name "will be rejected", and the code only warns. The document
  shows `struct hwmon_ops` without `visible` and `read_string`, and calls
  `is_visible` mandatory. The document shows the `config` member of
  `struct hwmon_channel_info` without the const that the header has. The
  document lists no intrusion sensor type.
- **I2C detection.** Every reader stated the rules more strictly than the
  document does. The document says to avoid writes in a detect function, and
  allows a write once the detection is certain. The document gives a fixed
  list of addresses and calls other addresses strongly discouraged, and
  `drivers/hwmon/spd5118.c` lists 0x50 to 0x57.
- **PMBus locking.** Readers A and B did not recognise `pmbus_lock()`, and
  reader C was unsure of `pmbus_lock_interruptible()`. Both exist, and so does
  a `pmbus_lock` guard, which the core itself uses. No reader said that the
  callbacks of a chip driver run without the lock during `pmbus_do_probe()`.

## What only some readers got wrong

Readers B and C:

- **A bit with no name.** Both said that a bit beyond the table of names
  fails registration with `-EINVAL`. `hwmon_genattrs()` skips such a bit with
  no warning. Only a sensor type beyond `__templates` gives `-EINVAL`.
- **Where the units are.** Both called
  `Documentation/hwmon/sysfs-interface.rst` the authority on units. That file
  has a "Unit:" line for four attributes. The units are in
  `Documentation/ABI/testing/sysfs-class-hwmon`.
- **The `chip` argument.** Both said that `chip` may be NULL for
  `hwmon_device_register_with_info()`. The function returns
  `ERR_PTR(-EINVAL)`.
- **Limit, then convert.** Both said that a `write` callback must limit a
  value before any conversion. The example in the document divides before it
  calls `clamp_val()`. Only a multiplication, an addition or a subtraction
  must come after the limit.
- **`hwmon_thermal_set_trips()`.** Reader B said that the function tests
  visibility, and reader C that it calls `read` and ignores an error. The
  function calls `write` only, tests the `HWMON_T_MIN` and `HWMON_T_MAX` bits,
  and returns any error other than `-EOPNOTSUPP`.

Readers A and B:

- **`lm75_alarm_handler()`.** Both said that the handler reads a register
  before it notifies. The handler only calls `hwmon_notify_event()`.
- **`drivers/hwmon/sht4x.c`.** Both said that the driver takes a mutex of its
  own in its extra attributes. The driver uses the `hwmon_lock` guard.
- **PMBus attributes.** Both said that the core creates an attribute only if
  the chip answers for its register. The core checks the register with
  `pmbus_check_word_register()` for limits, fans and samples only.

Reader A only:

- Requesting an interrupt after registration is unsafe. `lm90_probe()`
  registers the hwmon device, then adds the action that stops its work, then
  requests the interrupt, since the handler needs the hwmon device.
- A guard that tests `CONFIG_HWMON` with the preprocessor, with no Kconfig
  dependency, is unsafe. The guard is true only when hwmon is built in, so
  the guard is safe.
- lm75_probe. The function is `lm75_generic_probe()`.
- The pattern in `MAINTAINERS` matches the context lines of a patch.
  `scripts/get_maintainer.pl` matches it against added and removed lines.

Reader B only:

- `hwmon_device_register()` no longer exists. The function is defined,
  exported and declared, and drivers still call it.
- hwmon_num_attrs. The counter is `hwmon_num_channel_attrs()`.
- The core sets the release function of the device. The tree sets
  `dev_release` in `hwmon_class`.
- The kernel API document tells drivers to serialize their callbacks. The
  document says that the core serialises them.
- The divisor of `DIV_ROUND_CLOSEST()` must be positive. The macro handles a
  negative divisor when both types are signed.

Reader C only:

- **Stubs in the header.** Reader C said that `include/linux/hwmon.h` has
  inline stubs when `CONFIG_HWMON` is disabled. The header has none, so a
  driver must compile the call out or depend on hwmon.
- **`select HWMON`.** Reader C said that a driver must not select it. Several
  Kconfig files in the tree do.
- **The device passed to callbacks.** In one answer reader C said that the
  callbacks receive the parent device. The callbacks receive the hwmon device.
- **Bad names.** Reader C said that `__hwmon_device_register()` calls
  `hwmon_is_bad_char()`, tests for a slash and returns `ERR_PTR(-EINVAL)`. The
  function tests with `strpbrk()` and only warns. `hwmon_is_bad_char()` has no
  case for a slash, and only the sanitize helpers call it.
- **The lock on the thermal path.** Reader C listed the thermal operations
  among the callers that hold no lock. Both operations take the lock.
- **`hwmon_lock()` after `hwmon_device_register_with_groups()`.** Reader C
  said that the helpers do not work. The core initialises the mutex for every
  registration.
- **PMBus registration.** Reader C said that `pmbus_do_probe()` calls
  `devm_hwmon_device_register_with_info()`. The function calls
  `devm_hwmon_device_register_with_groups()`. Reader C also named helper
  variants with a "_do_" prefix, which do not exist, and said that
  `pmbus_read_word_data()` takes the lock, which the function does not.
- **`hwmon_device_unregister()`.** Reader C said that the function tests the
  class of the device and logs an error. The function tests only the result of
  `sscanf()` on the name, and logs at debug level. On failure the device stays
  registered.
- **Attribute names.** Reader C said that a name that does not fit gives an
  error. `hwmon_genattr()` truncates the name with no warning.
- **Names that do not exist.** HWMON_C_KERNEL_DEFINED, hwmon_chip_label,
  hwmon_energy_attr and I2C_CLIST_END. Reader C also gave linear11 as a value
  of `enum pmbus_data_format`, which has no such value.
- **Printed values.** Reader C gave the format of a value as a long, and for
  `hwmon_energy64` as unsigned. `hwmon_attr_show()` prints a signed 64-bit
  value.

## What the readers already knew

- that new drivers register with `hwmon_device_register_with_info()` or
  `devm_hwmon_device_register_with_info()`, and that the other functions are
  deprecated
- how the core parses a written value, and what a write returns for text that
  is not a number
- that a zero word ends a `config` array and a NULL ends the `info` array
- that the core keeps pointers to the name and to the chip description, and
  copies neither
- that the core creates the attributes of `extra_groups` on the hwmon device,
  and holds no lock around them
- the `label` property of the device
- how the channel number relates to the sensor index of a thermal zone
  (readers A and B)
- how the core builds an attribute name, and the number that each sensor type
  counts from (readers A and B)

## Where the hand-written guide is stale

`hwmon.md` is short. Every function and path that it names exists in the tree.
It is incomplete more than stale.

- It says that registering from outside `drivers/hwmon/` "bypasses maintainer
  review". `MAINTAINERS` has a `K:` pattern for the registration functions, so
  a patch that adds or removes a registration call anywhere in the tree goes
  to the hwmon maintainer and list. The conventions file leaves this clause
  out.
- It says that the core serializes thermal and sysfs operations. That is true
  in the tree. It does not say that `pec_store()` holds the same lock, that
  `is_visible` runs without the lock, or that `hwmon_notify_event()` reaches
  the lock again through the thermal core.
- It says that drivers should use `hwmon_lock()` and `hwmon_unlock()` for the
  locking that the core does not do. `Documentation/hwmon/hwmon-kernel-api.rst`
  says only that the functions "can be used", and the PMBus core has a lock of
  its own. The conventions file keeps the sentence as a convention for new
  code.
- Its section "Arithmetic" tells a reviewer what to check and states no fact.
  The questions `hwmon.write-range` and `hwmon.conversion-arithmetic` ask for
  the requirements.
- No hwmon document states its rules on lowercase enum values, on the
  directory a driver belongs in, or on auxiliary devices. A search of
  `Documentation/hwmon/` for "lowercase" finds nothing. Neither
  `Documentation/hwmon/submitting-patches.rst` nor
  `Documentation/hwmon/hwmon-kernel-api.rst` mentions an auxiliary device or
  the directory. The build inserts these rules from
  `../../verbatim/hwmon-conventions.md`.
- It says nothing about the channel description, the callbacks, events,
  thermal zones, the `pec` attribute, the sysfs interface or PMBus.

## What was left out of the build set and why

The build set has 53 questions: 51 picked from the measurement set,
`hwmon.overview` and `hwmon.model-gaps`. It also has one item that inserts the
conventions. Fourteen measurement questions are left out.

Left out because every reader answered correctly, or nearly:

| Question | Rewritten, A / B / C | What the corrections were |
|---|---|---|
| `hwmon.write-parsing` | 0% / 0% / 8% | the name of a pointer |
| `hwmon.device-label` | 3% / 0% / 18% | which test hides the file |
| `hwmon.channel-arrays` | 16% / 24% / 4% | one function name that does not exist; the rule was right |
| `hwmon.name-lifetime` | 19% / 4% / 25% | a second error value of the sanitize helper |
| `hwmon.chip-info-lifetime` | 15% / 26% / 20% | which function reads the arrays again |
| `hwmon.thermal-channel-index` | 0% / 0% / 36% | a log message |
| `hwmon.sensor-types` | 15% / 12% / 22% | the name of one enumeration. `hwmon.energy64` and `hwmon.new-attribute` ask about the shared tables |
| `hwmon.extra-groups` | 13% / 12% / 27% | the lock of one driver. `hwmon.core-lock` and `hwmon.lock-helpers` ask about the lock |
| `hwmon.read-contract` | 18% / 16% / 35% | the print format. `hwmon.energy64` asks about the width |

Left out because the answer would not change a review:

| Question | Why |
|---|---|
| `hwmon.tracing-tests` | relevance 2. The corrections are the type of the traced value and that the tree has no test of the core |
| `hwmon.sensor-attr-macros` | the corrections are `container_of_const()` and the arguments of one macro |
| `hwmon.thermal-legacy` | relevance 2. One caller, and `hwmon.register-variants` asks which functions are restricted |

Merged into another question:

| Question | Now asked by |
|---|---|
| `hwmon.legacy-register` | `hwmon.register-variants`, which asks what each deprecated function does differently |
| `hwmon.thermal-failure` | `hwmon.register-unwind`, which asks about every failure path of `__hwmon_device_register()` |

## Questions reorganised

The build set is organised by subject. Each part has one section, so one call
to the builder answers the questions of a part together.

| Part | Questions |
|---|---|
| Main structures | 1 |
| Where to look | 3 |
| Hwmon devices in other subsystems | 2 |
| Class device and attribute names | 4 |
| Registration | 6 |
| Channel description | 4 |
| Driver callbacks | 7 |
| Locking | 6 |
| Events, thermal zones and PEC | 6 |
| Sysfs interface | 5 |
| I2C chip detection | 1 |
| PMBus core | 3 |
| Changing the core | 4 |
| Conventions | none: one inserted file |
| Model gaps | 1 |

What changed in the questions that were picked:

- `hwmon.overview` has the text that every build set uses for its first
  question.
- `hwmon.core-lock` asked "which lock does the core hold". It now asks
  whether the core holds a lock, and which, since the hand-written guide
  states that the core serializes.
- `hwmon.firmware-node` moved from registration to the part on thermal zones,
  since thermal zones and `pec` are what depend on the node.
- `hwmon.callers-elsewhere` and `hwmon.build-deps` moved from "Where to look"
  to a part of their own.
- Three titles changed: `hwmon.chip-flags`, `hwmon.lock-nesting` and
  `hwmon.i2c-detection`.
- The reason on `hwmon.pmbus-registration` changed, since the old reason held
  the answer.

Every other question has the id and the text that it has in the measurement
set.

## The numbers

The share of each answer from memory that the check rewrote, with the number
of corrections in brackets. "Rewritten" counts rewording too, so the
corrections are what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          263        18%     31      2   6.12 to 6.19
reader B          225        25%     19     10   6.12 to 6.17
reader C          282        45%      4     43   6.12 to 6.15

question                          reader A      reader B      reader C   verdict
hwmon.core-files                  23% ( 7)      20% ( 2)      22% (16)   middling
hwmon.docs                        15% ( 3)      41% ( 5)      35% ( 2)   weak: reader B
hwmon.shared-helpers              21% ( 3)      19% ( 1)      48% ( 4)   weak: reader C
hwmon.callers-elsewhere           36% ( 4)      45% ( 2)      62% ( 3)   weak: reader B, reader C
hwmon.build-deps                  22% ( 7)      39% ( 4)      65% ( 5)   weak: reader C
hwmon.tracing-tests               18% ( 3)      12% ( 2)      57% ( 3)   weak: reader C
hwmon.overview                     7% ( 8)       0% ( 1)      41% ( 9)   weak: reader C
hwmon.class-device                 3% ( 1)      37% ( 9)      43% ( 6)   weak: reader C
hwmon.sensor-types                15% ( 5)      12% ( 2)      22% ( 3)   middling
hwmon.config-macros               10% ( 3)      21% ( 1)      66% ( 3)   weak: reader C
hwmon.attr-names                   1% ( 1)      10% ( 2)      65% ( 3)   weak: reader C
hwmon.chip-flags                  12% ( 5)      32% ( 5)      87% ( 7)   weak: reader C
hwmon.register-variants           10% ( 9)      23% (10)      28% ( 3)   middling
hwmon.register-args               10% ( 2)      30% ( 2)      53% ( 4)   weak: reader C
hwmon.name-rules                  34% ( 2)      38% ( 2)      55% ( 6)   weak: reader C
hwmon.name-lifetime               19% ( 1)       4% ( 1)      25% ( 3)   middling
hwmon.chip-info-lifetime          15% ( 2)      26% ( 2)      20% ( 1)   middling
hwmon.probe-order                 29% ( 2)      40% ( 2)      36% ( 2)   weak: reader B
hwmon.unregister-order            12% ( 1)      15% ( 1)      24% ( 2)   middling
hwmon.callback-device             37% ( 1)      26% ( 1)       0% ( 1)   middling
hwmon.extra-groups                13% ( 1)      12% ( 1)      27% ( 1)   middling
hwmon.device-label                 3% ( 1)       0% ( 0)      18% ( 1)   middling
hwmon.firmware-node               10% ( 1)      24% ( 1)      66% ( 3)   weak: reader C
hwmon.thermal-legacy              19% ( 3)      17% ( 1)      30% ( 1)   middling
hwmon.channel-arrays              16% ( 2)      24% ( 4)       4% ( 2)   middling
hwmon.chip-entry-position         15% ( 7)      15% ( 2)      58% ( 6)   weak: reader C
hwmon.visibility                   5% ( 3)      18% ( 5)      54% ( 4)   weak: reader C
hwmon.missing-callbacks            8% ( 2)       1% ( 1)      74% ( 3)   weak: reader C
hwmon.unknown-bits                12% ( 2)      46% ( 4)      36% ( 2)   weak: reader B
hwmon.read-contract               18% ( 9)      16% ( 5)      35% ( 9)   middling
hwmon.energy64                    18% ( 6)      28% ( 4)      56% ( 5)   weak: reader C
hwmon.read-string                 26% ( 4)      35% ( 4)      43% ( 3)   weak: reader C
hwmon.write-parsing                0% ( 1)       0% ( 0)       8% ( 2)   all fair: drop, or shrink to a pointer
hwmon.write-range                 19% ( 3)      35% ( 2)      36% ( 3)   middling
hwmon.invalid-values              27% ( 5)      65% ( 3)      79% ( 2)   weak: reader B, reader C
hwmon.conversion-arithmetic       10% ( 4)      25% ( 2)      32% ( 4)   middling
hwmon.error-codes                 19% ( 4)      40% ( 3)      65% ( 3)   weak: reader B, reader C
hwmon.callback-context            18% ( 5)      30% ( 3)      61% ( 4)   weak: reader C
hwmon.core-lock                   25% ( 4)       9% ( 8)      54% ( 8)   weak: reader C
hwmon.lock-helpers                24% ( 3)      23% ( 4)      31% ( 3)   middling
hwmon.lock-nesting                26% ( 5)      38% ( 2)      20% ( 2)   middling
hwmon.interrupt-paths             44% ( 7)      27% ( 2)      41% ( 3)   weak: reader A, reader C
hwmon.driver-mutex                 4% ( 3)      22% ( 2)      43% ( 4)   weak: reader C
hwmon.cached-readings             33% ( 7)      32% ( 5)      49% ( 3)   weak: reader C
hwmon.notify-event                21% ( 3)      10% ( 2)      54% ( 7)   weak: reader C
hwmon.notify-context              33% ( 6)      25% ( 4)      69% ( 4)   weak: reader C
hwmon.thermal-conditions           6% ( 3)       8% ( 2)      58% ( 3)   weak: reader C
hwmon.thermal-channel-index        0% ( 0)       0% ( 0)      36% ( 1)   middling
hwmon.thermal-ops                  3% ( 1)       9% ( 2)      50% ( 3)   weak: reader C
hwmon.thermal-failure              0% ( 0)       0% ( 0)      56% ( 2)   weak: reader C
hwmon.pec-attribute               15% ( 6)      27% ( 6)      60% ( 3)   weak: reader C
hwmon.abi-units                   11% ( 6)      20% ( 5)      47% ( 7)   weak: reader C
hwmon.abi-alarms                  37% ( 6)      36% ( 6)      63% ( 5)   weak: reader C
hwmon.abi-permissions             34% ( 5)      46% ( 5)      47% ( 5)   weak: reader B, reader C
hwmon.nonstandard-attributes      35% ( 5)      53% ( 7)      56% ( 4)   weak: reader B, reader C
hwmon.doc-versus-code             52% (10)      84% ( 8)      84% ( 6)   all weak
hwmon.sensor-attr-macros          10% ( 3)      33% ( 6)       9% ( 6)   middling
hwmon.legacy-register             14% ( 5)      34% ( 5)      24% ( 7)   middling
hwmon.i2c-detection               27% ( 5)      45% ( 9)      59% ( 8)   weak: reader B, reader C
hwmon.pmbus-files                 20% ( 4)      32% ( 5)      48% ( 9)   weak: reader C
hwmon.pmbus-registration          20% ( 4)      31% ( 2)      57% ( 5)   weak: reader C
hwmon.pmbus-locking               26% ( 8)      38% ( 5)      63% ( 8)   weak: reader C
hwmon.new-attribute               17% ( 7)      20% (10)      63% ( 6)   weak: reader C
hwmon.register-unwind             12% ( 5)      15% ( 4)      53% ( 6)   weak: reader C
hwmon.unregister-id               20% ( 3)       8% ( 2)      44% ( 6)   weak: reader C
hwmon.attribute-memory            15% ( 6)      33% ( 5)      54% ( 4)   weak: reader C
```

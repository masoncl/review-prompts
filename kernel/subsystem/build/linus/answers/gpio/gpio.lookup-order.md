- Board tables: `gpiod_find_and_request()` searches them only when its
  `platform_lookup_allowed` argument is true. `gpiod_get_index()` passes true.
- `fwnode_gpiod_get_index()` and `devm_fwnode_gpiod_get_index()`: pass false,
  so `-ENOENT` from the primary and secondary nodes is the final result.
- Firmware hit on a descriptor with `GPIOD_FLAG_SHARED`: the result is
  replaced by `-ENOENT` and the board tables are searched, for the fwnode-only
  getters too; see "Lines with several consumers".
- OF legacy names: `of_find_gpio_quirks[]` in `drivers/gpio/gpiolib-of.c`, run
  only after both suffixes gave `-ENOENT`.
  - The rename table is inside `of_find_gpio_rename()`; each entry is compiled
    in only under `IS_ENABLED()` of the consumer driver's symbol.
  - No quirk matches a NULL `con_id`.
- ACPI fallback to _CRS by index: only what `acpi_can_fallback_to_crs()`
  allows, which is a NULL `con_id` on an ACPI device with no properties and no
  `driver_gpios`. No quirk widens it.
- ACPI and `-ENOENT`: the property loop in `__acpi_find_gpio()` passes on only
  success and `-EPROBE_DEFER`; any other failure ends as `-ENOENT` when the
  _CRS fallback is not allowed.
- `acpi_find_gpio()`: returns `-ENOENT` for a GpioInt resource when the request
  flags equal `GPIOD_OUT_LOW` or `GPIOD_OUT_HIGH`.
  - With ACPI, `-ENOENT` (NULL from the optional getters) therefore does not
    prove that firmware has no entry.
- `-EPROBE_DEFER` has more sources than a missing controller:

  | Source | Also returned when |
  |---|---|
  | `of_get_named_gpiod_flags()` | a registered chip's `of_xlate` rejects the specifier; see `of_gpiochip_match_node_and_xlate()` |
  | `swnode_find_gpio()` | the referenced software node is not registered yet (`-ENOTCONN`) |
  | `gpio_desc_table_match()` | no chip has a label equal to `key`, or, with `chip_hwnum` equal to `U16_MAX`, no line is named `key` |
  | `gpiod_request()` | `try_module_get()` on the chip's owner fails |

- Property name buffer: `char propname[32]` in the OF, ACPI and swnode
  lookups. `for_each_gpio_property_name()` fills it with `snprintf()`, so a
  `con_id` longer than 25 characters is truncated silently.

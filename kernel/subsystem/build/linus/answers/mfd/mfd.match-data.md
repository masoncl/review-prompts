- Backends of `device_get_match_data()`: only `of_fwnode_ops` and the ACPI
  fwnode ops implement `device_get_match_data`; it never reads a
  `struct platform_device_id`, `struct i2c_device_id` or
  `struct spi_device_id` table.
- Device whose primary fwnode is a software node, or that has no fwnode: the
  result is `NULL`; `software_node_ops` has no `device_get_match_data`.
- ACPI backend: `acpi_device_get_match_data()` returns
  `acpi_device_id.driver_data`, or `of_device_id.data` when the match came
  through the OF table, so both tables must hold the same kind of value.
- Legacy-table fallback: not in `device_get_match_data()`; the bus helpers
  `i2c_get_match_data()` and `spi_get_device_match_data()` add it, and it runs
  whenever the firmware result is `NULL`, which includes a matched entry whose
  data is 0.
- `dev->driver`: `of_device_get_match_data()` and
  `acpi_device_get_match_data()` dereference it without a test; it must be
  set, as it is from the start of probe, and the tables searched are those of
  that driver.
- **Potentially unsafe usage**: a valid variant stored as 0 in an id table.
  - Unsafe: when probe tests the result to reject an unmatched device; the
    variant and "no match" both read as 0.
  - Unsafe: with `i2c_get_match_data()` or `spi_get_device_match_data()` when
    the legacy table can match the same device with another value; the
    fallback replaces the 0.
  - Safe: variants start at 1 and probe rejects 0, as `adp5585_i2c_probe()`
    does with `enum adp5585_variant`.

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

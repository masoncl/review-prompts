- MFD core: no KUnit test and no selftest. No file under `drivers/mfd/`
  mentions KUnit, and no file with "test" or "kunit" in its name calls
  `mfd_add_devices()`.
- System controller helper: no KUnit test and no selftest; no such file calls
  a lookup function of `drivers/mfd/syscon.c`.
- Regmap interrupt controller: no test. `drivers/base/regmap/regmap-kunit.c`
  has no reference to `regmap_add_irq_chip()` or `struct regmap_irq_chip`.
- `REGMAP_KUNIT` in `drivers/base/regmap/Kconfig`: selects `REGMAP_RAM` only,
  so a KUnit run does not even build `drivers/base/regmap/regmap-irq.c` unless
  something else selects `REGMAP_IRQ`.
- `tools/testing/selftests/`: has no directory for MFD.

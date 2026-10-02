- `drivers/mfd/syscon.c`: defines no `struct platform_driver`, no probe
  function, no OF match table and no platform id table; there is no
  syscon_driver or syscon_probe() in this tree.
- `syscon` compatible: nothing binds to it; the file holds only the lookup
  functions and `of_syscon_register_regmap()`.
- `CONFIG_MFD_SYSCON`: a `bool` in `drivers/mfd/Kconfig`; the file has no
  initcall and no exit function.
- `of_syscon_register()`: maps `reg` index 0 with `of_iomap()`, not through a
  device resource, so nothing claims the memory region.

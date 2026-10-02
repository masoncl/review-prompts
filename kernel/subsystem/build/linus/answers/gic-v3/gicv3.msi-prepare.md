- Existing device ID: `its_msi_prepare()` always reuses the device found. It
  makes no test of the device's size against `nvec` and never creates a
  second device for the same ID.
- Lock: the mutex `its->dev_alloc_lock`, held across `its_find_device()` and
  `its_create_device()`. The raw spinlock `its->lock` is taken and released
  inside `its_find_device()` for the list walk, and again in
  `its_create_device()` for the `list_add()`; it is not held between the
  two.
- `its_msi_teardown()` in `drivers/irqchip/irq-gic-v3-its.c` with `lpi_map`
  not empty: `WARN_ON_ONCE()` and return; nothing is freed.
- `its_msi_teardown()` frees in this order: `its_lpi_free()` for the LPI
  range and bitmap, `its_send_mapd(its_dev, 0)`, then `its_free_device()`.
- `its_free_device()`: only unlinks the device and frees `col_map`, the ITT
  and the structure; it sends no MAPD and returns no LPIs.

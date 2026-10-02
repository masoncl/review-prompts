- Parent without the `syscon` compatible, two forms in this tree:
  - `device_node_to_regmap()` on the parent node, as `jz4740_wdt_probe()`
    does; creates a plain MMIO regmap.
  - `syscon_node_to_regmap()` on the parent node, when the parent driver
    registers its own regmap, as `sun20i_regulator_get_regmap()` does with
    `sunxi_sram_probe()`; returns `-EPROBE_DEFER` until the registration.
- `dev_get_regmap()` on the parent device: finds no regmap made by
  `of_syscon_register()`, because `__regmap_init()` calls
  `regmap_attach_dev()` only for a non-NULL device; it returns NULL unless a
  driver created a regmap on that device.
- `of_get_parent()` form: the lookup keeps no node reference, so
  `of_node_put()` directly after the lookup is right, as in
  `berlin2_reset_probe()`.

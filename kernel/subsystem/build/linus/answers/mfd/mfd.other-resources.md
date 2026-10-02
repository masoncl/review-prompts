- **Unsafe usage**: `IORESOURCE_REG` cells together with a non-NULL
  `mem_base`. The core tests `flags & IORESOURCE_MEM`, and `IORESOURCE_REG`
  contains that bit. The resource is offset by `mem_base->start`, gets
  `mem_base` as parent and is inserted under it.
  - Safe: pass NULL as `mem_base`, as `ocelot_core_init()` does; the resource
    then takes the last `else` branch of `mfd_add_device()`.
- `IORESOURCE_IO`: does not contain the `IORESOURCE_MEM` bit, so it is copied
  unchanged whether or not `mem_base` is set.
- `platform_get_resource()` and `platform_get_resource_byname()`: compare
  `resource_type()` exactly, unlike the bit test in the core.
  - A lookup for `IORESOURCE_MEM` never returns an `IORESOURCE_REG` resource;
    `ocelot_regmap_from_resource_optional()` relies on that.
- Ocelot child, for an `IORESOURCE_REG` resource: uses only `res->name`, never
  `res->start`.
  - `ocelot_spi_init_regmap()` on the parent side turns `start` and the size
    into `reg_base` and `max_register` of the named regmap.
- Other children: use `res->start` as the register address on the parent's
  bus; for example `drivers/regulator/wm831x-dcdc.c`.
- `ocelot_core_try_add_regmap()` in `drivers/mfd/ocelot-core.c`: skips a name
  that already has a regmap on the parent, and discards the result of
  `ocelot_spi_init_regmap()`.
  - A failed regmap shows up only in the child, for example as `-ENOENT` from
    `ocelot_regmap_from_resource()`.

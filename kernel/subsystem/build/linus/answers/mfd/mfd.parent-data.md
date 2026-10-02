- `simple_mfd_i2c_probe()` in `drivers/mfd/simple-mfd-i2c.c`: creates the
  regmap and adds the children, but sets no driver data; its children get NULL
  from `dev_get_drvdata()` on the parent and reach the regmap through
  `dev_get_regmap()`.
- `rk8xx_probe()` in `drivers/mfd/rk8xx-core.c`: receives a regmap that the bus
  glue (`drivers/mfd/rk8xx-i2c.c`, `drivers/mfd/rk8xx-spi.c`) already created,
  then sets driver data, adds the irq chip, and only then adds the cells.
- Children of a syscon parent: call `syscon_node_to_regmap()` or
  `device_node_to_regmap()` on `dev->parent->of_node`; these return `ERR_PTR()`
  and are checked with `IS_ERR()`, while `dev_get_regmap()` is checked for NULL.
- `regulator_register()` in `drivers/regulator/core.c`: when `config->regmap`
  is NULL and the child has no regmap of its own, uses
  `dev_get_regmap(dev->parent, NULL)`; `devm_clk_register_regmap()` in
  `drivers/clk/qcom/clk-regmap.c` has the same fallback.
- Earliest point: `really_probe()` in `drivers/base/dd.c` returns `-EBUSY` if
  the device's devres list is not empty when probing starts, so on a device
  that binds to a driver a regmap can be attached only from inside that
  device's own probe or later.
- Parent unbind and parent probe failure: both run `device_unbind_cleanup()`,
  which calls `devres_release_all()` and then `dev_set_drvdata(dev, NULL)`.
- Parent probe failure after plain `mfd_add_devices()`: the driver core does
  not remove the children; the parent's error path must call
  `mfd_remove_devices()`, or the children stay registered with NULL parent
  driver data. For example, `da9052_device_init()` in
  `drivers/mfd/da9052-core.c` calls it when its second `mfd_add_devices()` call
  fails.
- **Unsafe usage**: a child calling `dev_get_regmap()` on its parent from its
  remove callback, or from any path that can run while the parent unbinds.
  - Unsafe: when the parent's devres removes the children, as after
    `devm_mfd_add_devices()`; `devres_release_all()` unlinks every devres entry
    of the parent before it runs any release callback, so the lookup returns
    NULL while `devm_mfd_dev_release()` is removing the children;
    `dev_get_drvdata()` on the parent is still set at that point.
  - Safe: look the regmap up once in probe and keep the pointer, as
    `rk808_clkout_probe()` in `drivers/clk/clk-rk808.c` does; `release_nodes()`
    in `drivers/base/devres.c` runs the newest release first, so a regmap
    created with a devm initializer such as `devm_regmap_init_i2c()` before
    `devm_mfd_add_devices()` is freed after the children are gone.

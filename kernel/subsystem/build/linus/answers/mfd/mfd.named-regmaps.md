- NULL `name`: returns the most recently attached regmap, named or unnamed;
  `find_dr()` in `drivers/base/devres.c` walks the list newest first.
- Parent with several regmaps whose children pass NULL: the default regmap must
  be attached last, as `pm8008_probe()` in `drivers/mfd/qcom-pm8008.c` does.
- Unmanaged regmaps are found too: `__regmap_init()` calls
  `regmap_attach_dev()` for any non-NULL `dev`, so `regmap_init()` and
  `devm_regmap_init()` both add the lookup entry.
- `regmap_attach_dev()` called directly: publishes a regmap that was created on
  another device (for example a dummy I2C client) on the parent; see
  `max77759_create_i2c_subdev()` in `drivers/mfd/max77759.c`.
- Lookup name after `regmap_attach_dev()`: it is `name` from the
  `struct regmap_config` passed to that call, which replaces the name given at
  init when it is not NULL; `pm8008_probe()` creates with "primary" and attaches
  with "secondary".
- `regmap_attach_dev()` also sets `map->dev` to the new device; the entry on the
  device the regmap was created on stays in place.
- `dev_get_regmap_match()`: compares only the name, never the regmap pointer, so
  two regmaps with the same name on one device cannot be told apart and the
  newest is returned.
- `regmap_exit()`: `regmap_detach_dev()` removes the newest entry on `map->dev`
  whose name equals `map->name`, and any newest entry when `map->name` is NULL;
  with several regmaps on one device the entry removed can belong to another
  regmap, unless every regmap there has a distinct, non-NULL name.

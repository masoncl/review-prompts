- Match table: there is no of_default_bus_match_table symbol in the C code;
  the table is the function-local `match_table` in
  `of_platform_default_populate()`, `drivers/of/platform.c`.
- Code that tests the string `simple-mfd`: only that table and
  `simple_pm_bus_of_match` in `drivers/bus/simple-pm-bus.c`.
- `of_platform_default_populate()`: not a boot-only path; it is exported and
  drivers call it on their own node, for example `drivers/bus/imx-weim.c`.
- `of_platform_default_populate_init()` with `CONFIG_PPC`: does not call
  `of_platform_default_populate()`; platform code does, for example
  `arch/powerpc/platforms/microwatt/setup.c`.
- `of_platform_populate()` with `matches == NULL`: creates devices for the
  direct children of `root` and recurses into none of them;
  `__of_match_node()` returns NULL for a NULL table. The kerneldoc "NULL to
  use the default" does not describe the code.
- `devm_of_platform_populate()`: passes `matches == NULL`, so a `simple-mfd`
  child node gets a platform device and that node's children get none.
- Driver that needs recursion into `simple-mfd` children: calls
  `of_platform_default_populate()`.
- `of_platform_bus_create()` recurses only after
  `of_platform_device_create_pdata()` returned a device for the `simple-mfd`
  node itself; a disabled node or one with `OF_POPULATED` already set gets no
  device and its children are not walked.
- `OF_POPULATED` and `of_device_is_available()`: tested in
  `of_platform_device_create_pdata()`; `of_platform_bus_create()` tests
  `OF_POPULATED_BUS`.
- `of_clk_init()` and `of_irq_init()`: set `OF_POPULATED` on each node they
  initialise, so a `simple-mfd` node that is also such a provider loses its
  children.
- `CLK_OF_DECLARE_DRIVER()`: clears `OF_POPULATED` again, `CLK_OF_DECLARE()`
  does not; see `drivers/clk/ingenic/x1000-cgu.c`.
- Children that get no platform device even when walked, in addition to the
  flag and availability tests above: nodes without a `compatible` property;
  nodes matching `of_skipped_node_table`; nodes compatible with
  `arm,primecell`, which go to `of_amba_device_create()` and are not recursed
  into.

- `of_platform_populate()`: makes no availability test on `root`; availability
  is tested per node, inside `of_platform_device_create_pdata()` and
  `of_amba_device_create()`.
- `of_platform_bus_create()`: every return path yields 0, so
  `of_platform_populate()` returns `-EINVAL` (no root node) or 0, and 0 says
  nothing about which devices exist; the `of_platform_populate()` stub
  without `CONFIG_OF_ADDRESS` returns `-ENODEV`.
- `OF_POPULATED_BUS` on `root`: set by `of_platform_populate()` unconditionally
  after the walk, not only on success.
- `strict`: the no-"compatible" skip applies only when it is true;
  `of_platform_populate()` always passes true, `of_platform_bus_probe()`
  passes false.
- `of_skipped_node_table`: one entry, "operating-points-v2"; nothing about
  reserved memory is skipped by table.
- `reserved_mem_matches`: the opposite of a skip list;
  `of_platform_default_populate_init()` creates a device for each matching
  child of `/reserved-memory` with `of_platform_device_create()`, except
  under `CONFIG_PPC`.
- There is no of_default_bus_match_table definition here; the default table
  is the static `match_table` inside `of_platform_default_populate()`, and its
  "arm,amba-bus" entry exists only under `CONFIG_ARM_AMBA`.
- `matches` NULL: `__of_match_node()` returns NULL, so only the direct
  children of `root` get devices; the kerneldoc "NULL to use the default" is
  not what the code does. `devm_of_platform_populate()` passes NULL.
- "arm,primecell" node without `CONFIG_ARM_AMBA`: `of_amba_device_create()` is
  a stub returning NULL and `of_platform_bus_create()` still returns before
  the platform path, so the node gets no device of either kind.
- `OF_POPULATED_BUS` test in `of_platform_bus_create()`: this is the
  `of_node_check_flag()` skip; `OF_POPULATED` is not checked there, it is
  test-and-set inside the two create helpers.
- `OF_POPULATED_BUS` is also set by `of_platform_bus_create()` on a node it
  descended into, whatever the children returned.
- Second `of_platform_populate()` on the same `root`: the flag on `root` is
  not tested, the children are walked again; per-node flags are what stop
  duplicates.
- `OF_POPULATED` set by other code: `of_irq_init()` in `drivers/of/irq.c` and
  `of_clk_init()` in `drivers/clk/clk.c` set it on nodes they initialise, so
  populate makes no platform device for them and does not descend.
  - A driver that needs both clears it by hand, for example
    `CLK_OF_DECLARE_DRIVER()` and `imx_gpcv2_irqchip_init()`.
- `of_platform_depopulate()`: the `OF_POPULATED_BUS` test is on
  `parent->of_node` only; each child platform device is then destroyed if its
  own node has `OF_POPULATED`, including one made by hand with
  `of_platform_device_create()`.
- `of_platform_depopulate()` after populating a different node:
  `of_platform_populate()` flags `root`, depopulate tests `parent->of_node`;
  if they differ and `parent->of_node` lacks the flag, depopulate does nothing.
  `devm_of_platform_populate()` passes `dev->of_node` and `dev`, so they match.
- `of_platform_device_destroy()`: clears both flags before it unregisters the
  device, not after.
- **Unsafe usage**: unregistering a device that `of_platform_device_create()`
  or `of_platform_populate()` made, with `platform_device_unregister()` or
  `of_device_unregister()`, and leaving `OF_POPULATED` set;
  `platform_device_release()` clears no flag, so
  `of_platform_device_create_pdata()` returns NULL for that node from then on.
  - Safe: remove it with `of_platform_device_destroy()`, as
    `of_platform_notify()` does.
  - Safe: clear `OF_POPULATED` on `dev->of_node` first, then unregister, as
    `ssi_remove_ports()` in `drivers/hsi/controllers/omap_ssi_core.c` does.
  - Safe: a device built with `of_device_alloc()` and `of_device_add()`, which
    never set `OF_POPULATED`, as `ibmebus_create_device()` in
    `arch/powerpc/platforms/pseries/ibmebus.c` does.
- `of_find_device_by_node()`: searches `platform_bus_type` only, so it returns
  NULL for a node whose device is on `amba_bustype`.
- Releasing the lookup result: `platform_device_put()` accepts NULL and
  `of_platform_notify()` relies on that; `put_device(&pdev->dev)` needs a
  NULL test first, because `dev` is not the first member of
  `struct platform_device`.

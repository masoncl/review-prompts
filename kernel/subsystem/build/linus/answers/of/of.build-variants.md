- Stub return values are not all errors: without `CONFIG_OF`, for example,
  `of_add_property()`, `of_remove_property()` and `of_dma_configure()`
  return 0.
- `of_iomap()` and `of_address_to_resource()`: their stubs (NULL, `-EINVAL`)
  are selected by `CONFIG_OF`, not `CONFIG_OF_ADDRESS`; see the second
  `#ifdef` block in `include/linux/of_address.h`.
- With `CONFIG_OF` on and `CONFIG_OF_ADDRESS` off, those two are plain
  externs; SPARC defines them in `arch/sparc/kernel/of_device_common.c`.
- `of_irq_get()`, `of_irq_get_byname()` and `of_irq_count()` without
  `CONFIG_OF_IRQ`: return 0, not an error; `of_irq_parse_one()` returns
  `-EINVAL`.
- There is no of_msi_map_id() here; the `of_msi_xlate()` stub returns
  `id_in` unchanged, and the `!CONFIG_OF` stub of `of_map_msi_id()` returns
  `-EINVAL`.
- `CONFIG_OF_DYNAMIC` off: besides the `of_node_get()` and `of_node_put()`
  inlines, only `of_reconfig_notifier_register()`,
  `of_reconfig_notifier_unregister()`, `of_reconfig_notify()` and
  `of_reconfig_get_state_change()` have stubs in `include/linux/of.h`, all
  four returning `-EINVAL`.
- No stub exists for the changeset functions (for example
  `of_changeset_init()`, `of_changeset_apply()`), `of_attach_node()`,
  `of_detach_node()` or `of_resolve_phandles()`; a caller fails to build
  unless its Kconfig entry requires the option or the calls sit under an
  `#if` on it, as in `drivers/media/platform/qcom/venus/core.c`.
- `CONFIG_OF_EARLY_FLATTREE` off: stubs exist only for the functions in the
  `#else` branch of `include/linux/of_fdt.h`; `of_scan_flat_dt()` and
  `early_init_dt_scan()`, for example, have none.
- `early_init_dt_scan_chosen_stdout()` stub: returns `-ENODEV`;
  `of_flat_dt_get_machine_name()` stub: returns NULL.
- `CONFIG_OF_FLATTREE` and `CONFIG_OF_RESOLVE`: select no stubs; without
  `CONFIG_OF_FLATTREE`, `initial_boot_params` is not even declared.
- `of_dma_get_range()` in `drivers/of/of_private.h`: returns `-ENODEV`
  unless both `CONFIG_OF_ADDRESS` and `CONFIG_HAS_DMA` are set.
- `of_platform_register_reconfig_notifier()`: empty unless both
  `CONFIG_OF_DYNAMIC` and `CONFIG_OF_ADDRESS` are set.
- `CONFIG_OF_ADDRESS` depends on `!SPARC && (HAS_IOMEM || UML)` and
  `CONFIG_OF_IRQ` on `!SPARC && IRQ_DOMAIN`, so their stubs apply on SPARC
  and on any other `CONFIG_OF` build that fails those tests.
- `CONFIG_OF_PROMTREE`: selected only by `arch/sparc/Kconfig` and by
  `config OLPC` in `arch/x86/Kconfig`; `arch/powerpc/Kconfig` selects
  `OF_EARLY_FLATTREE` instead.
- x86 with `CONFIG_OLPC`: `CONFIG_OF_EARLY_FLATTREE` is also on, so
  `drivers/of/fdt.c` is built next to `drivers/of/pdt.c`.
- SPARC: `CONFIG_OF_EARLY_FLATTREE` defaults to off; `fdt.c` is built only
  if something selects `CONFIG_OF_FLATTREE`, for example
  `CONFIG_OF_OVERLAY`.
- `CONFIG_OF_UNITTEST` depends on `OF_EARLY_FLATTREE`, which defaults to off
  on SPARC; x86 with `CONFIG_OF` always has `OF_EARLY_FLATTREE`.
- No blob from the bootloader: `unflatten_device_tree()` in
  `drivers/of/fdt.c` unflattens the built-in `drivers/of/empty_root.dts`;
  `of_have_populated_dt()` tells that case apart.
- Checker for expected messages: `scripts/dtc/of_unittest_expect`, run on a
  saved console log; the kernel compares nothing.
- `EXPECT_NOT_BEGIN()` and `EXPECT_NOT_END()`: mark a message that must not
  appear between them.
- Match rule, `compare()` in the script: the console line, timestamp
  removed, must begin with the expected text; anything after it is ignored.
- Expected text of a message printed with `pr_err()`, `pr_warn()` or
  `pr_info()` therefore starts with the `pr_fmt` prefix of the printing
  file, for example `"OF: overlay: "`; a patch that changes a `pr_fmt` in
  `drivers/of/` changes every such message of that file.
- Expected strings are formatted output, with node paths and errno numbers
  already expanded; search `drivers/of/unittest.c` for a fixed fragment of
  the message, not for the format string.
- A message printed by several tests has one pair per test; all pairs need
  the new text.
- Placeholders in expected text: `<<int>>`, `<<hex>>`, and `<<all>>`, which
  matches the rest of the line.
- `level` argument of the four macros: the level the marker line is printed
  at; the script compares text only.

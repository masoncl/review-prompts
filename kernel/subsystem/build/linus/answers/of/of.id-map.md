- `of_map_id()` signature here: `(np, id, map_name, cells_name, map_mask_name,
  filter_np, arg)`; there is no `u32` ID out-pointer and no node out-pointer.
- Result: a `struct of_phandle_args` filled through `arg`; the node is
  `arg->np`, the translated ID is `arg->args[0]`.
- Wrappers: `of_map_iommu_id()` and `of_map_msi_id()` in `drivers/of/base.c`
  are the only callers of `of_map_id()`; `of_map_iommu_id()` passes a NULL
  `filter_np`.
- `filter_np` is `struct device_node * const *` and is never written.
- `filter_np` non-NULL: the map property must exist; `*filter_np` non-NULL
  as well: only entries that target that node match.

| Case | Return | `arg->np` | `arg->args[]` |
|---|---|---|---|
| `np`, `map_name`, `cells_name` or `arg` NULL | `-EINVAL` | not written | not written |
| property absent, `filter_np` NULL | 0 | NULL | `args[0]` = input ID, `args_count` 1 |
| property absent, `filter_np` non-NULL | `-ENODEV` | NULL | not written |
| no entry matches, or none targets `*filter_np` | 0 | NULL | `args[0]` = unmasked input ID, `args_count` 1 |
| an entry matches | 0 | target node | each output cell plus (masked ID − id-base) |

- Match versus bypass: only `arg->np` tells them apart; both return 0. See
  `imx_pcie_add_lut_by_rid()` in `drivers/pci/controller/dwc/pci-imx6.c`.
- Ownership: on a match `arg->np` holds a reference from
  `of_find_node_by_phandle()`, with or without a filter; the caller calls
  `of_node_put()`.
- **Unsafe usage**: `of_node_put(arg->np)` after a failed call when `arg` was
  not zero-initialised.
  - Unsafe: `of_map_id()` sets `arg->np = NULL` only after its argument
    check, so on that `-EINVAL` return, for example for a NULL `np`,
    `arg->np` is stack garbage; under `CONFIG_OF_DYNAMIC` `of_node_put()`
    passes it to `kobject_put()`.
  - Safe: `struct of_phandle_args spec = {};` then an unconditional
    `of_node_put(spec.np)`, as `of_pmsi_get_msi_info()` in
    `drivers/irqchip/irq-gic-its-msi-parent.c` does.

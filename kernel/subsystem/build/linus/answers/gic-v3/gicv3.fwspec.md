- There is no GIC_IRQ_TYPE_PARTITION case and no partition domain in this
  tree; a partitioned PPI translates like any PPI or EPPI and
  `gic_irq_domain_translate()` ignores `param[3]`.
- Devicetree type cell: the code tests the literals 0 to 3 and
  `GIC_IRQ_TYPE_LPI`; `GIC_ESPI` and `GIC_EPPI` are the binding names in
  `include/dt-bindings/interrupt-controller/arm-gic.h`.
- One-cell form (`param_count == 1`, `param[0] < 16`): tested before the
  fwnode kind, gives the SGI with `IRQ_TYPE_EDGE_RISING`; `gic_smp_init()`
  uses it.
- LPI specifier: the trigger type comes from `param[2]` like the others, and
  the same `WARN_ON()` applies.
- Number out of range for its type (SPI > 987, PPI > 15, ESPI > 1023,
  EPPI > 63): `pr_warn_once()` only, translation succeeds with the plain
  sum; for example PPI number 16 becomes hwirq 32, an SPI.
- `WARN_ON(*type == IRQ_TYPE_NONE)`: the only trigger check in translate,
  for every devicetree type and for ACPI; it still returns 0.
- Trigger a SPI or ESPI cannot use: rejected later, by `gic_set_type()` with
  -EINVAL, not by translate.
- ACPI branch: `param_count != 2` and `param[0] < 16` return -EINVAL; a
  fwnode that is neither devicetree nor irqchip returns -EINVAL.
- Affinity lookup path: `platform_get_irq_affinity()` ->
  `get_irq_affinity()` -> `of_irq_get_affinity()` ->
  `irq_populate_fwspec_info()` -> `gic_irq_get_fwspec_info()`.
- `gic_irq_get_fwspec_info()` outcomes:

| Specifier | Result |
|---|---|
| not devicetree | 0, no affinity, flags 0 |
| exactly 4 cells, `param[3]` non-zero, type not 1 or 3 | 0, no affinity, flags 0 |
| exactly 4 cells, `param[3]` non-zero, PPI or EPPI | mask of the matching partition |
| same, phandle not found or no partition matches | -ENOENT |
| anything else, any type | `cpu_possible_mask`, valid |

- Partitions: `gic_data.parts`, an array of `struct partition_affinity`,
  matched by comparing `partition_id` with the fwnode of the phandle.
- `gic_populate_ppi_partitions()` fills `gic_data.parts` in `gic_of_init()`
  after `gic_init_bases()` returned; before that every PPI or EPPI lookup
  with a non-zero fourth cell gives -ENOENT.
- `of_irq_get_affinity()` returns `info.affinity` without testing
  `IRQ_FWSPEC_INFO_AFFINITY_VALID`; `acpi_irq_get_affinity()` tests it.

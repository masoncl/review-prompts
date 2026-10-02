- First register access in `gicv5_its_init_bases()`: `GICV5_ITS_CR0`; no ID
  register is read before `gicv5_its_init_devtab()`.
- `GICV5_ITS_CR0_ITSEN` set by firmware: `WARN()`, then `gicv5_its_disable()`;
  init fails only if that disable times out.
- Order after that: `GICV5_ITS_CR1` and `ITS_FLAGS_NON_COHERENT`,
  `gicv5_its_init_devtab()`, `gicv5_its_enable()`, `gicv5_its_init_domain()`.

| Failing step | Undone in `gicv5_its_init_bases()` |
|---|---|
| `gicv5_its_disable()` of a pre-enabled ITS | `kfree()` of the chip data |
| `gicv5_its_init_devtab()` | `kfree()` of the chip data |
| `gicv5_its_enable()` | `gicv5_its_deinit_devtab()`, chip data |
| `gicv5_its_init_domain()` | `gicv5_its_disable()` (return dropped), `gicv5_its_deinit_devtab()`, chip data |

- `iounmap()` of the ITS base: done by the callers, `gicv5_its_init()` and
  `gic_acpi_parse_madt_its()`, not by `gicv5_its_init_bases()`.
- `gic_acpi_parse_madt_its()` on failure also frees the translate frame
  tokens, the domain fwnode and the memory region.
- **Unsafe usage**: dereferencing `np` in `gicv5_its_init_bases()`.
  - Unsafe: `np` is `to_of_node(handle)`, which is NULL when `handle` is not
    an OF node, as on the ACPI path.
  - Safe: naming the ITS with `fwnode_get_name(its_node->fwnode)`, as
    `gicv5_its_print_info()` does; `irqchip_fwnode_ops` supplies `get_name`.

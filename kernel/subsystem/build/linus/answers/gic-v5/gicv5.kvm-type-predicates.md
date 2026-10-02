| Predicate | Test for a GICv5 guest |
|---|---|
| `__irq_is_sgi()` | always false |
| `__irq_is_ppi()` | type is PPI and ID < `VGIC_V5_NR_PRIVATE_IRQS` |
| `__irq_is_spi()` | type is SPI; ID not bounded |
| `__irq_is_lpi()` | type is LPI; ID not bounded |
| `vgic_valid_spi()` | type is SPI and ID < `nr_spis` |

- `irq_is_private()`: equals `irq_is_ppi()` for a GICv5 guest.
- `nr_spis`: stays 0 for a GICv5 guest; `vgic_init()` does not set it and
  `vgic_v5_set_attr()` rejects `KVM_DEV_ARM_VGIC_GRP_NR_IRQS`, so
  `vgic_valid_spi()` is false.
- **Potentially unsafe usage**: indexing per-interrupt state with
  `vgic_v5_get_hwirq_id()` after only a type predicate.
  - Unsafe: after `irq_is_spi()` or `irq_is_lpi()`; the 24-bit ID can be
    anything.
  - Safe: after `irq_is_ppi()`; its bound is the size of `private_irqs[]`
    and of every PPI bitmap, and `kvm_vgic_set_owner()` relies on it before
    it dereferences the lookup result.

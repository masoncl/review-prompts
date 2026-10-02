- `lpi_write_config()`: ORs in `LPI_PROP_GROUP1` and nothing else beyond
  `set`; the tree has no LPI_PROP_RES1.
- `lpi_write_config()` visibility step: `gic_flush_dcache_to_poc()` on the
  byte when `RDIST_FLAGS_PROPBASE_NEEDS_FLUSHING` is set, `dsb(ishst)` when
  it is clear.
- `lpi_update_config()`: adds no barrier of its own between the write and
  the invalidate.
- Table written: chosen by `irqd_is_forwarded_to_vcpu()` at the time of the
  call. `its_vlpi_map()` sets the bit before `lpi_write_config()` so the VM's
  table is written; `its_vlpi_unmap()` clears it before
  `lpi_update_config()` so the physical table is written.
- Invalidate chosen by `lpi_update_config()`:

  | Condition | Invalidate |
  |---|---|
  | `has_direct_lpi`, and not forwarded or `is_v4_1(its_dev->its)` | `direct_lpi_inv()` |
  | otherwise, not forwarded | `its_send_inv()` |
  | otherwise, forwarded | `its_send_vinv()` |

- **Potentially unsafe usage**: calling `lpi_write_config()` without
  `lpi_update_config()`.
  - Unsafe: when nothing after the write invalidates that LPI; the
    redistributor may keep its cached byte.
  - Safe: a vPE doorbell, where the caller invalidates itself:
    `its_vpe_mask_irq()` then `its_vpe_send_inv()`, and
    `its_vpe_4_1_mask_irq()` then `its_vpe_4_1_send_inv()`.
  - Safe: `PROP_UPDATE_VLPI` in `its_vlpi_prop_update()`, where the caller
    invalidates the whole vPE afterwards, as `vgic_its_invall()` does with
    `its_invall_vpe()`.

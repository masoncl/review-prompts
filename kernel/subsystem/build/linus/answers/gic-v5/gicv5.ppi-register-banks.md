- Enable: there are no separate set-enable and clear-enable registers; only
  `SYS_ICC_PPI_ENABLER0_EL1` and `SYS_ICC_PPI_ENABLER1_EL1`.
- `gicv5_ppi_irq_mask()` and `gicv5_ppi_irq_unmask()`: open-code the enable
  access with `sysreg_clear_set_s()` then `isb()`; `enum ppi_reg` has no
  enable value.
- `read_ppi_sysreg_s()`: switches on `which`, picks the bank with `irq < 64`,
  and returns the whole 64-bit register; the caller masks with
  `BIT_ULL(hwirq % 64)`.
- `read_ppi_sysreg_s()` reads pending and active state from the set
  registers, for example `SYS_ICC_PPI_SPENDR0_EL1`; the driver never reads a
  clear register.
- `write_ppi_sysreg_s()`: writes only the one bit, to the set or the clear
  register; no read-modify-write and no `isb()`.
- `write_ppi_sysreg_s()` has no `PPI_HM` case; passing it fails the build at
  `BUILD_BUG_ON(1)`.
- Per-PPI priority field: the driver never computes one;
  `gicv5_ppi_priority_init()` writes all 16 registers whole.
- `vgic_v5_sync_ppi_priorities()` in `arch/arm64/kvm/vgic/vgic-v5.c` is the
  in-tree per-PPI computation: register `i / 8`, field
  `GENMASK(pri_bit + 4, pri_bit)` with `pri_bit` equal to `(i % 8) * 8`.
- **Unsafe usage**: passing an INTID that still holds `GICV5_HWIRQ_TYPE` in
  bits 31:29 to `read_ppi_sysreg_s()` or `write_ppi_sysreg_s()`; `irq < 64`
  is then false for every PPI, so bank 1 is always used.
  - Safe: the `GICV5_HWIRQ_ID` field alone, which `handle_irq_per_domain()`
    extracts before `generic_handle_domain_irq()`; `d->hwirq` in the PPI
    domain is the bare ID too, set from `gicv5_irq_domain_translate()`, as
    used in `gicv5_ppi_irq_get_irqchip_state()`.

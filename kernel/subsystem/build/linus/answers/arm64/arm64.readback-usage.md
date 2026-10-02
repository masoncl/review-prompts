- `gic_has_group0()` in `drivers/irqchip/irq-gic-v3.c`: `gic_write_pmr()` then
  `gic_read_pmr()`, no barrier; on a zero read-back it returns `false`, no
  access to Group 0.
- `gic_has_group0()` does not find the number of priority bits;
  `gic_get_pribits()` reads that from `ICC_CTLR_EL1`.
- `__arm_spe_pmu_dev_probe()` in `drivers/perf/arm_spe_pmu.c`: writes
  `U64_MAX` to `SYS_PMSEVFR_EL1` and reads it back, no barrier; bits that read
  0 are unsupported filter bits, stored in `pmsevfr_res0`.
- `init_el2_hcr` in `arch/arm64/include/asm/el2_setup.h`: no `HCR_EL2`
  read-back. It tests the E2H0 field of `SYS_ID_AA64MMFR4_EL1`, else writes
  `far_el1`, `isb`, writes `far_el2`, `isb`, and reads `far_el1` to see
  whether the two names alias.
- `vec_probe_vqs()`: does not find the length by reading `SYS_ZCR_EL1` or
  `SYS_SMCR_EL1` back; it reads the resulting length with `sve_get_vl()` or
  `sme_get_vl()`, which depends on the write being self-synchronising.
- `sve_setup()`: does no probing; `vec_probe_vqs()` is called by
  `vec_init_vq_map()`, `vec_update_vq_map()` and `vec_verify_vq_map()`.
- Read-backs of `ICC_SRE_EL1` and `ICC_SRE_EL2` that test whether a write to
  the SRE bit took effect have an `isb` between write and read:
  `__init_el2_gicv3`, `gic_enable_sre()` through `gic_write_sre()`, and
  `__vgic_v3_get_gic_config()`.

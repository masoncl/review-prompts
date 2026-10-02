- `pgtable_l4_enabled()` and `pgtable_l5_enabled()`: return
  `vabits_actual == VA_BITS` until `ARM64_ALWAYS_BOOT` is patched in, then
  test the `ARM64_HAS_VA52` capability.
- `vabits_actual`: not a variable; with `VA_BITS > 48` it is a macro that
  reads T1SZ through `read_tcr()`, see `arch/arm64/include/asm/memory.h`.
- `pgtable_l4_enabled()` with `CONFIG_PGTABLE_LEVELS > 3`: constant true when
  `CONFIG_PGTABLE_LEVELS > 4` or without `CONFIG_ARM64_LPA2`; one kernel folds
  at most one level at run time.
- Which level: P4D with 4K pages (5 levels configured), PUD with 16K pages
  (4 levels configured).
- Decision point: `early_map_kernel()` in `arch/arm64/kernel/pi/map_kernel.c`;
  with `CONFIG_ARM64_LPA2` and `!cpu_has_lpa2()` it uses `VA_BITS_MIN` and
  starts one level lower.
- `cpu_has_lpa2()`: tests the stage 1 granule field only, with command-line
  overrides applied; `has_lpa2()` also tests stage 2, for `ARM64_HAS_LPA2`,
  which KVM uses.
- `arm64.nolva`: alias of `id_aa64mmfr2.varange=0`; `mmfr2_varange_filter()`
  then also hides LPA2, so the level is folded.
- `lpa2_is_enabled()`: `TCR_EL1_DS` is set only together with the 52-bit
  T1SZ, in `__cpu_setup` under `ARM64_HAS_VA52` and in `early_map_kernel()`
  through `remap_idmap_for_lpa2()`; true means no level is folded at run time.
- `lpa2_is_enabled()` false on a `CONFIG_ARM64_LPA2` kernel: the one foldable
  level is folded.
- PUD folded: `p4d_none()` and `p4d_bad()` return false, and `p4d_clear()`
  does nothing; P4D folded: the same for `pgd_none()`, `pgd_bad()` and
  `pgd_clear()`.

| Write | Where | What shows it |
|---|---|---|
| `ZCR_ELx_LEN_MASK` of `SYS_ZCR_EL1`, `SMCR_ELx_LEN_MASK` of `SYS_SMCR_EL1` | `vec_probe_vqs()`, through `write_vl()` | comment `/* self-syncing */`; `sve_get_vl()` or `sme_get_vl()` runs next |
| same two fields, and `SYS_SVCR` | `task_fpsimd_load()` | code only, no comment: `sme_load_state()` and `sve_load_state()` follow and take the length from `sme_get_vl()` and `sve_get_vl()` |
| `SYS_ICC_PMR_EL1` | `local_daif_restore()`, masking branch | comment: "writes to PMR are self-synchronizing"; no barrier follows `gic_write_pmr()` |
| `daif` | `local_daif_restore()` | same comment, quoting the ARM ARM on PSTATE writes |
| PSTATE.SSBS | `spectre_v4_enable_hw_mitigation()` | comment: "SSBS is self-synchronizing" |

- There is no sve_set_vq(), sme_set_vq(), sve_load_vq or fpsimdmacros.h here;
  `task_fpsimd_load()` calls `sysreg_clear_set_s()` itself.
- `pmr_sync()` in `local_daif_restore()`: only in the unmasking branch.
- `pmr_sync()`: `dsb sy`, patched to NOPs by
  `ARM64_HAS_GIC_PRIO_RELAXED_SYNC`; empty without `CONFIG_ARM64_PSEUDO_NMI`.
  There is no gic_pmr_sync static key.
- `spectre_v4_enable_hw_mitigation()`: `spec_bar()` follows
  `set_pstate_ssbs(0)` under `CONFIG_ARM64_ERRATUM_3194386`.

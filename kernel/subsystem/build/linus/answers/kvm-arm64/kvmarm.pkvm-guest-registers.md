- There is no fixed_config.h, PVM_ID_AA64 allow macro, pvm_read_id_reg() or
  get_pvm_id_ helper here; the limits are `struct pvm_ftr_bits` tables such
  as `pvmid_aa64pfr0[]` in `arch/arm64/kvm/hyp/nvhe/sys_regs.c`.
- `pvm_calc_id_reg()`: applies a table to the hypervisor's copy of the host's
  sanitised value; `SYS_ID_AA64ISAR0_EL1` passes through unmasked,
  `SYS_ID_AA64DFR0_EL1` and `SYS_ID_AA64MMFR4_EL1` are fixed constants, any
  register without a case reads 0.
- `kvm_init_pvm_id_regs()`: fills only the AArch64 ID range, once per VM,
  under `vm_table_lock` (asserted).
- A table entry with `vm_supported` set depends on the hyp VM's
  `vcpu_features`, which `pkvm_init_features_from_host()` has already
  filtered.
- `init_pkvm_hyp_vcpu()` sets ID registers before traps, because
  `pvm_init_traps_hcr()` and `pvm_init_traps_mdcr()` read them with
  `kvm_has_feat()`.
- Where each trap register of a hyp vCPU comes from:

| Register | Protected | Non-protected |
|---|---|---|
| `arch.hcr_el2` | `pkvm_vcpu_reset_hcr()` then `pvm_init_traps_hcr()` | `pkvm_vcpu_reset_hcr()` |
| `HCR_TWI`, `HCR_TWE`, `HCR_VSE` | host, every run | host, every run |
| `arch.hcrx_el2` | `vcpu_set_hcrx()` at EL2 | host's value at `__pkvm_init_vcpu` |
| `arch.mdcr_el2` | `pvm_init_traps_mdcr()`, then replaced by the host's in `flush_hyp_vcpu()` on every run | host's, every run |
| `arch.fgt` | never written at EL2 | host's, copied by `handle___pkvm_vcpu_load()` |
| CPTR | `__activate_cptr_traps()` at each entry | same |

- There is no CPTR setup in `arch/arm64/kvm/hyp/nvhe/pkvm.c`.
- `kvm_handle_pvm_sys64()` in `arch/arm64/kvm/hyp/nvhe/switch.c` tries
  `kvm_hyp_handle_sysreg()` first, then `kvm_handle_pvm_sysreg()`.
- `pvm_sys_reg_descs[]` outcomes: not listed, undefined exception injected;
  `HOST_HANDLED()` (`access` NULL), exit to the host; otherwise handled at
  EL2.

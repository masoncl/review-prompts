| Register | Protected | Non-protected | Overwritten from host |
|---|---|---|---|
| MDCR_EL2 | `pvm_init_traps_mdcr()` at init | 0 at init | every entry, both kinds, `flush_hyp_vcpu()` |
| HCRX_EL2 | `vcpu_set_hcrx()` on the hyp VM, at init | host's `hcrx_el2`, at init | never |
| FGT registers | no EL2 writer | host's `arch.fgt` | at each load, non-protected only |
| CPTR_EL2 | no stored value | no stored value | never |

- `arch.mdcr_el2` of a protected vCPU: the value from `pvm_init_traps_mdcr()`
  does not survive the first entry; `__activate_traps()` in
  `arch/arm64/kvm/hyp/nvhe/switch.c` writes the host's value.
- Host's `arch.mdcr_el2`: built by `kvm_arm_setup_mdcr_el2()` in
  `arch/arm64/kvm/debug.c`.
- `arch.fgt` of a protected hyp vCPU: stays as zeroed by
  `map_donated_memory()` in `__pkvm_init_vcpu()`;
  `__activate_traps_hfgxtr()` writes it to the registers as it is.
- Host's `arch.fgt`: built by `kvm_vcpu_load_fgt()` in
  `arch/arm64/kvm/config.c`.
- There is no pvm_init_traps_cptr() here; `__activate_cptr_traps()` in
  `arch/arm64/kvm/hyp/include/hyp/switch.h` builds CPTR_EL2 on each entry.
- `pkvm_vcpu_init_traps()`: for a non-protected vCPU it returns after the
  `hcrx_el2` copy, before `pkvm_check_pvm_cpu_features()`.

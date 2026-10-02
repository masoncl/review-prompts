| Register | Saved | Restored |
|---|---|---|
| `SYS_ICH_VMCR_EL2` | every exit, `__vgic_v5_save_state()` | load only, `__vgic_v5_restore_vmcr_apr()` |
| `SYS_ICH_APR_EL2` | put only, `__vgic_v5_save_apr()` | load only, `__vgic_v5_restore_vmcr_apr()` |
| `SYS_ICC_ICSR_EL1` | every exit, `__vgic_v5_save_state()` | every entry, `__vgic_v5_restore_state()` |

- There is no __vgic_v5_restore_apr here; `__vgic_v5_restore_vmcr_apr()`
  writes both registers.
- `__vgic_v5_restore_state()`: writes only `SYS_ICC_ICSR_EL1`. The VMCR is
  not written on entry.
- `vgic_v5_put()`: saves only the APR. The VMCR image it leaves is the one
  from the last exit.
- Hypercalls: only `__vgic_v5_save_apr()` and `__vgic_v5_restore_vmcr_apr()`
  have `HANDLE_FUNC()` entries in `arch/arm64/kvm/hyp/nvhe/hyp-main.c`. They
  are issued with `kvm_call_hyp()` from `vgic_v5_put()` and `vgic_v5_load()`.
- `kvm_call_hyp()` under VHE: calls the function directly, then `isb()`.
- `__vgic_v5_save_state()` and `__vgic_v5_restore_state()`: not hypercalls;
  they run with the PPI save and restore functions (see "PPI register world
  switch").

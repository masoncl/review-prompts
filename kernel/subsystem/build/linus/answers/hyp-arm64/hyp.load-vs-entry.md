| State | Protected | Non-protected | Where |
|---|---|---|---|
| `HCR_TWE`, `HCR_TWI` from x3 | at load | not at load | `handle___pkvm_vcpu_load()` |
| `arch.fgt` | never from host | at load, `memcpy()` from host vCPU | `handle___pkvm_vcpu_load()` |
| `vgic_vmcr`, `vgic_ap0r`, `vgic_ap1r` | at load | at load | `handle___vgic_v3_restore_vmcr_aprs()` |
| `vgic_vmcr`, APRs back to host | at put | at put | `handle___vgic_v3_save_aprs()` |
| register state back to host | every exit | at put, if `PKVM_HOST_STATE_DIRTY` clear; also on the `__pkvm_vcpu_sync_state` hypercall | `sync_hyp_vcpu()` for protected; `handle___pkvm_vcpu_put()` and `handle___pkvm_vcpu_sync_state()` for non-protected |

- State that `flush_hyp_vcpu()` takes from the host: copied on each entry,
  not at load; see "Per-entry flush and sync".
- `handle___pkvm_vcpu_load()`: has no `is_protected_kvm_enabled()` test; its
  id lies above `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY`, so `handle_host_hcall()`
  rejects it until `kvm_protected_mode_initialized` is set.
- `arch.fgt`: not copied at init.
- `kvm_arch_vcpu_load()` in `arch/arm64/kvm/arm.c`: runs
  `kvm_vcpu_load_debug()`, `kvm_vcpu_load_fgt()` and the TWE/TWI update before
  the `__pkvm_vcpu_load` hypercall; state computed after the hypercall, such
  as `vcpu->arch.pid`, reaches EL2 only through `flush_hyp_vcpu()`.
- `__vgic_v3_restore_vmcr_aprs`: issued right after `__pkvm_vcpu_load`, so the
  pointer check in "The run hypercall" passes.

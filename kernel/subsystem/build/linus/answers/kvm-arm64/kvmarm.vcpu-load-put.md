- Ordering stated in comments of `kvm_arch_vcpu_load()`: two only.
  `kvm_arm_vmid_update()` before VTTBR_EL2 is programmed (eager on VHE), and
  `kvm_timer_vcpu_load()` before `kvm_vgic_load()`.
- Ordering enforced but not commented there: `kvm_vcpu_load_debug()` before
  `kvm_vcpu_load_vhe()`; `kvm_vcpu_load_debug()` has a `KVM_BUG_ON()` on
  `SYSREGS_ON_CPU`.
- `kvm_vcpu_load_fgt()`: runs between debug and VHE load; it fills
  `vcpu->arch.fgt`, which the trap activation writes to hardware.
- `last_vcpu_ran` flush: triggers when `*last_ran != vcpu->vcpu_idx`, that is
  when this vCPU was not the last one of that MMU loaded on this CPU.
- There is no kvm_vcpu_load_sysregs_vhe() here; `kvm_vcpu_load_vhe()` in
  `arch/arm64/kvm/hyp/vhe/switch.c` does sysregs, traps and stage 2.

| Mode | Extra difference |
|---|---|
| pKVM | `vcpu_set_pauth_traps()` does nothing; `kvm_arch_vcpu_put()` sets `PKVM_HOST_STATE_DIRTY` for a non-protected VM |
| nested | `kvm_vcpu_load_hw_mmu()` picks an MMU only if `hw_mmu` is `NULL`; outside hyp context it may raise `KVM_REQ_MAP_L1_VNCR_EL2` |
| nested | `kvm_vcpu_put_hw_mmu()` keeps `hw_mmu` when `vcpu->scheduled_out` and not `IN_WFI` |
| nested | `vcpu_set_pauth_traps()` takes `HCR_API` and `HCR_APK` from the guest's `HCR_EL2` when `is_nested_ctxt()` |

- Callers besides `vcpu_load()` and `kvm_sched_in()`: four arm64 functions do
  `kvm_arch_vcpu_put()` then `kvm_arch_vcpu_load()` on a loaded vCPU, all with
  preemption disabled; search for callers of `kvm_arch_vcpu_load()`.
- `kvm_debug_handle_oslar()` in `arch/arm64/kvm/debug.c`: the put/load pair
  that is easy to miss.
- `kvm_emulate_nested_eret()` sets `IN_NESTED_ERET` and `kvm_inject_nested()`
  sets `IN_NESTED_EXCEPTION` around the pair; both make the FP steps return
  early, and `IN_NESTED_ERET` makes `vgic_v4_put()` request a doorbell.

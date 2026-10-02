- Lock held across the sequence: only `vcpu->mutex`, from `kvm_vcpu_ioctl()`.
  Each step that needs `kvm->arch.config_lock` takes it itself; nothing
  holds it from one step to the next.
- Steps after the `vcpu_has_run_once()` early return, in order:

  | Step | Scope | Skipped on a later call by |
  |---|---|---|
  | `kvm_init_mpidr_data()` | VM | `mpidr_data` set, or one online vCPU |
  | `kvm_vgic_map_resources()` | VM, in-kernel irqchip | `ready` in `struct vgic_dist` |
  | `kvm_finalize_sys_regs()` | VM; NV also vCPU | `sysreg_masks` set (mask setup); `kvm_vm_has_ran_once()` (GIC fields); the NV per-vCPU rewrite always runs |
  | `kvm_vcpu_allocate_vncr_tlb()` | vCPU, NV | `vcpu->arch.vncr_tlb` set |
  | `kvm_vgic_vcpu_nv_init()` | vCPU, NV | nothing; same owner is accepted |
  | `kvm_calculate_traps()` | vCPU and VM | `KVM_ARCH_FLAG_FGU_INITIALIZED`, VM part |
  | `kvm_timer_enable()` | vCPU | `timer->enabled` |
  | `kvm_arm_pmu_v3_enable()` | vCPU, PMU | nothing; it only validates |
  | `vgic_v5_finalize_ppi_state()` | VM, GICv5 | `GICV5_ARCH_PPI_SW_PPI` in the mask |
  | set `PKVM_HOST_STATE_DIRTY` | vCPU, pKVM, non-protected VM | nothing |
  | `pkvm_create_hyp_vm()` | VM, pKVM | `pkvm_hyp_vm_is_created()` |
  | `pkvm_create_hyp_vcpu()` | vCPU, pKVM | `VCPU_PKVM_FINALIZED` |
  | set `KVM_ARCH_FLAG_HAS_RAN_ONCE` | VM | nothing; every vCPU sets it |

- There is no kvm_arch_vcpu_run_map_fp() and no kvm_arm_vcpu_init_debug() in
  this tree.
- Pid change on a vCPU that has run: only the `kvm_vcpu_initialized()` and
  `kvm_arm_vcpu_is_finalized()` checks run.
- Per-vCPU has-run state: not written here; `kvm_vcpu_ioctl()` in
  `virt/kvm/kvm_main.c` sets `vcpu->pid` after the function returns 0.
- Failed first run: steps that finished stay done; a step with a guard is
  skipped on the retry, the others run again. A new step must be safe to run
  once per vCPU and again after a failure.
- `kvm_vgic_map_resources()` failure: calls `kvm_vm_dead()`, so later ioctls
  return `-EIO` and there is no retry.
- `kvm_timer_enable()` with an in-kernel irqchip: `timer_irqs_are_valid()`
  sets `KVM_ARCH_FLAG_TIMER_PPIS_IMMUTABLE` when the PPIs are valid, so timer
  PPIs are frozen before `KVM_ARCH_FLAG_HAS_RAN_ONCE` is set, and stay frozen
  if a later step fails.
- Order, vgic first: `kvm_vgic_set_owner()` returns `-EAGAIN` until
  `vgic_initialized()`; `kvm_timer_enable()`, through
  `timer_irqs_are_valid()`, and `kvm_vgic_vcpu_nv_init()` call it.
- Order, ID registers before the flag: `kvm_set_vm_id_reg()` does
  `KVM_BUG_ON()` once `kvm_vm_has_ran_once()`, so the GIC field fix-up in
  `kvm_finalize_sys_regs()` runs only while the flag is clear.
- Order, GICv5 PPIs after the timer: `vgic_v5_finalize_ppi_state()` exposes
  only PPIs that have an owner, plus `GICV5_ARCH_PPI_SW_PPI`, read from
  vCPU 0.
- Order, pKVM last: `__pkvm_init_vm` takes `vcpu_features` and, for a
  non-protected VM, `kvm->arch.flags` from the host (see
  `pkvm_init_features_from_host()`), and `pkvm_create_hyp_vcpu()` needs the
  VM that `pkvm_create_hyp_vm()` made.

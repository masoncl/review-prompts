- Backing state:

  | Predicate | Tests | Can go false again |
  |---|---|---|
  | `vcpu_has_run_once()` | `!!READ_ONCE((vcpu)->pid)` | no |
  | `kvm_vm_has_ran_once()` | `KVM_ARCH_FLAG_HAS_RAN_ONCE` in `kvm->arch.flags` | no |
  | `kvm_vcpu_initialized()` | vCPU flag `VCPU_INITIALIZED` | yes |

- `VCPU_INITIALIZED` cleared on the host vCPU: by
  `kvm_arch_vcpu_ioctl_run()` when `vcpu_mode_is_bad_32bit()`.
- `fixup_guest_exit()` in `arch/arm64/kvm/hyp/nvhe/switch.c`: clears
  `VCPU_INITIALIZED` for a protected vCPU in AArch32, but on the hyp vCPU's
  copy of `cflags`; the host's `kvm_vcpu_initialized()` does not change.
- After `kvm_arch_vcpu_ioctl_run()` clears `VCPU_INITIALIZED`,
  `vcpu_has_run_once()` is still true; code must not assume that has-run
  implies initialised.
- Window: `KVM_ARCH_FLAG_HAS_RAN_ONCE` is set inside
  `kvm_arch_vcpu_run_pid_change()`, `vcpu->pid` after it returns. The VM
  predicate can be true while no vCPU's predicate is.
- `vcpu_has_run_once()` users: `kvm_arch_vcpu_run_pid_change()`,
  `kvm_arch_vcpu_ioctl_vcpu_init()`, `vcpu_reset_hcr()` and
  `kvm_vgic_create()`. It gates no register write and no finalise.
- `kvm_vm_has_ran_once()` users: search for the name; they are in
  `arch/arm64/kvm/sys_regs.c`, `arch/arm64/kvm/pmu-emul.c` and
  `arch/arm64/kvm/hypercalls.c`. No capability in
  `kvm_vm_ioctl_enable_cap()` tests it.
- `kvm_arm_pmu_v3_set_attr()`: refuses every attribute with `-EBUSY` once
  `vcpu->arch.pmu.created`; only `KVM_ARM_VCPU_PMU_V3_FILTER` and
  `KVM_ARM_VCPU_PMU_V3_SET_PMU` also test `kvm_vm_has_ran_once()`.
- Other gates in use, for example: `KVM_ARCH_FLAG_TIMER_PPIS_IMMUTABLE` for
  timer PPIs, `kvm->created_vcpus` for `KVM_CAP_ARM_MTE`,
  `vgic_initialized()` in `kvm_arch_vcpu_precreate()`.
- Register writes after first run: `set_id_reg()`, `set_pmmir()` and
  `kvm_arm_set_fw_reg_bmap()` return 0 for an unchanged value and `-EBUSY`
  for a change; `set_pmmir()` and `kvm_arm_set_fw_reg_bmap()` return
  `-EINVAL` first for a bit outside their valid mask; `set_pmcr()` ignores a
  changed `N` silently.
- **Potentially unsafe usage**: testing `kvm_vm_has_ran_once()` without
  `kvm->arch.config_lock`.
  - Unsafe: when the result decides a write to VM-wide state; the flag is set
    under that lock, and `kvm_set_vm_id_reg()` asserts the lock and does
    `KVM_BUG_ON()` if the VM has run.
  - Safe: a read-only fast path, as `get_id_reg()` does; the flag is never
    cleared, and when it is clear the function takes the lock.
- **Potentially unsafe usage**: gating a write to VM-wide configuration on
  `vcpu_has_run_once()`.
  - Unsafe: with only the calling vCPU's `vcpu->mutex` held and no VM-wide
    test under `kvm->arch.config_lock`; another vCPU's `vcpu->pid` is
    written by its own `KVM_RUN` under its own mutex.
  - Safe: with every vCPU's mutex held and every vCPU tested, as
    `kvm_vgic_create()` does after `kvm_trylock_all_vcpus()`.
  - Safe: as a shortcut in front of steps that each test VM-wide state again
    under `kvm->arch.config_lock`, as `kvm_arch_vcpu_run_pid_change()` does;
    for example `kvm_finalize_sys_regs()` tests `kvm_vm_has_ran_once()`.
  - Safe: for state private to that vCPU, from its own ioctl, as
    `vcpu_reset_hcr()` does for `hcr_el2`.

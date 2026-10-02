- Callers and vCPU state:

  | Caller | vCPU loaded |
  |---|---|
  | `check_vcpu_requests()` on `KVM_REQ_VCPU_RESET` | yes |
  | `__kvm_vcpu_set_target()`, first `KVM_ARM_VCPU_INIT` | no |
  | `kvm_vcpu_set_target()`, repeated `KVM_ARM_VCPU_INIT` | no |
  | `kvm_arch_vcpu_ioctl()` for `KVM_SET_ONE_REG`, `KVM_GET_ONE_REG`, on `KVM_REQ_VCPU_RESET` | no |

- Loaded means inside `kvm_arch_vcpu_ioctl_run()`, the only arm64 ioctl
  handler that calls `vcpu_load()`; `KVM_ARM_VCPU_INIT` runs unloaded.
- First action of `kvm_reset_vcpu()`: copy `vcpu->arch.reset_state` and clear
  its `reset` under `mp_state_lock`, before `preempt_disable()`. There is no
  kvm_pmu_vcpu_reset() in this tree.
- Every caller consumes a pending `reset_state`, so a reset from
  `KVM_ARM_VCPU_INIT` or the one-reg path applies the PSCI entry point too.
- Request order: `check_vcpu_requests()` handles `KVM_REQ_SLEEP` before
  `KVM_REQ_VCPU_RESET`; the `smp_rmb()` at the end of `kvm_vcpu_sleep()`
  pairs with the `smp_wmb()` in `kvm_psci_vcpu_on()`, so a vCPU woken by
  `CPU_ON` sees the reset request in the same pass.
- `kvm_reset_vcpu_core()` and `kvm_reset_vcpu_psci()`: defined in
  `arch/arm64/include/asm/kvm_emulate.h`, not in `arch/arm64/kvm/reset.c`.
- `kvm_reset_vcpu_psci()`: also clears `PENDING_EXCEPTION`, `EXCEPT_MASK` and
  `INCREMENT_PC`.

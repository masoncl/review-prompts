- Widths: `cflags` and `iflags` are `u8`, `sflags` is `u16`;
  `NESTED_SERROR_PENDING` and `IN_NESTED_EXCEPTION` are bits 8 and 9.
- `cflags` members: `VCPU_INITIALIZED`, `VCPU_SVE_FINALIZED`,
  `VCPU_PKVM_FINALIZED`; there is no GUEST_HAS_SVE or GUEST_HAS_PTRAUTH vCPU
  flag (SVE is `KVM_ARCH_FLAG_GUEST_HAS_SVE` in `kvm->arch.flags`).
- `cflags` written from `KVM_RUN`: `kvm_arch_vcpu_ioctl_run()` clears
  `VCPU_INITIALIZED` on a bad 32-bit state, and `VCPU_PKVM_FINALIZED` is set
  from `kvm_arch_vcpu_run_pid_change()`.
- `cflags` under pKVM: copied to the hyp vCPU once, in
  `init_pkvm_hyp_vcpu()`; later host changes do not reach it, and nVHE hyp
  clears `VCPU_INITIALIZED` and `VCPU_SVE_FINALIZED` on its own copy.
- `iflags` also holds `PKVM_HOST_STATE_DIRTY`: the host sets and clears it;
  hyp reads it from the host vCPU and never clears it.
- `iflags` in hyp: `inject_sync64()` in `arch/arm64/kvm/hyp/nvhe/sys_regs.c`
  sets the exception flags itself, besides `__kvm_adjust_pc()` clearing them.
- `sflags` is touched by code under `arch/arm64/kvm/hyp/`:
  `PMUSERENR_ON_CPU` is written by `__activate_traps_common()` on VHE and
  nVHE, and `SYSREGS_ON_CPU` is written and read by VHE code.
- `sflags` under pKVM: never copied between host and hyp vCPU.
- Accessors: `vcpu_set_flag()` and `vcpu_clear_flag()` disable preemption,
  except in the nVHE object, because load/put, run from preempt notifiers,
  write flags too.
- **Unsafe usage**: writing a vCPU flag from code that can run while another
  thread is in an ioctl of that vCPU; the accessors are a plain
  read-modify-write.
  - Safe: with `vcpu->mutex` held, which `kvm_vcpu_ioctl()` takes, as
    `kvm_incr_pc()` in an exit handler is; `kvm_inject_sea()` asserts the
    mutex.
  - Safe: state set from another thread kept outside the sets, as
    `kvm_arm_halt_guest()` does with `vcpu->arch.pause` plus `KVM_REQ_SLEEP`;
    the comment on `pause` in `struct kvm_vcpu_arch` gives the reason.
- Choosing a set: `iflags` if a pKVM hyp vCPU must see a change made after
  creation, since it is the only set copied on each run; it has three free
  bits.

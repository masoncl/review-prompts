- `KVM_BUG_ON()`: `WARN_ON_ONCE()` that is skipped when `kvm->vm_bugged` is
  already set, then `kvm_vm_bugged()`; there is no ratelimited print.
- `kvm->vm_bugged`: read only to skip a repeat WARN or a repeat
  `kvm_vm_bugged()`; every ioctl entry test reads `kvm->vm_dead`.
- `KVM_BUG_ON_DATA_CORRUPTION()` with `CONFIG_BUG_ON_DATA_CORRUPTION`: a
  plain `BUG_ON()`.
- `kvm_device_ioctl()`: returns `-EIO` on a dead VM, like `kvm_vm_ioctl()`,
  `kvm_vcpu_ioctl()` and the two compat entry points.
- File operations other than ioctl do not test `vm_dead`: for example
  `kvm_vcpu_mmap()` and `kvm_vm_stats_read()`.
- `KVM_REQ_VM_DEAD` is tested on the guest entry path by x86
  `vcpu_enter_guest()` and arm64 `check_vcpu_requests()`; only x86 and arm64
  code names the request.
- `kvm_vm_dead()` is also called on purpose: `sev_vm_move_enc_context_from()`
  kills the source VM after a successful migration.

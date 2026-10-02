- Uniqueness: the `kvm->vcpu_ids` bitmap in `struct kvm`; `test_bit()` returns
  `-EEXIST` and `__set_bit()` reserves the id in the first `kvm->lock`
  section.
- Order of tests in that section: count limit (`-EINVAL`), then the bitmap
  (`-EEXIST`), then `kvm_arch_vcpu_precreate()`.
- `kvm_arch_vcpu_precreate()` and `kvm_arch_vcpu_create()`: never see an id
  that another live or in-progress vCPU holds.
- `kvm_get_vcpu_by_id()` in the second lock section: wrapped in
  `WARN_ON_ONCE()`; a hit there is a KVM bug, not a userspace error.
- The bit is cleared only on the failure path of `kvm_vm_ioctl_create_vcpu()`,
  under `kvm->lock`.
- Type of the id: `unsigned long` in `kvm_vm_ioctl_create_vcpu()`,
  `unsigned int` in `kvm_arch_vcpu_precreate()`, `int` in `vcpu->vcpu_id`.

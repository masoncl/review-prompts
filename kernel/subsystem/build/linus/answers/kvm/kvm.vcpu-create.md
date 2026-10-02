- `vcpu->mutex`: taken after `xa_insert()` and before `kvm_get_kvm()`, inside
  `kvm->lock`; released after `atomic_inc(&kvm->online_vcpus)`.
- `kvm->lock` does not keep userspace out: `kvm_vcpu_ioctl()` does not take
  it itself. `vcpu->mutex` and `kvm_wait_for_vcpu_online()` do.
- Count limit in the first lock section: `kvm->max_vcpus`, not
  `KVM_MAX_VCPUS`.
- Second lock section: has no test of `online_vcpus` against a limit.
- `vcpu->vcpu_idx`: -1 from allocation until just before `xa_insert()`, and
  reset to -1 on failure; `kvm_lockdep_assert_vcpu_is_locked_or_unreachable()`
  treats a negative index as unreachable.

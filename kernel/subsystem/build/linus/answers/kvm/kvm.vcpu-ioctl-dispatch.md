- There is no kvm_arch_vcpu_async_ioctl() here; the hook is
  `kvm_arch_vcpu_unlocked_ioctl()`, defined by every architecture with no
  configuration gate.
- Before the hook, in order: the mm and `vm_dead` test, the `_IOC_TYPE()` test
  against `KVMIO` (`-EINVAL`), then `kvm_wait_for_vcpu_online()`.
- x86 hook: handles only `KVM_MEMORY_ENCRYPT_OP`, and only when
  `vcpu_mem_enc_unlocked_ioctl` in `struct kvm_x86_ops` is set, which only
  `vt_x86_ops` in `arch/x86/kvm/vmx/main.c` does, under
  `CONFIG_KVM_INTEL_TDX`; `KVM_INTERRUPT`, `KVM_NMI` and `KVM_SMI` run under
  `vcpu->mutex`.
- arm64 hook: always returns `-ENOIOCTLCMD`.
- A hook handler may take the locks itself: `tdx_vcpu_unlocked_ioctl()` takes
  `kvm->lock`, every `vcpu->mutex` with `kvm_lock_all_vcpus()`, then
  `kvm->slots_lock`, and then calls `vcpu_load()`.

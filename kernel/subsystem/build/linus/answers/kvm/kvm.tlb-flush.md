- There is no CONFIG_HAVE_KVM_ARCH_TLB_FLUSH_ALL and no
  kvm_arch_flush_remote_tlbs_memslot() here.
- Override: the arch defines `__KVM_HAVE_ARCH_FLUSH_REMOTE_TLBS` or
  `__KVM_HAVE_ARCH_FLUSH_REMOTE_TLBS_RANGE` in its `asm/kvm_host.h` and
  supplies the matching function; each is independent of the other.
- x86: defines both only when `IS_ENABLED(CONFIG_HYPERV)`; otherwise it gets
  the generic stubs.
- Stub return values: `kvm_arch_flush_remote_tlbs()` returns `-ENOTSUPP`,
  `kvm_arch_flush_remote_tlbs_range()` returns `-EOPNOTSUPP`; generic code
  tests only for zero.
- `kvm_flush_remote_tlbs_memslot()`: asserts `slots_lock` and nothing else.

- `kvm_set_internal_memslot()` in `virt/kvm/kvm_main.c`: the only non-static
  function that calls `kvm_set_memory_region()`.
- `kvm_set_memory_region()` and `kvm_set_memslot()`: static; there is no
  __kvm_set_memory_region() in this tree.
- Export: `EXPORT_SYMBOL_FOR_KVM_INTERNAL()`, which exports only to the
  modules in `KVM_SUB_MODULES` and expands to nothing without it.
- Restrictions: `WARN_ON_ONCE()` plus `-EINVAL` when
  `mem->slot < KVM_USER_MEM_SLOTS` or when `mem->flags` is non-zero.
- Id test: compares the whole `mem->slot`, address-space bits included, so
  it bounds the id only for address space 0;
  `kvm_vm_ioctl_set_memory_region()` compares `(u16)mem->slot`.
- `kvm->slots_lock`: `kvm_set_internal_memslot()` neither takes nor asserts
  it; the caller takes it, and `kvm_set_memory_region()` asserts it.
- Ioctl path: `kvm_vm_ioctl_set_memory_region()` takes `slots_lock` itself
  with `guard(mutex)`.
- Callers: x86 `__x86_set_memory_region()` and s390 `kvm_arch_init_vm()`.

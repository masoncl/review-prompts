- Generated header: `hyp_constants.h`, made by `arch/arm64/kvm/Makefile` and
  included by `arch/arm64/kvm/pkvm.c`.
- Host VM size: computed inline in `__pkvm_create_hyp_vm()`.
  `pkvm_get_hyp_vm_size()` is a static EL2 function in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c`; the host cannot call it.
- No size crosses the hypercall: `__pkvm_init_vm()` and `__pkvm_init_vcpu()`
  get the host VA of the area with no size, and donate `PAGE_ALIGN()` of
  EL2's own size from it.
- If EL2's size exceeds the host's allocation, EL2 takes whatever host-owned
  pages follow it, or the donation fails; nothing compares the two sizes.
- `struct pkvm_hyp_vm` embeds `struct kvm`, `struct pkvm_hyp_vcpu` embeds
  `struct kvm_vcpu`: a field added to either, or to `struct kvm_arch` or
  `struct kvm_vcpu_arch`, grows the donation too.
- **Unsafe usage**: a member under `#ifdef __KVM_NVHE_HYPERVISOR__` in either
  structure or in a structure they embed.
  - Unsafe: `arch/arm64/kvm/hyp/hyp-constants.c` is built by
    `arch/arm64/kvm/Makefile` without `-D__KVM_NVHE_HYPERVISOR__`, EL2 code is
    built with it (`arch/arm64/kvm/hyp/nvhe/Makefile`), so the host constant
    and EL2's `sizeof()` differ.
  - Safe: a member whose presence depends only on a `CONFIG_` symbol, as
    `debugfs_nv_dentry` in `struct kvm_arch` under
    `CONFIG_PTDUMP_STAGE2_DEBUGFS`; both builds see the same layout.
- New field at EL2: starts as zero (`map_donated_memory()`). The hyp copy is
  separate from the host's; a host value arrives only where EL2 copies it, for
  example `init_pkvm_hyp_vcpu()`, `pkvm_init_features_from_host()` or
  `flush_hyp_vcpu()`.
- New field that owns a resource: release it in
  `__pkvm_finalize_teardown_vm()` before `teardown_donated_memory()` clears the
  object. There is no __pkvm_teardown_vm().
- Alignment: both sides round the size with `PAGE_ALIGN()`;
  `map_donated_memory_noclear()` returns `NULL` unless the address is
  page-aligned.

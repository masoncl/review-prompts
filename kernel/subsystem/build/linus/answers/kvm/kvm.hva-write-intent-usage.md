- Read-only slots exist only where `kvm_arch_has_readonly_mem()` is true;
  otherwise `check_memory_region_flags()` rejects `KVM_MEM_READONLY`. Search
  for `select HAVE_KVM_READONLY_MEM` to list the architectures.
- **Potentially unsafe usage**: translating with `gfn_to_hva()`,
  `gfn_to_hva_memslot()` or `kvm_vcpu_gfn_to_hva()` on a path that reads.
  - Unsafe: the architecture selects `HAVE_KVM_READONLY_MEM` and the path
    never writes the address; on a read-only slot `__gfn_to_hva_many()`
    returns `KVM_HVA_ERR_RO_BAD` and the read fails as a bad address.
  - Safe: the architecture does not select `HAVE_KVM_READONLY_MEM`, as for
    `kvmppc_mmu_book3s_64_get_pteg()`.
  - Safe: the path then writes the same address, as
    `kvm_update_stolen_time()` in `arch/arm64/kvm/pvtime.c` does with
    `kvm_get_guest()` and `kvm_put_guest()`.
- Read helpers built on write intent, which fail on a read-only slot:
  - `kvm_get_guest()`: `__kvm_get_guest()` uses `gfn_to_hva()`.
  - `kvm_read_guest_cached()`, `kvm_read_guest_offset_cached()`:
    `__kvm_gfn_to_hva_cache_init()` uses `gfn_to_hva_many()`; `-EFAULT`.
  - `kvm_is_gpa_in_memslot()`: uses `gfn_to_hva()`; returns false.
  - `kvm_gpc_activate()`: `__kvm_gpc_refresh()` uses `gfn_to_hva_memslot()`;
    `-EFAULT`.
- **Unsafe usage**: reading `writable` after a call to `gfn_to_hva_prot()`,
  `gfn_to_hva_memslot_prot()` or `kvm_vcpu_gfn_to_hva_prot()` without testing
  the hva first; `gfn_to_hva_memslot_prot()` writes `*writable` only when
  `!kvm_is_error_hva(hva)`.
  - Safe: test `kvm_is_error_hva()` and return before reading it, as
    `__kvm_at_swap_desc()` in `arch/arm64/kvm/at.c` does.
  - Safe: test it in the same condition, before `writable`, as
    `kvm_handle_guest_abort()` does.
- x86 walker: `FNAME(walk_addr_generic)` calls `kvm_vcpu_gfn_to_memslot()` and
  then `gfn_to_hva_memslot_prot()`, not `kvm_vcpu_gfn_to_hva_prot()`; the
  result goes to `walker->pte_writable[]`.
- There is no kvm_read_guest_atomic() here; `kvm_vcpu_read_guest_atomic()`
  calls the static `__kvm_read_guest_atomic()`, which passes a NULL
  `writable`.
- `kvm_host_page_size()`: calls `kvm_vcpu_gfn_to_hva_prot(vcpu, gfn, NULL)`.
- s390: `arch/s390/kvm/s390/gaccess.c` calls none of
  `gfn_to_hva_prot()`, `gfn_to_hva_memslot_prot()` and
  `kvm_vcpu_gfn_to_hva_prot()`, and s390 does not select
  `HAVE_KVM_READONLY_MEM`.

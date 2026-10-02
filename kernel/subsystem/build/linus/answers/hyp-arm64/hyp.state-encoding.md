- All-zero `struct hyp_page`: host sees `PKVM_PAGE_OWNED`, hyp sees
  `PKVM_NOPAGE`, because `get_hyp_state()` XORs `__hyp_state_comp` with
  `PKVM_PAGE_STATE_VMEMMAP_MASK`.
- Hyp stage-1 PTEs: SW bits are not kept in step with the hyp state;
  `pkvm_mkstate()` is called only for guest stage-2 maps, and
  `fix_host_ownership_walker()` in `arch/arm64/kvm/hyp/nvhe/setup.c` is the
  only reader of hyp SW bits.
- Non-memory addresses: have no ownership record at all;
  `host_stage2_set_owner_metadata_locked()` and the `PKVM_ID_HOST` case of
  `host_stage2_set_owner_locked()` return `-EPERM` for them.
- `guest_get_page_state()`: tests `guest_pte_is_poisoned()` before validity, so
  a poisoned entry is `PKVM_POISON`, not `PKVM_NOPAGE`, and fails a
  `__guest_check_page_state_range()` for `PKVM_NOPAGE` with `-EPERM`.
- `__hyp_check_page_state_range()`: has no memory check and no lock assertion
  of its own.
- **Potentially unsafe usage**: `hyp_phys_to_page()`, `get_host_state()`,
  `get_hyp_state()` or `for_each_hyp_page()` on a physical address.
  - Unsafe: when nothing earlier showed the address lies in a `hyp_memory`
    region; `hyp_back_vmemmap()` backs the vmemmap only for those regions.
  - Safe: after `check_range_allowed_memory()`, as
    `__host_check_page_state_range()` and `__pkvm_host_share_guest()` do.
  - Safe: after `addr_is_memory()`, as `host_stage2_get_guest_info()` and
    `check_page_ownership()` in `arch/arm64/kvm/hyp/nvhe/mm.c` do.
  - Safe: `__hyp_check_page_state_range()` after
    `__host_check_page_state_range()` passed on the same range, as in
    `__pkvm_host_donate_hyp()`.
  - Safe: on an address taken from hyp's own allocation, as
    `reclaim_pgtable_pages()` passes to `__pkvm_hyp_donate_host()`, which has
    no hypercall handler.
  - Safe: on memory that `__pkvm_host_donate_hyp()` accepted earlier, as
    `__unmap_donated_memory()` passes to `__pkvm_hyp_donate_host()`.
- **Potentially unsafe usage**: `pkvm_getstate()` directly on a guest PTE.
  - Unsafe: when the PTE may be invalid; an empty or poisoned entry has zero
    SW bits and decodes as `PKVM_PAGE_OWNED`.
  - Safe: after `get_valid_guest_pte()` succeeded, as
    `__pkvm_guest_share_host()` does; it rejects poisoned, invalid and
    non-last-level entries.
  - Safe: through `guest_get_page_state()`.

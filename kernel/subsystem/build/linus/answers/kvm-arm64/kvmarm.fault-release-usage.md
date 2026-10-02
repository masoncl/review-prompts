- Release helper per exit of the `user_mem_abort()` chain:

| Exit | Released by | Helper | Lock |
|---|---|---|---|
| `__kvm_faultin_pfn()` gave an error pfn | nobody | none | n/a |
| cacheable PFNMAP, no `kvm_supports_cacheable_pfnmap()` | `kvm_s2_fault_pin_pfn()` | `kvm_release_faultin_page()`, `unused` true | not held |
| `kvm_s2_fault_compute_prot()` returned nonzero | `user_mem_abort()` | `kvm_release_page_unused()` | not held |
| any exit of `kvm_s2_fault_map()` | `kvm_s2_fault_map()` | `kvm_release_faultin_page()`, `unused` = `!!ret` | held |

- `kvm_s2_fault_compute_prot()` nonzero covers `-ENOEXEC`, the MTE `-EFAULT`,
  and 1 after an exclusive/atomic injection.
- `kvm_s2_fault_map()` exits include the `mmu_invalidate_retry()` hit and a
  `transparent_hugepage_adjust()` error; `ret` is still `-EAGAIN` or the
  error there, so `unused` is true.
- `dirty` argument: `prot & KVM_PGTABLE_PROT_W`, the final permission, not
  `map_writable` from the faultin; same in `gmem_abort()`.
- `s2vi->page`: NULL when the pfn has no refcounted page; on NULL both
  helpers put nothing, but `kvm_release_faultin_page()` makes its lock
  assertion first.
- **Unsafe usage**: returning after `kvm_s2_fault_pin_pfn()` returned 1
  without releasing `s2vi.page`; the reference from `__kvm_faultin_pfn()`
  leaks.
  - Safe: `kvm_release_page_unused()` before the return, as
    `user_mem_abort()` does when `kvm_s2_fault_compute_prot()` returns
    nonzero.
  - Safe: returning the result of `kvm_s2_fault_map()`, as
    `user_mem_abort()` does; `kvm_s2_fault_map()` releases the page at its
    `out_unlock` label, which every path reaches.
  - Safe: returning with no release when `kvm_s2_fault_pin_pfn()` returned 0
    or an error, as `user_mem_abort()` does; `__kvm_faultin_pfn()` leaves the
    page NULL with an error pfn, and the `-EFAULT` exit after it has already
    released the page.
- **Unsafe usage**: releasing `s2vi->page` after `kvm_s2_fault_map()`
  returned; it has released the page on every path, so this is a second put.
  - Safe: return its result directly, as `user_mem_abort()` does.
- **Potentially unsafe usage**: calling `kvm_release_faultin_page()` without
  `mmu_lock` held.
  - Unsafe: with `unused` false; under `CONFIG_LOCKDEP` the
    `lockdep_assert_once()` in `kvm_release_faultin_page()` in
    `include/linux/kvm_host.h` fires.
  - Safe: with `unused` true, which that assertion exempts, as
    `kvm_s2_fault_pin_pfn()` does.
- `pkvm_mem_abort()`: does not call `__kvm_faultin_pfn()` or either release
  helper.
  - It calls `account_locked_vm()`, then `pin_user_pages()` with
    `FOLL_HWPOISON | FOLL_LONGTERM | FOLL_WRITE` under `mmap_read_lock()`.
  - Success: the pin and the locked-vm charge are kept;
    `__pkvm_pgtable_stage2_reclaim()` in `arch/arm64/kvm/pkvm.c` drops both
    with `unpin_user_pages_dirty_lock()` and `account_locked_vm()`.
  - Map failure, including `-EAGAIN` (returned as 0): `unpin_user_pages()`
    then `account_locked_vm(mm, 1, false)`.
  - Pin failure: only the charge is undone; `-EHWPOISON` sends the signal
    and returns 0.
  - Folio not `folio_test_swapbacked()`: `-EIO`, pin and charge undone.

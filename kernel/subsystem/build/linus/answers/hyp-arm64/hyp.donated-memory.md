- `map_donated_memory()` failure: returns `NULL` for any cause;
  `__pkvm_init_vm()` and `__pkvm_init_vcpu()` report `-ENOMEM`.
- VM size: `pkvm_get_hyp_vm_size()` of `READ_ONCE(host_kvm->created_vcpus)`.
  The same value is stored in `hyp_vm->kvm.created_vcpus` and bounds `vcpus[]`.
- Clearing on map: `map_donated_memory()` clears `size` bytes; the donation
  covers `PAGE_ALIGN(size)`. The tail of the last page keeps host content.
- PGD: taken with `map_donated_memory_noclear()`. `hyp_pool_init()` in
  `kvm_guest_prepare_stage2()` zeroes it, through `__hyp_attach_page()`.
- Hand-back paths:

| Path | Function | Clears | Goes to |
|---|---|---|---|
| init error | `unmap_donated_memory()` | `size` bytes | host frees with `free_pages_exact()` |
| VM, vCPU at teardown | `teardown_donated_memory()` | `PAGE_ALIGN(size)`, before the link is written | `teardown_mc` |
| PGD, stage-2 tables at teardown | `reclaim_pgtable_pages()` | no; pool pages are already zero | `stage2_teardown_mc` |
| unused hyp vCPU memcache pages | `unmap_donated_memory_noclear()` | no | `stage2_teardown_mc` |

- `__pkvm_hyp_donate_host()`: returns `-EBUSY` if any page has a non-zero
  `refcount` in `struct hyp_page` (`__hyp_check_page_count_range()`).
  `__unmap_donated_memory()` wraps the call in `WARN_ON()`.
- `reclaim_pgtable_pages()`: sets `page->refcount = 0` before each donation for
  that reason.
- Host after teardown: `free_hyp_memcache()` frees page by page with
  `free_page()`. `__pkvm_create_hyp_vm()` and `__pkvm_create_hyp_vcpu()`
  allocate with `alloc_pages_exact()` so each page can be freed alone.
- **Potentially unsafe usage**: handing memory back to the host without
  clearing it.
  - Unsafe: when EL2 wrote hyp or guest state into the pages and nothing has
    zeroed them since.
  - Safe: after `teardown_donated_memory()` has cleared the object; it then
    calls `unmap_donated_memory_noclear()`.
  - Safe: pages drained from `hyp_vm->pool`, as in `reclaim_pgtable_pages()`;
    `__hyp_attach_page()` zeroed them when they were freed.
  - Safe: pages still in the hyp vCPU memcache, as in
    `__pkvm_finalize_teardown_vm()`; EL2 wrote only the link into them.

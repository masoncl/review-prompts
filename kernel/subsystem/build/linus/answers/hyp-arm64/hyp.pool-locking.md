- `get_page` and `put_page` callbacks of the three pools
  (`hpool_get_page()`, `hpool_put_page()`, `host_s2_get_page()`,
  `host_s2_put_page()`, `guest_s2_get_page()`, `guest_s2_put_page()`): call
  `hyp_get_page()` or `hyp_put_page()`, so they take the pool lock.
- `get_page` and `put_page` of `hyp_early_alloc_mm_ops`
  (`arch/arm64/kvm/hyp/nvhe/early_alloc.c`): empty functions; no count is
  changed and no lock is taken.
- Helpers that rely on the caller: `hyp_page_ref_inc()`,
  `hyp_page_ref_dec()`, `hyp_page_ref_dec_and_test()` and
  `hyp_set_page_refcounted()` in
  `arch/arm64/kvm/hyp/include/nvhe/memory.h`, and `hyp_split_page()`.
- Refcount changes without the pool lock; search for `refcount` and the
  helpers above under `arch/arm64/kvm/hyp/nvhe` for the sites:

| Where | Page | What protects the count |
|---|---|---|
| `hyp_pin_shared_mem()`, `hyp_unpin_shared_mem()` | host page shared with hyp, in no pool | `host_mmu.lock` and `pkvm_pgd_lock` |
| `get_pkvm_hyp_vm()`, `put_pkvm_hyp_vm()`, `pkvm_load_hyp_vcpu()`, `pkvm_put_hyp_vcpu()` | page holding the donated `struct pkvm_hyp_vm`, in no pool | `vm_table_lock` |
| `guest_s2_zalloc_page()`, `refcount = 1` | page just popped from the memcache | not yet linked into a table; caller holds the VM's `lock` |
| `reclaim_pgtable_pages()`, `refcount = 0` | page just allocated from the VM pool | sole owner; VM already removed from `vm_table` |
| `hyp_split_page()` | tails of a block just allocated | sole owner |
| `hyp_pool_init()` | every page of the range | pool not yet in use |
| `pkvm_ownership_selftest()`, `init_selftest_vm()` | selftest pages, `CONFIG_NVHE_EL2_DEBUG` only | run from `__pkvm_init_finalise()` |

- Memcache page after `guest_s2_zalloc_page()`: later changes go through
  `guest_s2_get_page()` and `guest_s2_put_page()`, under the VM pool's lock.
- `__hyp_check_page_count_range()`: reads `refcount` under `host_mmu.lock`
  and `pkvm_pgd_lock`; `__pkvm_host_unshare_hyp()` and
  `__pkvm_hyp_donate_host()` return `-EBUSY` when it is non-zero.
- `get_pkvm_unref_hyp_vm_locked()`: reads the VM page's count with
  `hyp_page_count()` under `vm_table_lock`.

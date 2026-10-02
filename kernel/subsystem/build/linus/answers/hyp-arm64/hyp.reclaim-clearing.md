- `hyp_poison_page()`: two callers only,
  `__pkvm_host_force_reclaim_page_guest()` and
  `__pkvm_host_reclaim_page_guest()`; it clears with `memset()`.
- A page the host shared with a guest (guest `PKVM_PAGE_SHARED_BORROWED`):
  `__pkvm_host_reclaim_page_guest()` returns `-EPERM`; it leaves through
  `__pkvm_host_unshare_guest()`, which clears nothing.
- `__pkvm_hyp_donate_host()`: does no clearing and no cache maintenance; a
  caller that needs either does it before the call.
- Hypervisor pages, in `arch/arm64/kvm/hyp/nvhe/pkvm.c`:

| Helper | Clears | Cache maintenance |
|---|---|---|
| `unmap_donated_memory()` | `memset()` over `size` | `kvm_flush_dcache_to_poc()` |
| `unmap_donated_memory_noclear()` | no | `kvm_flush_dcache_to_poc()` |
| `teardown_donated_memory()` | `memset()` over `PAGE_ALIGN(size)` | `kvm_flush_dcache_to_poc()` |

- The flush for all three is in `__unmap_donated_memory()`, just before
  `__pkvm_hyp_donate_host()`.
- `teardown_donated_memory()`: after the `memset()` it pushes each page on
  the teardown memcache with `push_hyp_memcache()`, then flushes and
  donates.

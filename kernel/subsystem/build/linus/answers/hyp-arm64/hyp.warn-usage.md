- **Potentially unsafe usage**: `WARN_ON()` or `BUG_ON()` on the result of a
  call or on a state test.
  - Unsafe: when a host or guest argument, a page state or a memory shortfall
    can make the condition true and nothing earlier under the same lock hold
    has excluded it; the `brk` ends in `hyp_panic()` and
    `nvhe_hyp_panic_handler()` panics the host.
  - Safe: when earlier checks under the same locks make failure impossible,
    as in `__pkvm_host_share_hyp()`: `__host_check_page_state_range()` has
    passed for `PKVM_PAGE_OWNED`, so `__host_set_page_state_range()` skips
    `host_stage2_idmap_locked()`, its only call that can fail.
  - Safe: when the asserted step allocates and the memory was checked first,
    as `__guest_check_pgtable_memcache()` returns `-ENOMEM` before
    `WARN_ON(kvm_pgtable_stage2_map(...))` in `__pkvm_host_donate_guest()`,
    which passes the fixed `KVM_PGTABLE_PROT_RWX`.
- Returned, not asserted, while nothing has been changed yet:
  `__pkvm_host_share_ffa()` returns the result of
  `__host_set_page_state_range()`, and `__pkvm_host_unshare_guest()` returns a
  `kvm_pgtable_stage2_unmap()` error before it touches page state.
- Range arguments: rejected by `pfn_range_is_valid()` (`-EINVAL`) before any
  lock is taken, and by `check_range_allowed_memory()` (`-EINVAL` or
  `-EPERM`) before any host page state is read.
- There is no host_request_owned_transition() here; the host-side check is
  `__host_check_page_state_range()`.
- `host_stage2_adjust_range()`: returns `-EEXIST` for a valid PTE, `-EPERM`
  for an annotated one, and `-EINVAL` after `WARN_ON(1)`.
- `kvm_pgtable_stage2_map()` on a guest table and the other asserted commit
  steps are wrapped in `WARN_ON()`, not `BUG_ON()`.
- Debug-only assertions: `assert_host_shared_guest()` returns at once and
  `hyp_assert_lock_held()` is an empty stub without `CONFIG_NVHE_EL2_DEBUG`,
  so neither protects a production build.

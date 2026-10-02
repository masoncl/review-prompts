- `__pkvm_host_share_hyp()`: the hyp-side check is unconditional. Of the
  page-state checks, only `assert_host_shared_guest()` is a no-op without
  `CONFIG_NVHE_EL2_DEBUG`.
- `__guest_check_pgtable_memcache()`: explicit check before a guest
  stage-2 map; `-ENOMEM` when `pkvm_memcache.nr_pages` is below
  `kvm_mmu_cache_min_pages()`.
- `__guest_check_pgtable_memcache()` runs after the state checks and before
  the first update, in `__pkvm_host_donate_guest()` and
  `__pkvm_host_share_guest()`.
- `__pkvm_guest_share_host()` and `__pkvm_guest_unshare_host()`: no
  memcache check; `get_valid_guest_pte()` limits them to an existing
  last-level leaf (`-E2BIG` otherwise).
- Checked before the locks in `__pkvm_host_share_guest()`: `prot` within
  `KVM_PGTABLE_PROT_RWX`, `pfn_range_is_valid()`,
  `__guest_check_transition_size()`, `check_range_allowed_memory()`.
- Checked, not asserted, and always the first update of its function:
  - `kvm_pgtable_stage2_unmap()` in `__pkvm_host_unshare_guest()`
  - `kvm_pgtable_stage2_annotate()` in
    `__pkvm_host_force_reclaim_page_guest()`
  - `__host_set_page_state_range()` in `__pkvm_host_share_ffa()` and
    `__pkvm_host_unshare_ffa()`
- `kvm_pgtable_stage2_unmap()` on a guest table is asserted only in
  `__pkvm_host_reclaim_page_guest()`.
- `host_stage2_set_owner_metadata_locked()`: asserted with `WARN_ON()` in
  `__pkvm_host_donate_guest()` and `__pkvm_guest_unshare_host()`.
- `__pkvm_host_reclaim_page_guest()`: the host-side state check is itself
  asserted with `WARN_ON()`, after the guest state has been checked.
- **Unsafe usage**: in a transition function in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c`, changing state on either side
  before the last check that can return an error; no transition function
  has an undo path.
  - Safe: check the whole range, then update it in a second pass, as
    `__pkvm_host_share_guest()` does.
  - Safe: make the one fallible update first and return its error, as
    `__pkvm_host_unshare_guest()` does with `kvm_pgtable_stage2_unmap()`.
  - Safe: after the last returning check, wrap every update in
    `WARN_ON()`, as `__pkvm_host_donate_guest()` does.

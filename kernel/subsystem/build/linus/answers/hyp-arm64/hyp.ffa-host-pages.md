- `__ffa_host_share_ranges()`: tests `PAGE_ALIGNED(sz | range->address)`, so
  the address as well as the size must be aligned to the kernel `PAGE_SIZE`.
- `__pkvm_host_share_ffa()` in `arch/arm64/kvm/hyp/nvhe/mem_protect.c`: also
  fails for a range beyond the host IPA space (`pfn_range_is_valid()`), and
  for one that is not memory or is `MEMBLOCK_NOMAP`
  (`check_range_allowed_memory()`).
- `ffa_host_share_ranges()`: turns every such failure into `FFA_RET_DENIED`;
  the errno is dropped.
- A page named in two ranges of one descriptor: the second share finds it
  `PKVM_PAGE_SHARED_OWNED` and the whole call gets `FFA_RET_DENIED`.
- Lend and share: identical at EL2; `func_id` is used only as the id of the
  SMC.
- Fragmented first call (`fraglen != len`): succeeds only on
  `FFA_MEM_FRAG_RX` with `a3 == fraglen`; anything else goes to
  `err_unshare`.
- EL3 failure: `ret` stays 0, so EL3's registers reach the host unchanged
  after the unshare.
- Later fragment fails in `do_ffa_mem_frag_tx()`: only that fragment's ranges
  are rolled back; pages of earlier fragments stay
  `PKVM_PAGE_SHARED_OWNED`, because their descriptors are no longer held.
  The `ffa_mem_reclaim()` there tells EL3 to drop the handle; it does not
  touch host page state.

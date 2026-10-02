- `FFA_FN64_RXTX_MAP` query: forwarded; EL3's minimum size reaches the host
  unchanged. `FFA_RXTX_MAP` query: `FFA_RET_NOT_SUPPORTED`.
- Answered at EL2 with `FFA_SUCCESS` and properties 0: only `FFA_MEM_SHARE`,
  `FFA_FN64_MEM_SHARE`, `FFA_MEM_LEND`, `FFA_FN64_MEM_LEND`. Every other id
  not on the deny list makes `do_ffa_features()` return false, and the query
  is forwarded.
- Calls EL2 handles itself, other than share and lend: their feature query is
  answered by EL3, so the answer does not reflect EL2's own limits; for
  example `do_ffa_rxtx_map()` accepts exactly
  `KVM_FFA_MBOX_NR_PAGES * PAGE_SIZE / FFA_PAGE_SIZE` pages.
- `ffa_call_supported()`: does not look at `hyp_ffa_version`; an id on the
  list is refused at every agreed version.
- New optional interface not implemented at EL2: models have this right; add
  a `case` to `ffa_call_supported()` in `arch/arm64/kvm/hyp/nvhe/ffa.c`.

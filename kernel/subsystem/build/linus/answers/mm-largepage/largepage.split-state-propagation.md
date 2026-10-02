- New head pages: `flags.f &= ~PAGE_FLAGS_CHECK_AT_PREP` clears every flag but
  hwpoison before the masked copy, so a flag outside the mask is lost,
  `PG_anon_exclusive` included; young and idle are set again by
  `folio_set_young()` and `folio_set_idle()`.
- Copy mask: includes `PG_mlocked`, `PG_locked`, `PG_swapcache` and
  `PG_dropbehind`.
- `folio_split_memcg_refs()`, `split_page_owner()`, `pgalloc_tag_split()`:
  called by `__split_unmapped_folio()` before `__split_folio_to_order()`,
  not inside it.
- `zone_device_private_split_cb()`, LRU, page cache and swap cache slots,
  unfreeze: done by `__folio_freeze_and_split_unmapped()`.
- Last cpupid: `folio_xchg_last_cpupid()`; there is no
  page_cpupid_xchg_last() here.
- `split_page_memcg()`: exists but is not used by the folio split.
- `_deferred_list`, mapcount fields, `_pincount` of a new large folio:
  re-initialised by `prep_compound_page()`, not copied.
- `PG_partially_mapped` and deferred-list membership: removed from the old
  folio at freeze time; no piece is queued again.
- `private` on a new head: `VM_WARN_ON_ONCE_PAGE()` only, not cleared.
- `_mapcount` on a new head: asserted to be -1, not reset.
- A change that adds per-folio state must:
  - add a head-page flag to the mask;
  - read state kept in the second page (`PAGE_FLAGS_SECOND`) before the loop,
    which overwrites that page when it becomes a head, as `handle_hwpoison`
    does;
  - set second-page state after `prep_compound_page()`;
  - fix the first piece separately: the loop skips it, and apart from the
    `PG_has_hwpoisoned` handling before the loop only `folio_set_order()` or
    `ClearPageCompound()` touch it;
  - tolerate repeated calls: a non-uniform split calls the function once per
    order, each time on the piece containing `split_at`;
  - not sleep: both callers of `__folio_freeze_and_split_unmapped()` have
    IRQs off and the folio is frozen;
  - put per-page accounting in `__split_unmapped_folio()`.

- `enum folio_references` in `mm/vmscan.c` has three values:
  `FOLIOREF_RECLAIM`, `FOLIOREF_KEEP`, `FOLIOREF_ACTIVATE`; there is no
  FOLIOREF_RECLAIM_CLEAN.
- No reference, classic LRU: `FOLIOREF_RECLAIM` whether or not
  `PG_referenced` was set; the flag is cleared by
  `folio_test_clear_referenced()`.
- `folio_referenced()` fills a `vma_flags_t`; the tests are
  `vma_flags_test()` on `VMA_LOCKED_BIT` and, in `is_exec_file_folio()`, on
  `VMA_EXEC_BIT`.
- Return value of `folio_referenced()`: counts VMAs that referenced the
  folio, not PTEs; "more than once" means more than one VMA.
- Classic LRU, swap-backed anon folio, one reference, `PG_referenced` clear:
  `FOLIOREF_KEEP`, same as a non-exec file folio.
- Return of -1 has two causes: rmap lock contention (`rwc.contended`), or
  `folio_referenced_one()` found a non-shared swap-backed anon folio mapped
  by an exiting or OOM-reaped mm. Both give `FOLIOREF_KEEP`.
- `VMA_LOCKED_BIT` is tested before the -1 test, so it wins.
- Zero can hide references: `invalid_folio_referenced_vma()` skips VMAs
  without `vma_has_recency()` and, under cgroup reclaim, VMAs of an mm
  outside `sc->target_mem_cgroup`.
- MGLRU branch: taken when `lru_gen_enabled() && !lru_gen_switching()`;
  while switching, the classic rules apply.
- MGLRU, any reference: the count is ignored and `lru_gen_set_refs()`
  decides:

| Folio flags on entry | Result |
|---|---|
| neither `PG_referenced` nor `PG_workingset`, exec file folio | sets `PG_workingset`, `FOLIOREF_ACTIVATE` |
| neither flag, any other folio | sets `PG_referenced`, `FOLIOREF_KEEP` |
| either flag set | `FOLIOREF_ACTIVATE` |

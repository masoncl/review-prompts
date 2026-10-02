- Flags type: `tlbf_t`, a `__bitwise` type in
  `arch/arm64/include/asm/tlbflush.h`; `__flush_tlb_range()` and
  `__flush_tlb_page()` both end in `__do_flush_tlb_range()`, which interprets
  the flags.

| Flag | Changes | A caller |
|---|---|---|
| `TLBF_NONE` | broadcast, drops walk cache, notifies, waits | `flush_tlb_range()` |
| `TLBF_NOWALKCACHE` | leaf-only op (`vale1is` instead of `vae1is`) | `contpte_convert()` |
| `TLBF_NOSYNC` | no completing barrier | `__ptep_clear_flush_young()`, `arch_tlbbatch_add_pending()` |
| `TLBF_NONOTIFY` | no `mmu_notifier_arch_invalidate_secondary_tlbs()` call | `flush_tlb_fix_spurious_fault()` |
| `TLBF_NOBROADCAST` | local op `vale1`, `dsb(nshst)` before, `dsb(nsh)` after | `__ptep_set_access_flags_anysz()` in `arch/arm64/mm/fault.c` |

- `__flush_tlb_page()`: ORs in `TLBF_NOWALKCACHE` itself and uses level 3.
- Refused combination: `TLBF_NOBROADCAST` without `TLBF_NOWALKCACHE` hits
  `BUG()` at run time in `__do_flush_tlb_range()`; there is no build-time
  check.
- `__flush_tlb_page()` cannot reach that `BUG()`, since it always adds
  `TLBF_NOWALKCACHE`.
- Limit excess in `__do_flush_tlb_range()`: it calls `flush_tlb_mm()` and
  returns before any flag is tested, so the flush is broadcast, drops the
  walk cache, waits and notifies whatever flags were passed.
- `TLBF_NOBROADCAST` without `TLBF_NOSYNC`: completion is a bare
  `dsb(nsh)`, not `__tlbi_sync_s1ish()`.
- `TLBF_NOBROADCAST` without `TLBF_NONOTIFY`: the notifier is still called,
  as in `__ptep_set_access_flags_anysz()`.
- **Potentially unsafe usage**: `TLBF_NOSYNC`.
  - Unsafe: when the entry was unmapped or made stricter and nothing later
    completes the invalidation before the caller relies on it.
  - Safe: `arch_tlbbatch_add_pending()`; `arch_tlbbatch_flush()` later runs
    `__tlbi_sync_s1ish_batch()`.
  - Safe: `__ptep_clear_flush_young()`; `__ptep_test_and_clear_young()`
    clears only the access flag, so a stale entry maps the same page.
- **Potentially unsafe usage**: `TLBF_NOBROADCAST`.
  - Unsafe: when the change unmaps or reduces permission; other CPUs keep
    the old entry.
  - Safe: when the change only makes the entry more permissive and a later
    fault on it goes through `handle_pte_fault()`, as for
    `__ptep_set_access_flags()`; a CPU with a stale entry takes a write
    fault and `fix_spurious_fault()` in `mm/memory.c` calls
    `flush_tlb_fix_spurious_fault()`.

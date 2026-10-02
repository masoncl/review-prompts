- `walk_pte_range()` when the PTE table cannot be mapped: sets
  `walk->action = ACTION_AGAIN` and returns 0; it does not return `-EAGAIN`.
- `walk_pmd_range()` on `ACTION_AGAIN`: jumps back and re-reads the PMD.
- Retry with the PMD now none, in a walk without `install_pte`: the walker
  calls `pte_hole` if set and moves on; `pmd_entry` is not called again.
- Retry with the PMD not none: `pmd_entry` runs again, then
  `split_huge_pmd()`, then the mapping is tried again.
- Ops with both `pmd_entry` and `pte_entry`: `pmd_entry` can run more than
  once for one PMD because of the walker's own retry, so it must tolerate a
  repeat even if it never sets `ACTION_AGAIN`.
- **Potentially unsafe usage**: setting `ACTION_AGAIN` from `pmd_entry`.
  - Unsafe: when the PMD state that made the callback set it can still be
    there on the retry and the callback sets it again; `walk_pmd_range()` has
    no retry limit and loops with the caller's locks held.
  - Safe: straight after `pte_offset_map_lock()` returned NULL, in a callback
    that first took `pmd_is_huge()` entries through `pmd_trans_huge_lock()`,
    as `smaps_pte_range()` in `fs/proc/task_mmu.c` does.
  - Safe: `__pte_offset_map()` in `mm/pgtable-generic.c` defines the failing
    states: none, non-present, `pmd_trans_huge()`, or bad and then cleared. On
    the retry the walker takes a none PMD and the huge branch takes the rest.

- Queuers, complete list for this tree:

| Site | Condition | `partially_mapped` |
| --- | --- | --- |
| `__folio_remove_rmap()` | see next bullets | true |
| `map_anon_folio_pmd_nopf()` | every new PMD-mapped anon THP, while `split_underused_thp` is on | false |
| `migrate_folio_move()` | src was queued before the move | src's flag |
| `deferred_split_scan()` | requeue, see below | unchanged |

- `__do_huge_pmd_anonymous_page()` does not call `deferred_split_folio()`
  itself; fault paths and `collapse_huge_page()` reach it through
  `map_anon_folio_pmd_nopf()`.
- `collapse_huge_page()` below PMD order: maps with
  `map_anon_folio_pte_nopf()`, which does not queue.
- `__folio_remove_rmap()` test: partially mapped, anon,
  `!folio_test_partially_mapped()` and `!folio_is_device_private()`.
- A folio in the swapcache: the rmap test passes but
  `deferred_split_folio()` returns early; the folio is not queued and the
  flag stays clear.
- Partially mapped under `CONFIG_NO_PAGE_MAPCOUNT`: decided from the folio's
  total mapcount, not per page; at PTE level it means mapcount non-zero,
  below the folio's page count, and no entire mapping.
- PMD-level removal queues too: when the last entire mapping goes away and
  PTE mappings of some but not all pages remain.
- `deferred_split_scan()` requeues with `list_lru_add_irq()` when the split
  did not happen and the folio is partially mapped, or when
  `folio_trylock()` failed.
- Callers of the rmap helpers do nothing about the queue themselves; the
  final put unqueues (see "Leaving the deferred split queue").
- **Unsafe usage**: calling `folio_remove_rmap_ptes()` or
  `folio_remove_rmap_pmd()` on an anon large folio whose refcount is already
  zero or frozen.
  - Unsafe: `folio_unqueue_deferred_split()` tests `list_empty()` without the
    lock and assumes nobody adds once the refcount is zero; a late add leaves
    a freed folio on the queue.
  - Safe: remove the rmap first, then drop the mapping's reference, as
    `try_to_unmap_one()` does; the unqueue in `__folio_put()` and
    `folios_put_refs()` runs only after the last reference is gone.
- Code that replaces a folio: unqueue the old one while it is frozen and
  still charged, as `__folio_migrate_mapping()` does.
- The replacement folio: does not inherit the queue entry; only an explicit
  `deferred_split_folio()` call puts it there. `migrate_folio_move()` samples
  `_deferred_list` and the flag of src before `move_to_new_folio()`.
- No memcg charge-moving code exists in this tree.

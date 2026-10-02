- `pgattr_change_is_safe()` mask: `PTE_PXN | PTE_RDONLY | PTE_WRITE | PTE_NG |
  PTE_SWBITS_MASK`, nothing else.
- `pgattr_change_is_safe()` tests before the mask: true when old or new is
  not valid; false for a pfn change and for a change that clears `PTE_NG`.
- Not in the mask, so a change is rejected: for example `PTE_USER`,
  `PTE_UXN`, `PTE_GP`, `PTE_AF`, `PTE_CONT`.
- `PTE_CONT`: there is no test for it; only a change of the bit is rejected,
  by the mask comparison.
- `MT_NORMAL` and `MT_NORMAL_TAGGED`: `PTE_ATTRINDX_MASK` is added to the mask
  when old and new are each one of the two, in either direction; there is no
  MTE test.
- `BUG_ON(!pgattr_change_is_safe())`: in `init_pte()`, `init_pmd()` and
  `alloc_init_pud()` only; `alloc_init_cont_pmd()` has none.
- `pmd_set_huge()` and `pud_set_huge()`: return 0 and leave the entry
  unchanged when `pgattr_change_is_safe()` fails.
- `init_pmd()` and `alloc_init_pud()` on such a refusal: `WARN_ON()` fires;
  the `BUG_ON()` after it compares the old value with the unchanged entry.
- `alloc_init_cont_pte()` and `alloc_init_cont_pmd()`: do not add `PTE_CONT`
  when `pte_range_has_valid_noncont()` or `pmd_range_has_valid_noncont()`
  finds a valid entry without it.
- `__check_safe_pte_update()`: called from `__set_ptes_anysz()` before each
  store, not from `__set_pte_complete()`.
- `__check_safe_pte_update()` tests nothing unless `CONFIG_DEBUG_VM` is on,
  old and new are both valid, and the mm is `current->active_mm` or has
  `mm_users` above 1.
- `__check_safe_pte_update()` issues three `VM_WARN_ONCE()`; the store still
  happens:

| Condition | Message |
|---|---|
| new entry not young, whatever the old was | "racy access flag clearing" |
| old entry writable and new entry not dirty | "racy dirty state clearing" |
| `!pgattr_change_is_safe()` | "unsafe attribute change" |

- Unchecked writers: `__set_pte()`, `set_pmd()` and `set_pud()` call neither
  check; the `pageattr_ops` walkers in `arch/arm64/mm/pageattr.c` and the
  split helpers use them.
- `set_memory_x()` and `set_memory_nx()`: change `PTE_MAYBE_GP` (`PTE_GP` when
  `system_supports_bti_kernel()`), which is outside the mask, through those
  unchecked writers.

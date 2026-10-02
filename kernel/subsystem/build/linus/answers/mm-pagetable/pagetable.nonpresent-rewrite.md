- `change_softleaf_pte()`: exists, static in `mm/mprotect.c`, called for
  every non-present, non-empty PTE.
- Child uffd bit at fork: cleared unless `userfaultfd_protected(dst_vma)`,
  that is WP or RWP; same test in `copy_huge_non_present_pmd()`.

| Entry | Fork, `copy_nonpresent_pte()` | Protection change, `change_softleaf_pte()` |
|---|---|---|
| swap | exclusive cleared in parent and child, with no COW test; soft-dirty kept | unchanged |
| migration write | to read if `vma_is_cow_mapping(dst_vma)`; soft-dirty, uffd, A/D kept | to read-exclusive (anon) or read; soft-dirty and A/D kept, uffd not copied |
| migration read-exclusive | same as write | unchanged |
| device-private write | to read if `vma_is_cow_mapping(dst_vma)`; uffd kept, soft-dirty dropped | to read; uffd kept, soft-dirty dropped |
| device-private read, migration read, hwpoison | copied as is | unchanged |
| device-exclusive | restored to a present PTE by `try_restore_exclusive_pte()`, then copied as present | unchanged |
| poison or guard marker | `copy_pte_marker()` | returns before any uffd change |
| uffd-wp marker | `copy_pte_marker()` | cleared on a resolve flag, else untouched |

- uffd flags on protection change: `MM_CP_UFFD_WP` or `MM_CP_UFFD_RWP` sets
  `pte_swp_mkuffd()`; `MM_CP_UFFD_WP_RESOLVE` or `MM_CP_UFFD_RWP_RESOLVE`
  clears it; applied after the per-kind rewrite to every row except markers.
- PMD fork, `copy_huge_non_present_pmd()`: rewrites migration write and
  read-exclusive to read with no `vma_is_cow_mapping()` test; the
  device-private rewrite keeps both soft-dirty and uffd.
- PMD protection change, `change_non_present_huge_pmd()`: same bit rules as
  the PTE column, so device-private drops soft-dirty there but not at PMD
  fork.
- PMD paths run only when `thp_migration_supported()` and
  `pmd_is_valid_softleaf()`.

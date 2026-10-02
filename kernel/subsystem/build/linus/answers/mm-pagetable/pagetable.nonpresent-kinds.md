| Kind | Folio ref + mapcount | PMD can hold it |
|---|---|---|
| `SOFTLEAF_NONE` | not an entry; also what `softleaf_type()` gives for an unknown type | no |
| `SOFTLEAF_SWAP` | neither; it holds a swap count | no |
| `SOFTLEAF_MIGRATION_READ`, `SOFTLEAF_MIGRATION_READ_EXCLUSIVE`, `SOFTLEAF_MIGRATION_WRITE` | neither; `try_to_migrate_one()` removes the rmap and puts the folio after installing the entry | yes |
| `SOFTLEAF_DEVICE_PRIVATE_READ`, `SOFTLEAF_DEVICE_PRIVATE_WRITE` | both | yes |
| `SOFTLEAF_DEVICE_EXCLUSIVE` | both | no |
| `SOFTLEAF_HWPOISON` | neither | no |
| `SOFTLEAF_MARKER` | neither | no |

- PMD kinds, outside hugetlb: `softleaf_is_valid_pmd_entry()` accepts
  migration and device-private only; a PMD decodes to either only under
  `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`.
- `zap_nonpresent_ptes()`, migration entry: decrements `rss[mm_counter(folio)]`
  only; it does not call `folio_remove_rmap_pte()` or `folio_put()`.
- `zap_nonpresent_ptes()`, swap entry: releases with
  `swap_put_entries_direct()`; there is no free_swap_and_cache_nr() here.
- `zap_nonpresent_ptes()`, uffd-wp marker: dropped unconditionally in an
  anonymous VMA; kept in any other VMA unless `zap_drop_markers()`.
- `zap_nonpresent_ptes()`, hwpoison entry and poison marker: cleared unless
  `should_zap_cows()` is false.
- `details == NULL`: `zap_drop_markers()` is false and `should_zap_cows()` is
  true, so guard markers and file uffd-wp markers stay and poison goes.

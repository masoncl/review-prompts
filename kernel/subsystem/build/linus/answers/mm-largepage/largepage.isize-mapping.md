- `finish_fault()`: maps the whole folio or exactly one PTE. A non-shmem folio
  that crosses `file_end` sets `needs_fallback`, which forces `nr_pages = 1`
  and skips `do_set_pmd()`. No partial range is mapped.
- `do_set_pmd()`, `filemap_map_pmd()`, `set_pte_range()`: make no `i_size`
  test. The tests are in `filemap_map_pages()`, `filemap_map_folio_range()`
  and `finish_fault()`.
- `file_end` differs by one between the two sites, with the same comparison
  against `folio_next_index()`:

| Site | `file_end` | Folio that ends exactly at the last page of the file |
|---|---|---|
| `finish_fault()` | `DIV_ROUND_UP(i_size, PAGE_SIZE)` | mapped whole, PMD allowed |
| `filemap_map_pages()`, `filemap_map_folio_range()` | that value minus 1 | no PMD, PTE range clamped |

- `filemap_map_folio_range()`: maps the whole folio by PTEs only when the same
  `file_end` test as the PMD case passes; otherwise it maps only the clamped
  range.
- `filemap_map_pages()`: reads `i_size` once, at entry. The only later read is
  in `next_uptodate_folio()`, once per folio after `folio_trylock()`, and it
  tests only the current index.
- `finish_fault()` test: applies to every VMA with `vm_file`, not only to
  mappings that use `filemap_fault()`.
- `shmem_mapping()`: the only exemption. Without `CONFIG_SHMEM` it is a stub
  that returns `false`, so nothing is exempt.
- There is no try_folio_split_or_unmap() or try_folio_split_to_order() here.
  `folio_split_or_unmap()` in `mm/truncate.c` calls `folio_split()` down to
  `mapping_min_folio_order()`.
- Failed split, non-shmem: `folio_split_or_unmap()` calls `try_to_unmap()` on
  the whole folio, so pages below the new EOF are unmapped too. It does not
  call `unmap_mapping_range()` or `unmap_mapping_folio()`.
- Failed split, shmem: `folio_split_or_unmap()` does not call
  `try_to_unmap()`.
- After a failed split, `truncate_inode_partial_folio()` decides by the dirty
  flag:
  - dirty: returns `false`; the folio stays in the page cache and
    `truncate_inode_pages_range()` skips it.
  - clean: `truncate_inode_folio()` removes the whole folio, including the
    part below the new EOF.
- Zeroing of the truncated part: skipped when `mapping_inaccessible()`.
- Successful split: `__folio_freeze_and_split_unmapped()` removes the
  after-split folios at or past `end` from the page cache. `end` comes from
  `i_size`, raised by `shmem_fallocend()` for shmem.

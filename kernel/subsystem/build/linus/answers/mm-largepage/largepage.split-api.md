| Function | Target order | Pieces | Where pieces go | Kept locked + referenced |
|---|---|---|---|---|
| `split_folio()`, `split_folio_to_list()` | 0, never the mapping's min order | uniform | LRU, or `list` | first piece (the pointer passed) |
| `split_folio_to_order()` | `new_order` | uniform | LRU | first piece (the pointer passed) |
| `split_huge_page()`, `split_huge_page_to_order()`, `split_huge_page_to_list_to_order()` | 0 for `split_huge_page()`, else `new_order` | uniform | LRU, or `list` | piece containing `page` |
| `folio_split()` | `new_order` for `split_at`'s piece | non-uniform | LRU, or `list` | first piece, wherever `split_at` is |
| `folio_split_unmapped()` | `new_order` | uniform | nowhere: no LRU, no list | every piece |

- `split_huge_page()`, `split_huge_page_to_order()`,
  `split_huge_page_to_list_to_order()`: when `page` is outside the first
  piece, the first piece is unlocked and put like any other.
- Anon folio, every entry point but `folio_split_unmapped()`: must be mapped
  at least once; `folio_get_anon_vma()` returns NULL for an unmapped folio
  and the split returns `-EBUSY`.
- `anon_vma` lock and `i_mmap_rwsem`: taken by `__folio_split()`, not by the
  caller.
- `list != NULL`: each new piece but `lock_at`'s is unlocked; each is on
  `list` with one extra reference from `lru_add_split_folio()`, unless the
  folio is device-private; the original folio is not added.
- `folio_split_unmapped()`: anon, unmapped and locked are `VM_WARN_ON_ONCE_FOLIO()`
  only; it does not call `folio_check_splittable()`, so order and writeback
  are not checked.
- `folio_split_unmapped()` afterwards: caller remaps, puts pieces on the LRU,
  unlocks each piece and owns one reference on each; see
  `migrate_vma_split_unmapped_folio()` in `mm/migrate_device.c`.

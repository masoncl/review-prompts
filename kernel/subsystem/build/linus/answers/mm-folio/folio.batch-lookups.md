- `*start` after the call differs per function:

| Function | `*start` on return |
|---|---|
| `find_get_entries()` | index after the last entry returned; unchanged if nothing found |
| `find_lock_entries()` | index after the last entry returned; a skipped folio does not advance it; unchanged if nothing returned |
| `filemap_get_folios()`, `filemap_get_folios_tag()` | batch filled: `folio_next_index()` of the last folio, which can exceed `end`; otherwise `end + 1`, or `(pgoff_t)-1` when `end` is `(pgoff_t)-1` |
| `filemap_get_folios_contig()` | `folio_next_index()` of the last folio; unchanged if nothing found |

- `find_lock_entries()` skips a folio that fails `folio_trylock()`, has
  `folio->mapping != mapping`, or is under writeback; none of these waits.
- `find_lock_entries()` and multi-index value entries: one that begins before
  `*start` is skipped; one that extends past `end` ends the walk.
- `find_get_entries()` at `end`: no clipping; a folio or value entry crossing
  `end` is returned.
- `indices[]`: holds `xas.xa_index`. For the first entry of
  `find_get_entries()` this is the `*start` passed in when that entry covers
  `*start`, which can lie inside the folio; use `folio->index` for the
  folio's first index.
- `filemap_get_folios_dirty()` in `mm/filemap.c`: like `filemap_get_folios()`
  but drops folios it could trylock and found neither dirty nor under
  writeback. Folios are returned unlocked; a folio it could not lock is
  returned unchecked.

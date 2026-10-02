- `__filemap_get_folio()`: an inline in `include/linux/pagemap.h` that passes
  a NULL policy to `__filemap_get_folio_mpol()`; the body to read is
  `__filemap_get_folio_mpol()` in `mm/filemap.c`.
- `write_begin_get_folio()` in `include/linux/pagemap.h`: `FGP_WRITEBEGIN`
  plus `fgf_set_order(len)`, plus `FGP_DONTCACHE` when the iocb has
  `IOCB_DONTCACHE`; returns a folio or `ERR_PTR()`; creates, locks, may sleep.
- There is no FGP_ENTRY flag here. `__filemap_get_folio_mpol()` always treats
  a value entry as "no folio"; the single-index lookup that returns one is
  `filemap_get_entry()`.
- There is no filemap_get_incore_folio() here. `mincore_page()` in
  `mm/mincore.c` calls `filemap_get_entry()` and resolves a shmem swap entry
  itself.
- `struct page` wrappers present: `find_get_page()`, `find_get_page_flags()`,
  `find_lock_page()`, `find_or_create_page()`, `grab_cache_page_nowait()`, all
  over `pagecache_get_page()` in `mm/folio-compat.c`, which maps every
  `ERR_PTR()` to `NULL`, so `-EAGAIN` and `-ENOMEM` are indistinguishable.
- `FGP_WRITE`: never throttles or sleeps. On create it adds `__GFP_WRITE` if
  `mapping_can_writeback()`; on a found folio it clears the idle flag, and
  only when `FGP_ACCESSED` is not set.
- `FGP_NOWAIT` with `FGP_STABLE`: `FGP_NOWAIT` covers the folio lock and the
  allocation only. `folio_wait_stable()` still runs and sleeps on writeback
  when `mapping_stable_writes()` is true.

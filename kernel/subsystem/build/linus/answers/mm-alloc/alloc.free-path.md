- Chain: `__free_pages()` -> `___free_pages()` -> `__free_frozen_pages()` ->
  `__free_pages_prepare()` -> `free_frozen_page_commit()` (per-CPU list) or
  `free_one_page()` -> `split_large_buddy()` -> `__free_one_page()`.
- `__folio_put()`: in `mm/folio.c`; there is no mm/swap.c.
- There is no FPI_TRYLOCK and no free_unref_page_commit(); the names are
  `FPI_NOLOCK` and `free_frozen_page_commit()`.
- `free_pages_prepare()`: a wrapper for `__free_pages_prepare()` with
  `FPI_NONE`; `compaction_free()` calls it from outside `mm/page_alloc.c`.
- `FPI_PREPARED`: `__free_pages_prepare()` returns true at once; used by
  `free_prepared_contig_range()` after each order-0 page was prepared.
- `___free_pages()`, count not reaching zero on a non-compound page: frees the
  tail chunks through `__free_frozen_pages()`, so they can go to a per-CPU
  list.

| Entry point | Reference |
|---|---|
| `free_pages_nolock()` | drops one |
| `free_pages_bulk()`, `__free_contig_range()`, `free_contig_range()` | drop one on every order-0 page |
| `cma_release()` | drops one on every page |
| `free_frozen_pages_nolock()` | expects zero |
| `free_contig_frozen_range()`, `cma_release_frozen()` | expect zero |
| `free_reserved_pages()` | sets every count to zero itself |

- With `FPI_NOLOCK` and `can_spin_trylock()` false: the page goes on neither
  list; `add_page_to_zone_llist()` puts it on `zone->trylock_free_pages`.
- With `FPI_NOLOCK` and a failed pcp trylock: `free_one_page()` trylocks
  `zone->lock`, and on failure also uses `zone->trylock_free_pages`.
- With `FPI_NOLOCK`, `free_frozen_page_commit()`: queues the page and returns
  before the `pcp->high` check, so no drain to the buddy lists, and
  `pcp->count` may exceed `high`.
- `free_unref_folios()`: an order that fails `pcp_allowed_order()` goes to
  `free_one_page()` directly, not through `__free_pages_ok()`.
- Order-0 page with `PageHWPoison()`: `__free_pages_prepare()` returns false;
  the page reaches no list.

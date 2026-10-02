- There is no FPI_TRYLOCK here; the flag is `FPI_NOLOCK` in
  `mm/page_alloc.c`.
- Three places pass `FPI_NOLOCK`: `free_pages_nolock()`,
  `free_frozen_pages_nolock()` (used by `__free_slab()` in `mm/slub.c`), and
  the charge-failure path of `__alloc_frozen_pages_noprof()`.
- `__free_pages()` passes `FPI_NONE`; it is not an any-context free.
- Page origin: `___free_pages()` and `__free_frozen_pages()` make no test of
  how the page was allocated, so pages from the ordinary allocator are
  accepted.
- `add_page_to_zone_llist()`: stores the order in `page->private`; struct
  page has no order field.
- `FPI_NOLOCK` with `can_spin_trylock()` false (also `!CONFIG_SMP` in NMI):
  the page goes to the llist with no lock tried.
- Draining `zone->trylock_free_pages`: done only by `free_one_page()` called
  without `FPI_NOLOCK`.
- Not drained by: any allocation path, `free_pcppages_bulk()`, or a
  `FPI_NOLOCK` free that got `zone->lock`.
- An ordinary free that lands on the per-CPU list therefore leaves the llist
  untouched, also when that list is later drained in bulk.

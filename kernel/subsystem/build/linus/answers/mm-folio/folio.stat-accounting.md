- `__` forms: exist for node and zone only (`__node_stat_mod_folio()`,
  `__zone_stat_mod_folio()` and their add and sub forms in
  `include/linux/vmstat.h`); there is no `__`-prefixed lruvec folio helper.
- rmap accounting: `__folio_mod_stat()` in `mm/rmap.c` calls
  `lruvec_stat_mod_folio()`.
- Value type: `lruvec_stat_mod_folio()` takes `int`; the node and zone mod
  helpers take `long`.
- Add and sub helpers: take the folio and the item only, so a caller cannot
  pass them a count.
- Add and sub helpers: right only when the item counts pages and the whole
  folio changes state.
- Value for a mod helper: the number of units that changed state, which need
  not be `folio_nr_pages()`.
- **Potentially unsafe usage**: passing a mod helper a value other than
  `folio_nr_pages(folio)` for a large folio.
  - Unsafe: when the item counts pages and every page of the folio changes
    state; the counter is then off by the difference.
  - Safe: `__folio_mod_stat()` passes the number of pages whose mapping
    state changed, for `NR_ANON_MAPPED` and `NR_FILE_MAPPED`.
  - Safe: `try_grab_folio()` in `mm/gup.c` passes `refs`, because
    `NR_FOLL_PIN_ACQUIRED` counts pins.
- **Unsafe usage**: negating an `unsigned int` count into a node or zone mod
  helper; with `CONFIG_64BIT` the result is zero-extended to `long` and adds
  about 4G.
  - Safe: negate a `long`, as `folio_account_cleaned()` in
    `mm/page-writeback.c` does.
  - Safe: negate the `unsigned long` from `folio_nr_pages()`, as
    `node_stat_sub_folio()` does.
  - Safe: `lruvec_stat_mod_folio()`, whose `int` parameter converts the
    value back to negative.
- `lruvec_stat_mod_folio()` with an item not in `memcg_node_stat_items[]`
  (`mm/memcontrol.c`), on a folio that has a memcg: the node counter is
  updated, then `__mod_memcg_lruvec_state()` warns "missing stat item" once
  and skips the memcg update.
- `node_stat_mod_folio()` on an item memcg tracks: updates the node only;
  `__swap_cache_add_folio()` and `__swap_cache_del_folio()` in
  `mm/swap_state.c` use it for `NR_FILE_PAGES` and put `NR_SWAPCACHE` through
  `lruvec_stat_mod_folio()`.

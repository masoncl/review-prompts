- Two bindings: folio→`struct obj_cgroup` (`folio->memcg_data`) and
  objcg→memcg (`objcg->memcg`); the `folio_memcg()` result stays the folio's
  memcg only while both are stable.
- Folio lock, LRU isolation, exclusive reference: fix only folio→objcg; the
  memcg read through it can still switch to the parent.
- objcg→memcg stable: under `cgroup_mutex` (`offline_css()` asserts it), or
  under the `lru_lock` of the folio's own lruvec as returned by
  `folio_lruvec_lock()`.
- `objcg_lock`: static in `mm/memcontrol.c`, not available to callers; there
  is no deferred split queue lock in this role (`deferred_split_lru` is a
  `struct list_lru`).
- Pointer validity: `rcu_read_lock()` or `cgroup_mutex`;
  `obj_cgroup_memcg()` has a `lockdep_assert_once()` for exactly these, so
  `folio_memcg()` under the folio lock alone trips it.
  `mem_cgroup_swap_full()` holds the folio lock and still takes RCU.
- Page counters only: folio→objcg stability plus RCU is enough, as in
  `uncharge_batch()`.
- kmem folios: accepted by `folio_memcg()`; `folio_objcg()` masks
  `MEMCG_DATA_KMEM` off.
- Slab folios and `MEMCG_DATA_OBJEXTS`: rejected by `VM_BUG_ON_FOLIO()` only,
  so unchecked without `CONFIG_DEBUG_VM`.
- `folio_memcg_check()`: returns NULL when `MEMCG_DATA_OBJEXTS` is set; adds
  no lifetime or binding guarantee and hits the same lockdep assertion.
- `get_mem_cgroup_from_folio()` on `css_tryget()` failure: re-reads
  `folio_memcg()` and retries; no fallback to root.
- `get_mem_cgroup_from_folio()` on an uncharged folio: returns
  `root_mem_cgroup`; it returns NULL when `mem_cgroup_disabled()`.
- `get_mem_cgroup_from_folio()` calls `folio_memcg()`, not
  `folio_memcg_check()`, with no NULL test inside the loop: the folio must be
  non-slab and must stay charged for the duration of the call.

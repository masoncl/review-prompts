- There is no struct deferred_split, split_queue_lock, split_queue,
  split_queue_len, get_deferred_split_queue() or
  folio_split_queue_lock_irqsave() in this tree, and neither
  `struct mem_cgroup` nor `struct pglist_data` holds a deferred-split queue.
- The queue: one static `struct list_lru`, `deferred_split_lru` in
  `mm/huge_memory.c`, initialised memcg-aware by `thp_shrinker_init()`.
- A queued folio: linked by `_deferred_list` on one `struct list_lru_one`,
  chosen from `folio_nid()` and `folio_memcg()`; sublists are per memcg and
  per node.
- Root memcg, no memcg, or `mem_cgroup_kmem_disabled()` (see
  `__list_lru_init()`): the folio goes on the per-node `lru` of
  `struct list_lru_node`.
- Lock: the `lock` field of that `struct list_lru_one`; it also covers the
  setting and clearing of the partially-mapped flag.
- Sublist choice: redone from `folio_memcg()` on every queue and unqueue, in
  `lock_list_lru_of_memcg()` in `mm/list_lru.c`; it moves to the parent memcg
  when the memcg has no sublist or its sublist is marked dead.
  `deferred_split_isolate()` is the exception: the walk hands it the sublist.
- `deferred_split_folio()` and `__folio_unqueue_deferred_split()`: take the
  lock with `list_lru_lock_irqsave()` under `rcu_read_lock()`.
- `__folio_freeze_and_split_unmapped()`: takes it with plain
  `list_lru_lock()`; its callers have disabled IRQs.
- `deferred_split_folio()` returns without queueing for: order <= 1;
  `!partially_mapped` with `split_underused_thp` off; a folio in the
  swapcache.
- `deferred_split_folio()`: tests neither anon nor hugetlb; the anon test and
  the `folio_is_device_private()` exclusion are in `__folio_remove_rmap()`.
- hugetlb fields (`_hugetlb_subpool` and the rest) are in `__page_3` of
  `struct folio`; `_deferred_list` is in `__page_2`; they do not overlap.

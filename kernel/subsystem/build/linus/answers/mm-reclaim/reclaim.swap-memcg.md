- Memcg charged by `__mem_cgroup_try_charge_swap()`:
  `obj_cgroup_memcg(folio_objcg(folio))`, read under `rcu_read_lock()`, or the
  ancestor that `mem_cgroup_private_id_get_online()` returns for it.
- `mem_cgroup_private_id_get_online(memcg, nr_pages)`: takes all `nr_pages` id
  references at once. It walks to the parent while `id.ref` is zero.
- There is no mem_cgroup_id_get_online(), mem_cgroup_id_get_many(),
  mem_cgroup_id_put_many() or mem_cgroup_from_id() here.
- Put side: `mem_cgroup_private_id_put(memcg, n)`.
- No-slot test: `!folio_test_swapcache(folio)`. It raises `MEMCG_SWAP_FAIL`
  and returns 0.
- Caller: `folio_alloc_swap()` puts the folio in the swap cache first, then
  charges. On failure it calls `swap_cache_del_folio()`.
- Root memcg: the counter is not charged; the references and the record are
  still made.
- Owner record: `ci->memcg_table`, a `struct swap_memcg_table` per cluster,
  defined in `mm/swap_table.h`.
- There is no mm/swap_cgroup.c, swap_cgroup_record() or
  lookup_swap_cgroup_id() here.
- Record accessors: `__swap_cgroup_set()`, `__swap_cgroup_get()`,
  `__swap_cgroup_clear()`.
- Table lifetime: allocated in `swap_cluster_alloc_table()` unless
  `mem_cgroup_disabled()`, freed in `swap_cluster_free_table()`.
- Release: `__swap_cluster_free_entries()` in `mm/swapfile.c`. It clears one
  slot at a time and uncharges each run of equal ids.
- `__mem_cgroup_uncharge_swap(id, nr_pages)`: takes the id as an argument. It
  does not clear the record.
- v1 record: `__memcg1_swapout()` writes it.
- v1 swap-in: `memcg1_swapin()` clears the record and uncharges. There is no
  mem_cgroup_swapin_uncharge_swap() here.

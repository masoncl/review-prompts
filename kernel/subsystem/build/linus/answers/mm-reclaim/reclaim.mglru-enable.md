- `lru_gen_switching()` in `include/linux/mm_inline.h`: tests the static key
  `lru_switch`, defined in `mm/vmscan.c`.
- `lru_gen_change_state()`: enables `lru_switch` before it flips
  `lru_gen_caps[LRU_GEN_CORE]`, and disables it after the last lruvec is
  converted.
- Reclaim entry points `shrink_lruvec()`, `shrink_node()` and
  `kswapd_age_node()`: test `lru_gen_enabled() || lru_gen_switching()`, run
  the multi-gen path, and during a switch run the classic path as well.
- Multi-gen-only shortcuts test `lru_gen_enabled() && !lru_gen_switching()`:
  for example `folio_check_references()`, `prepare_scan_control()`,
  `snapshot_refaults()`, and the `lru_gen_look_around()` call in
  `folio_referenced_one()`.
- Per-lruvec flag: `lrugen->enabled` in `struct lru_gen_folio`, written by
  `lru_gen_change_state()` under the lru lock and by `lru_gen_init_lruvec()`.
- `lru_gen_enabled()`: one global static key, not per lruvec.
- `lru_gen_in_fault()`: returns `current->in_lru_fault`; it says nothing
  about which lists are in use.
- `lru_gen_change_state()`: does not call `lru_gen_rotate_memcg()`.
- `state_is_valid()` and `seq_is_valid()`: asserted under the lru lock before
  each lruvec is converted, not after.
- Locks, in order: `cgroup_lock()`, `cpus_read_lock()`, `get_online_mems()`,
  then a function-local `state_mutex`.
- **Potentially unsafe usage**: branching on `lru_gen_enabled()` alone.
  - Unsafe: in code that can run while `lru_gen_change_state()` converts the
    lists, and that chooses which set of lists reclaim scans or assumes
    folios other than the one it holds are on `lrugen->folios[]`; during a
    switch one lruvec has folios on both kinds of list.
  - Safe: run the multi-gen path and fall through to the classic path while
    `lru_gen_switching()` is true, as `shrink_node()` does.
  - Safe: under `cgroup_mutex`, which `lru_gen_change_state()` holds through
    `cgroup_lock()` for the whole switch, as `memcg_reparent_objcgs()` does;
    `offline_css()` asserts the mutex.
  - Safe: add or remove one folio under the lru lock with
    `lruvec_add_folio()` or `lruvec_del_folio()`, as `lru_deactivate()` in
    `mm/folio.c` does; `lru_gen_add_folio()` tests `lrugen->enabled` and
    `lru_gen_del_folio()` tests `folio_lru_gen()`.

- Models take `reset_batch_size()` to run under the caller's lru lock. Here it
  is called with no lruvec lock held, from `walk_mm()` and from
  `evict_folios()` after `move_folios_to_lru()`.
- Models pass a swap entry to `__mem_cgroup_try_charge_swap()`. Here it takes
  only the folio.
- Models restore userfaultfd write-protect with pte_swp_uffd_wp() and know no
  other uffd PTE state. Here the setter on a swap PTE is `pte_swp_mkuffd()`,
  and for a `userfaultfd_rwp()` VMA `do_swap_page()` re-applies `PAGE_NONE`
  when the swap PTE has the uffd bit.
- Models know one retry in `do_try_to_free_pages()`, for skipped low
  protection. Here the `sc->memcg_full_walk` retry exists because reclaimers
  other than kswapd may walk only part of the memcg tree in
  `shrink_node_memcgs()`, and the `sc->force_deactivate` retry runs only if
  `sc->skipped_deactivate`.
- Models take demotion to depend on the node only. Here `can_demote()` and
  `demote_folio_list()` take the memcg and drop target nodes with
  `mem_cgroup_node_filter_allowed()`.
- Models take `mem_cgroup_migrate()` to hand the same pointer to the new
  folio. Here, when the nodes differ, the objcg that `get_migration_objcg()`
  returns can belong to an ancestor memcg; see
  `__get_obj_cgroup_from_memcg()`.
- Models take every folio in an LRU-add batch to reach the LRU. Here
  `folio_batch_move_lru()` frees a folio whose only reference is the batch's.
- Models take `folio_mark_accessed()` to act on every folio. Here it returns
  at once when `folio_test_dropbehind()`.
- Models call isolate_hugetlb(). It is not in this tree;
  `folio_isolate_hugetlb()` in `mm/hugetlb.c` does the job.

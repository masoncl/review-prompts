- `MADV_DONTNEED` and `MADV_DONTNEED_LOCKED`: the one per-VMA-lock path that
  frees an installed table, an empty PTE table, under `CONFIG_PT_RECLAIM`.
- Call chain: `madvise_dontneed_single_vma()` sets `reclaim_pt` and calls
  `zap_vma_range_batched()`; `zap_pte_range()` in `mm/memory.c` clears the PMD
  in `zap_empty_pte_table()` or `zap_pte_table_if_empty()`, then calls
  `pte_free_tlb()`.
- There is no mm/pt_reclaim.c, try_get_and_clear_pmd() or try_to_free_pte()
  here, and no zap_page_range_single() or zap_page_range_single_batched();
  `zap_vma_range()` and `zap_vma_range_batched()` replace the last two.
- `reclaim_pt`: set only in `madvise_dontneed_single_vma()`; zaps from other
  per-VMA-lock callers use `zap_vma_range()`, which passes `NULL` details and
  frees no installed table, for example
  `tcp_zerocopy_vm_insert_batch_error()`, `binder_alloc_free_page()` and
  `madvise_guard_install()`.
- `CONFIG_PT_RECLAIM`: `def_bool y` in `mm/Kconfig`, on wherever
  `MMU_GATHER_RCU_TABLE_FREE` is set and `HAVE_ARCH_TLB_REMOVE_TABLE` is not.
- hugetlb VMA under `MADV_DONTNEED`: `__unmap_hugepage_range()` can clear a
  PUD entry through `huge_pmd_unshare()`
  (`CONFIG_HUGETLB_PMD_PAGE_TABLE_SHARING`); `__hugetlb_zap_begin()` takes
  `hugetlb_vma_lock_write()` and `i_mmap_lock_write()` for it.
- `get_lock_mode()` in `mm/madvise.c`: returns `MADVISE_VMA_READ_LOCK` for
  `MADV_GUARD_INSTALL`, `MADV_GUARD_REMOVE`, `MADV_DONTNEED`,
  `MADV_DONTNEED_LOCKED` and `MADV_FREE`.
- `MADV_COLD` and `MADV_PAGEOUT`: `MADVISE_MMAP_READ_LOCK`, never the per-VMA
  lock.
- `MADV_GUARD_INSTALL` under the VMA read lock: sets marker PTEs through
  `walk_page_range_vma_unsafe()`, and `walk_pmd_range()` allocates a missing
  PTE table with `__pte_alloc()`.
- `is_vma_lock_sufficient()`: also rejects an anonymous VMA with no
  `anon_vma` for `MADV_GUARD_INSTALL`; `try_vma_read_lock()` then takes the
  mmap read lock.
- `lock_next_vma()` users in `fs/proc/task_mmu.c`: maps, smaps and numa_maps
  share `m_start()`; maps and `query_vma_find_by_addr()` read VMA fields only.
- smaps and numa_maps under the VMA read lock: walk page tables read-only via
  `walk_page_vma()` with `PGWALK_VMA_RDLOCK_VERIFY` ops, picked by
  `get_smaps_walk_ops()`, `get_smaps_shmem_walk_ops()` and
  `get_show_numa_ops()`.
- `damon_va_walk_page_range()` in `mm/damon/vaddr.c`: walks under the VMA read
  lock with `PGWALK_VMA_RDLOCK_VERIFY` when the range fits one VMA that is
  not `VM_PFNMAP`.
- `bpf_iter_task_vma_find_next()` and `stack_map_lock_vma()` in `kernel/bpf/`:
  read VMA fields, no page-table access.

- `get_swap_device()` tests, in order: `entry.val` non-zero; type below
  `MAX_SWAPFILES` and `swap_info[type]` non-NULL (`swap_type_to_info()`);
  `percpu_ref_tryget_live(&si->users)`; then offset below `si->max`.
- `get_swap_device()` does not test `si->flags` or `nr_swapfiles`.
- swapoff before `percpu_ref_kill()`: `del_from_avail_list()` clears
  `SWP_WRITEOK`, then `wait_for_allocation()`, then `try_to_unuse()`.
- swapoff after `percpu_ref_kill()`, `synchronize_rcu()` and
  `wait_for_completion()`: frees the extent tree, `si->global_cluster`,
  `si->cluster_info` with every cluster's tables, and closes `si->swap_file`.
- A reference holds off that second half only; there is no swap_map or
  zeromap to free.
- `si->max` and `si->cluster_info`: zeroed by swapoff after
  `wait_for_completion()`.
- `synchronize_rcu()` in swapoff: an entry read and used inside one RCU
  read-side section needs no reference.
- A slot in use keeps `try_to_unuse()` looping, so swapoff never reaches
  `percpu_ref_kill()`; that is why a locked swap-cache folio or a held PTL
  over a swap PTE pins the device.
- `__swap_entry_to_info()`: indexes `swap_info[]` with no bound or NULL test,
  so the entry must be a real swap entry of a device that was swapped on.
- `swap_cache_has_folio()` and the other `swap_cache_` lookups in
  `mm/swap_state.c` call `__swap_entry_to_cluster()` and inherit its rules.
- **Potentially unsafe usage**: calling `__swap_entry_to_info()`,
  `__swap_entry_to_cluster()` or `__swap_offset_to_cluster()` with no
  `get_swap_device()` reference.
  - Unsafe: on an entry read from a page table or a shmem mapping after the
    PTL or RCU section it was read under has ended; swapoff can have freed
    `si->cluster_info`.
  - Safe: on `folio->swap` of a folio that is locked and tested to be in the
    swap cache; `swap_cluster_get_and_lock()` asserts both.
  - Safe: with the PTL held over the swap PTE, as `copy_nonpresent_pte()` does
    around `swap_dup_entry_direct()`, which reaches
    `__swap_offset_to_cluster()`; `unuse_pte()` needs that PTL.
  - Safe: inside the `rcu_read_lock()` section that read the entry, as
    `filemap_cachestat()` does with `swap_cache_get_shadow()`.
  - Safe: after `get_swap_device()` returned non-NULL, as `do_swap_page()`
    does.

- Order in `__folio_put()` for a folio that is neither zone-device nor
  hugetlb:
  1. `page_cache_release()`: takes the folio off the LRU, if it is on it;
  2. `folio_unqueue_deferred_split()`;
  3. `mem_cgroup_uncharge()`;
  4. `free_frozen_pages()` with `folio_order()`.
- There is no free_unref_page() here.
- Steps 1 and 2 need the memcg still charged: the lruvec and the deferred
  split sublist are both found through the folio's memcg.
- `uncharge_folio()` in `mm/memcontrol.c`: has `VM_BUG_ON_FOLIO()` on a folio
  with the LRU flag, and `WARN_ON_ONCE()` if the folio was still on the
  deferred list.
- `__folio_unqueue_deferred_split()`: warns on a non-zero refcount, and on an
  uncharged folio unless `mem_cgroup_disabled()`.
- `__page_cache_release()`: clears the LRU, active and unevictable flags
  only; a left-over mlocked flag is cleared in `__free_pages_prepare()`.
- `__free_pages_prepare()`: the "Bad page" checks run only when
  `is_check_pages_enabled()`; it clears `folio->mapping` of an anon folio
  itself before the head-page check.
- Large folio: the deferred split queue is the memcg-aware list_lru
  `deferred_split_lru`, locked with `list_lru_lock_irqsave()`; there is no
  split_queue_lock.
- `folio_unqueue_deferred_split()`: does nothing unless order > 1, the
  large-rmappable flag is set and `_deferred_list` is non-empty.
- `free_huge_folio()`: has no `in_task()` test; it runs in the caller's
  context.
- `free_huge_folio()`: calls `mem_cgroup_uncharge()` as well as the two
  hugetlb cgroup uncharges, all under `hugetlb_lock`.
- Hugetlb folio freed to the page allocator: when
  `folio_test_hugetlb_temporary()`, or when
  `h->surplus_huge_pages_node[nid]` is non-zero; the second test is on the
  node counter, not on the folio.
- `update_and_free_hugetlb_folio()`: on that branch, queues a
  vmemmap-optimized folio on `hpage_freelist` for `free_hpage_workfn()`;
  any other folio is freed inline.
- `free_zone_device_folio()`: calls `mem_cgroup_uncharge()` first for every
  type; the op is `folio_free` in `struct dev_pagemap_ops`, which has no
  page_free member.
- `free_zone_device_folio()` by `pgmap->type`:

| `pgmap->type` | `folio->mapping` | `folio_free` | then |
|---|---|---|---|
| `MEMORY_DEVICE_PRIVATE`, `MEMORY_DEVICE_COHERENT` | cleared | called | `percpu_ref_put_many()` on `pgmap->ref`, one per page |
| `MEMORY_DEVICE_PCI_P2PDMA` | cleared | called | refcount not reset |
| `MEMORY_DEVICE_GENERIC` | left as is | not called | `folio_set_count()` to 1 |
| `MEMORY_DEVICE_FS_DAX` | left as is | not called | `wake_up_var()` on `&folio->page`; refcount not reset |

- Contexts, for a folio that is not zone-device: process, softirq and
  hardirq, not NMI; `page_cache_release()` spins on the lruvec lock and
  `free_one_page()` with `FPI_NONE` spins on `zone->lock`, both with irqsave.
- Contexts, zone-device folio: the driver's `folio_free` runs in the
  caller's context and may take a plain `spin_lock()`.
- **Potentially unsafe usage**: `folio_put()` while holding the lruvec lock.
  - Unsafe: when it may drop the last reference and the folio has the LRU
    flag set; `__page_cache_release()` then takes the folio's lruvec lock
    again.
  - Safe: call `folio_put_testzero()` under the lock, clear the flags with
    `__folio_clear_lru_flags()`, and free after `lruvec_unlock_irq()`, as
    `move_folios_to_lru()` in `mm/vmscan.c` does.

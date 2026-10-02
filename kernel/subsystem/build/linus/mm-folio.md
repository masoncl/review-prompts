# MM Folios

## Main structures

### Objects and how they relate

- `struct folio`: still a union with `struct page` in this tree; `page_folio()`
  is a cast of `_compound_head()` and `folio_page()` is pointer arithmetic.
  No folio is allocated separately from the memmap.
- Kind of memory: recorded in `page_type`, which shares storage with
  `_mapcount` on the head page (`enum pagetype`, `FOLIO_TYPE_OPS()`). Slab,
  page table, hugetlb, zsmalloc and large kmalloc are page types, not flags.
- Overlays of `struct page` other than `struct folio`: for example
  `struct slab`, `struct ptdesc`, `struct netmem_desc` in
  `include/net/netmem.h`, `struct zpdesc` in `mm/zpdesc.h`.
  `struct page_pool` is not an overlay; `struct netmem_desc` points to it.
- `struct obj_cgroup`: what `folio->memcg_data` points to for a charged folio
  (`commit_charge()` in `mm/memcontrol.c`). It is not a `struct mem_cgroup`
  pointer.
- Folio → `struct mem_cgroup`: one more hop, `folio_memcg()` →
  `obj_cgroup_memcg()`, which asserts `rcu_read_lock()` or `cgroup_mutex`.
- Folio → memcg and folio → `struct lruvec` are not fixed for the folio's
  life: `memcg_reparent_objcgs()` points the objcg at the parent memcg and
  `lru_reparent_memcg()` in `mm/folio.c` splices the child's LRU lists into
  the parent's; with `lru_gen_enabled()` it is `lru_gen_reparent_memcg()` in
  `mm/vmscan.c` instead.
- Swap cache slots: one per page, in a per-cluster table hung off
  `struct swap_cluster_info` (`mm/swap.h`); each slot of a large folio holds
  the folio's PFN (`__swap_cache_do_add_folio()`), so there is no multi-index
  entry.
- Large folio ↔ `struct mm_struct`: under `CONFIG_MM_ID` (selected by
  `CONFIG_TRANSPARENT_HUGEPAGE`) a large non-hugetlb folio records up to two
  `mm_id` values with a mapcount each; `folio_maybe_mapped_shared()` reads the
  result.
- `_large_mapcount` of a non-hugetlb folio under `CONFIG_MM_ID`: added to and
  subtracted from with plain read and set under the bit spinlock taken by
  `folio_lock_large_mapcount()` in `include/linux/rmap.h`, not with an atomic
  add. The hugetlb rmap helpers use `atomic_inc()` and `atomic_dec()` without
  that lock.
- `migrate_info`: third user of the slot shared by `private` and `swap`;
  on a migration destination folio it holds a `struct anon_vma` pointer plus
  state bits (`__migrate_folio_record()` in `mm/migrate.c`).

## Where to look

**Core files:** Rows for the folio structure, flag accessors, reference
counting, page cache, truncation and invalidation, and GUP are omitted: they
are where models expect.

| Job | File in this tree | Easy to miss |
|---|---|---|
| Release path and per-CPU LRU batches | `mm/folio.c` | There is no mm/swap.c here. `__folio_put()`, `folios_put_refs()`, `release_pages()`, `struct cpu_fbatches`, `folio_add_lru()` and `lru_add_drain()` are all in `mm/folio.c`. `mm/swap.h` is the swap subsystem's private header, not this code. |
| `__folio_put()` hand-offs | `mm/folio.c` | Hands off only zone-device folios (`free_zone_device_folio()`) and hugetlb folios (`free_huge_folio()`). Other large folios take the common path: `folio_unqueue_deferred_split()`, then `free_frozen_pages()`. |
| Batch type | `include/linux/folio_batch.h` | There is no include/linux/pagevec.h here. `struct folio_batch` and its inline helpers are in `include/linux/folio_batch.h`. |
| Batch type, out-of-line helpers | `mm/folio.c` | `__folio_batch_release()` and `folio_batch_remove_exceptionals()`. |
| Writeback | split: `mm/page-writeback.c` and `mm/filemap.c` | `__folio_start_writeback()` and `__folio_end_writeback()` are in `mm/page-writeback.c`; `folio_end_writeback()` is in `mm/filemap.c`. |
| Page-based wrappers | split: `mm/folio-compat.c` and headers | `mm/folio-compat.c` exists and holds the out-of-line wrappers, for example `unlock_page()` and `set_page_dirty()`. Inline wrappers are in headers: `put_page()` and `get_page()` in `include/linux/mm.h`, `lock_page()` in `include/linux/pagemap.h`. |

**Entry points:** Rows for add, remove, lock, take a reference, mark dirty and
truncate are omitted: they are the functions models expect.

| Job | Start reading from | Easy to miss |
|---|---|---|
| Look up in the page cache | `__filemap_get_folio_mpol()` in `mm/filemap.c` | `__filemap_get_folio()` is a `static inline` in `include/linux/pagemap.h` that passes a NULL policy to it; `mm/filemap.c` does not define `__filemap_get_folio()`. |
| Drop a reference | `folio_put()` in `include/linux/mm.h` | Last reference goes to `__folio_put()` in `mm/folio.c`, not mm/swap.c. |
| Put on the LRU | `folio_add_lru()` in `mm/folio.c` | There is no lru_cache_add() here. |
| Start writeback | `__folio_start_writeback()` in `mm/page-writeback.c` | `folio_start_writeback()` is a macro in `include/linux/page-flags.h` that passes `keep_write` as `false`; there is no second wrapper for `true`. |
| End writeback | `folio_end_writeback()` in `mm/filemap.c` | It calls `folio_end_writeback_no_dropbehind()`, which is what calls `__folio_end_writeback()`; then it calls `folio_end_dropbehind()`. |
| Invalidate, best effort | `mapping_try_invalidate()` in `mm/truncate.c` | Per folio: `mapping_evict_folio()`. |
| Invalidate, hard | `invalidate_inode_pages2_range()` in `mm/truncate.c` | Per folio: `folio_unmap_invalidate()`, not `mapping_evict_folio()`. |

## Pages, heads and tails

**Non-folio compound pages**

- `page_slab()` in `mm/slab.h`: goes to the head and returns NULL unless the
  head's type is `PGTY_slab`. There is no folio_slab(). `slab_folio()` is the
  unchecked cast.
- `struct slab`, `struct ptdesc`, `struct zpdesc`: each asserted
  `<= sizeof(struct page)`, so each reinterprets one `struct page` only, the
  head if the page is compound.
- Compound slab or page table: tail 1 holds what `prep_compound_head()` wrote,
  so `folio_order()`, `folio_nr_pages()` and `folio_mapcount()` (0) are valid.
  `slab_order()` calls `folio_order(slab_folio(slab))`.
- `folio_test_large()`: true for every compound head, slab included
  (`s->allocflags` has `__GFP_COMP`).
- Type tests generated by `PAGE_TYPE_OPS()`, for example `PageSlab()`,
  `PageTable()`, `PageLargeKmalloc()`: read only the page passed, and the type
  is set on the head, so they are false for a tail found by address.
- `page_pool_page_is_pp()` in `include/linux/mm.h`: the test for page_pool
  pages, which carry no page type.
- Slab pages from `alloc_slab_page()` in `mm/slub.c` and large-kmalloc pages:
  allocated with `alloc_frozen_pages()` or a variant of it, so the refcount
  is 0. `folio_try_get()` fails on them. `get_page()` warns and returns
  without a reference for `folio_test_slab()` and
  `folio_test_large_kmalloc()`.
- KFENCE pool pages: `kfence_init_pool()` sets the slab type on them in
  place; they are not allocated that way.
- Page tables: `pagetable_alloc_noprof()` uses `alloc_pages_noprof()`, refcount
  1, so `folio_try_get()` succeeds and a type test is still needed afterwards.
- High-order allocation without `__GFP_COMP`: `prep_new_page()` builds no
  compound page; pages after the first have refcount 0 until `split_page()`.
- **Potentially unsafe usage**: using `folio->mapping`, `folio->index`,
  `folio->private` or `folio->lru` of a folio got by `page_folio()` from a PFN
  or address.
  - Unsafe: when the head may be slab, page table or zsmalloc memory; those
    words hold descriptor fields, see `struct slab` in `mm/slab.h`.
  - Safe: after a type test on the head; `folio_mapping()` in `mm/util.c`
    tests `folio_test_slab()`, and only that, before it reads
    `folio->mapping`.
- **Potentially unsafe usage**: reading the order or page count of a folio or
  compound page with no reference.
  - Unsafe: when the value is used unchecked; `prep_compound_page()` sets
    `PG_head` before `prep_compound_head()` writes the order.
  - Safe: when the value is range-checked first, as `scan_movable_pages()` in
    `mm/memory_hotplug.c` does for `folio_nr_pages()` and the
    `PageCompound()` branch of `isolate_migratepages_block()` does for
    `compound_order()`.
  - Safe: after `folio_try_get()` succeeded and `page_folio(page) == folio`
    was rechecked, as `do_migrate_range()` in `mm/memory_hotplug.c` does
    before it reads `folio_nr_pages()`.

**Page types**

- `folio_mapcount()` and `folio_mapped()`: safe on a small typed folio; they
  return 0 and false through `page_mapcount_is_type()`.
- `page_type_has_type()`: the boundary is `PGTY_mapcount_underflow << 24`.
  There is no PAGE_MAPCOUNT_RESERVE.
- Type setters from `PAGE_TYPE_OPS()` and `FOLIO_TYPE_OPS()`: the check that
  the field was `UINT_MAX` is `VM_BUG_ON_PAGE()` or `VM_BUG_ON_FOLIO()`, so
  without `CONFIG_DEBUG_VM` a set on a mapped page silently overwrites the
  mapcount.
- Setting a type that is already set, or clearing when the field is already
  `UINT_MAX`: returns early, no check.
- `PageSlab()`: tests only the page passed. `PageHuge()` is the type test that
  goes through `page_folio()`.
- Hugetlb: has `FOLIO_TYPE_OPS()` only, so there is `folio_test_hugetlb()` and
  no per-page test other than `PageHuge()`.
- `folio_precise_page_mapcount()` in `fs/proc/internal.h`: filters with
  `page_mapcount_is_type()`, not `page_has_type()`.
- Typed folio with mappings: hugetlb. It is the one type that
  `folio_expected_ref_count()` in `include/linux/mm.h` exempts from its
  `page_has_type()` test; see "Expected reference count".

**Tail page overlays**

| Fields | Tail page | Exists from order |
|---|---|---|
| `_flags_1`, `_head_1`, `_large_mapcount`, `_nr_pages_mapped`, `_mm_id_mapcount`, `_mm_ids`, `_mapcount_1`, `_refcount_1` | 1 | 1 |
| `_nr_pages` (only under `NR_PAGES_IN_LARGE_FOLIO`) | 1 | 1 |
| `_entire_mapcount`, `_pincount` | 1 with `CONFIG_64BIT`, else 2 | 1 with `CONFIG_64BIT`, else 2 |
| `_deferred_list` | 2 | 2 |
| `_hugetlb_subpool`, `_hugetlb_cgroup`, `_hugetlb_cgroup_rsvd`, `_hugetlb_hwpoison` | 3 | 2, hugetlb only |

- Folio order: the low 8 bits of `_flags_1`, read by `folio_large_order()`.
  There is no _folio_order field.
- `_nr_pages`: there is no _folio_nr_pages. Without `NR_PAGES_IN_LARGE_FOLIO`
  `folio_large_nr_pages()` computes the count from the order.
- `_nr_pages_mapped`, `_mm_id`, `_mm_ids`, `_mm_id_mapcount`: declared
  unconditionally; `CONFIG_PAGE_MAPCOUNT` and `CONFIG_MM_ID` gate their use,
  not their declaration.
- Hugetlb minimum order: `hugetlb_add_hstate()` has
  `BUG_ON(order < order_base_2(__NR_USED_SUBPAGE))`, and `__NR_USED_SUBPAGE`
  is 3, so order 2.
- `folio_entire_mapcount()`, `folio_large_mapcount()`: do not test
  `folio_test_large()`; they assert it with `VM_BUG_ON_FOLIO()` and
  `VM_WARN_ON_FOLIO()`, both debug-only. `folio_mapcount()` tests it.
- `deferred_split_folio()`: returns for `folio_order(folio) <= 1`; it makes no
  `folio_test_large_rmappable()` test.
  `folio_unqueue_deferred_split()` in `mm/internal.h` tests the order and
  `folio_test_large_rmappable()`. There is no folio_undo_large_rmappable().
- At free: the mapcount fields, `_pincount` and `_deferred_list` must hold the
  values `prep_compound_head()` gave them. `free_tail_page_prepare()` in
  `mm/page_alloc.c` checks this only when `is_check_pages_enabled()`.
- **Potentially unsafe usage**: touching `_deferred_list` after testing only
  `folio_test_large()`.
  - Unsafe: when the folio can be order 1, as page-cache folios can; the
    access lands in the `struct page` after the folio.
  - Safe: when the folio is known to be anonymous, as in the
    `folio_test_anon()` branch of `shrink_folio_list()` in `mm/vmscan.c`;
    `THP_ORDERS_ALL_ANON` excludes order 1 and `folio_check_splittable()`
    returns `-EINVAL` for an anonymous split to order 1.
  - Safe: after `folio_order(folio) > 1`, as `migrate_folio_move()` in
    `mm/migrate.c` does.

**Changing the folio layout**

- Field names in `struct page`: `compound_info` and `__folio_index`. There is
  no compound_head or index field in `struct page`; the `FOLIO_MATCH`,
  `TABLE_MATCH`, `SLAB_MATCH` and `ZPDESC_MATCH` lines use these names.
- `flags`: `memdesc_flags_t` in `struct page`, `struct folio`, `struct slab`
  and `struct ptdesc` (`pt_flags`); the bits are in `.f`. `_flags_1` to
  `_flags_3` are plain `unsigned long`.
- `sizeof(struct folio)`: no `static_assert` bounds it. Each group is a union
  with a `struct page`; a group that outgrows it fails the next group's
  `FOLIO_MATCH(flags, _flags_N)`.
- Tail 3 group: nothing follows it, so nothing fails to compile if it grows
  past `sizeof(struct page)`.
- Tail 1: the fields sit in a union with `_usable_1[4]`; growth past four
  words moves `_mapcount_1` and `_refcount_1`, and their `FOLIO_MATCH` lines
  fail.
- Tails 2 and 3: only `_flags_N` and `_head_N` are matched. A field appended
  there that reaches the tail's `_mapcount` or `_refcount` overlays them and
  no assert fails. Tail 3 is already full up to that point, and so is tail 2
  without `CONFIG_64BIT`.
- `TABLE_MATCH`, `SLAB_MATCH`, `ZPDESC_MATCH`, `NETMEM_DESC_ASSERT_OFFSET`:
  compare the descriptor with `struct page`, never with `struct folio`. A
  change to `struct folio` alone trips only `FOLIO_MATCH`.
- `struct netmem_desc` in `include/net/netmem.h`: its size assert is
  `sizeof(struct netmem_desc) <= offsetof(struct page, _refcount)`, tighter
  than the `<= sizeof(struct page)` of the other descriptors.
- `sizeof(struct page)`: `compound_info_has_mask()` tests
  `is_power_of_2(sizeof(struct page))`, so with
  `CONFIG_HUGETLB_PAGE_OPTIMIZE_VMEMMAP` a field that changes the size can
  switch the encoding of `compound_info` in every tail. No build check is
  tied to that switch; with `BITS_PER_LONG` 64, `__mm_zero_struct_page()` in
  `include/linux/mm.h` has `BUILD_BUG_ON()` only for a size that is not a
  multiple of 8, below 56 or above 96.
- Not checked at compile time, to update by hand for a new tail field:
  - `prep_compound_head()` in `mm/internal.h`, which sets the initial value.
  - `free_tail_page_prepare()` in `mm/page_alloc.c`, which checks per tail
    index.
  - `snapshot_page()` in `mm/util.c`, which copies the head, tail 1 and
    `__page_2` and never `__page_3`.
  - `__NR_USED_SUBPAGE` in `include/linux/hugetlb.h`, a plain constant that
    nothing ties to `struct folio`; `hugetlb_vmemmap_init()` has the
    `BUILD_BUG_ON()` against `HUGETLB_VMEMMAP_RESERVE_PAGES`.

## Converting between pages and folios

**Page to folio**

- `struct page` has no field named compound_head; `_compound_head()` reads
  `page->compound_info` (`include/linux/mm_types.h`); `compound_head()` is
  the macro that casts its result.
- Tail encoding depends on `compound_info_has_mask()` in
  `include/linux/page-flags.h`: true only with
  `CONFIG_HUGETLB_PAGE_OPTIMIZE_VMEMMAP` and a power-of-2
  `sizeof(struct page)`.
  - False: a tail's `compound_info` is the head pointer with bit 0 set.
  - True: a tail's `compound_info` is a mask with bit 0 set; the head is the
    tail's own address ANDed with that mask.
- Fake heads: there is no page_fixed_fake_head() and no fake-head test in this
  tree; `_compound_head()` makes no vmemmap-optimisation check beyond the
  mask.
- Page pointer in mask mode: must be the address of the entry in the memmap,
  because the head is computed from that address; a copied tail
  `struct page` gives a wrong head.
- `snapshot_page()` in `mm/util.c`: decodes a copied `struct page` using the
  address of the original.
- **Unsafe usage**: decoding a tail's `compound_info` by hand as "head
  pointer plus 1".
  - Safe: call `compound_head()` or `page_folio()`.
  - Safe: branch on `compound_info_has_mask()` first, as `snapshot_page()`
    does.
- `page_folio()` argument: evaluated once; `_Generic` evaluates only the
  selected association.
- State tested before the reference must be tested again after it:
  `page_idle_get_folio()` in `mm/page_idle.c` tests `folio_test_lru()` on
  both sides of `folio_try_get()`.
- **Potentially unsafe usage**: reading fields of `page_folio(page)` with no
  reference.
  - Unsafe: when the caller acts on the value as if it were stable; the
    folio can be split or freed, and the value is then stale or garbage.
  - Safe: when the value is only a hint and is validated, as
    `scan_movable_pages()` in `mm/memory_hotplug.c` does; it range-checks
    `folio_nr_pages()` against `MAX_FOLIO_NR_PAGES` before skipping ahead.

**Folio to page**

- `folio_page()`: `&(folio)->page + (n)` in every configuration; nth_page() is
  defined nowhere in this tree.
- Index check: none, with or without `CONFIG_DEBUG_VM`.
- Memmap contiguity inside a folio: guaranteed by `MAX_FOLIO_ORDER` in
  `include/linux/mmzone.h`, which is at most one memory section under
  `CONFIG_SPARSEMEM` without `CONFIG_SPARSEMEM_VMEMMAP`.
- Index beyond the folio under that configuration: the result may not be the
  `struct page` of `folio_pfn(folio) + n`; `page_range_contiguous()` in
  `mm/util.c` is the test for ranges not known to lie in one folio.
- File index: not a valid `n`; `folio_file_page()` in
  `include/linux/pagemap.h` masks it with `folio_nr_pages(folio) - 1`.
- `folio_file_page()` with an index outside the folio: wraps to a page inside
  the folio instead of going out of range.
- `try_to_unmap_one()` and `try_to_migrate_one()` in `mm/rmap.c`: take the pfn
  from the PTE value they read (`pte_pfn()`, or `softleaf_to_pfn()` for a
  non-present entry) and subtract `folio_pfn()`; they do not index with
  `pvmw.pfn`.
- `folio_within_vma()` in `mm/internal.h`: computes no index of a page within
  the folio.
- **Potentially unsafe usage**: `n` derived from a virtual address.
  - Unsafe: when the result is used as the page mapped at that address and
    the offset is taken from a base that is not where page 0 of the folio is
    mapped; `folio_page()` then returns another page.
  - Safe: `folio_zero_user()` in `mm/memory.c` takes the offset from
    `ALIGN_DOWN(addr_hint, folio_size(folio))`, so it is below
    `folio_nr_pages()`, and uses it only to choose the zeroing order.

**Folio statistics helpers**

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

## References and mapcounts

**Reference holders**

- Per-CPU batch, large folio: holds its reference only inside the queueing
  call. `__folio_batch_add_and_move()` in `mm/folio.c` and `mlock_folio()`,
  `mlock_new_folio()`, `munlock_folio()` in `mm/mlock.c` drain the batch at
  once when `folio_may_be_lru_cached()` is false, which it is for every large
  folio.
- Per-CPU batch while `lru_cache_disabled()`: drained in the same call too,
  for small folios as well.
- Batches: the members of `struct cpu_fbatches`, including
  `lru_deactivate_file` and `lru_move_tail`, plus `mlock_fbatch` in
  `mm/mlock.c`.
- `PG_lru` set does not rule out a batch reference: every batch of
  `struct cpu_fbatches` except `lru_add` is fed only with folios that are on
  the LRU, for example by `folio_activate()` (with `CONFIG_SMP`) and
  `folio_rotate_reclaimable()`.
- `lru_add` drain: `folio_batch_move_lru()` frees a folio whose only
  reference is the batch's (`folio_ref_freeze(folio, 1)`) instead of putting
  it on the LRU, and stores NULL in its slot; `folios_put_refs()` skips NULL
  slots.
- Pins: see "Recording a pin".

**Mapcount and reference count**

- `filemap_map_folio_range()` in `mm/filemap.c`: raises the mapcount before
  the reference count. It calls `set_pte_range()` and only then
  `folio_ref_add(folio, count - ref_from_caller)`, with the folio locked and
  the PTL held.
- In that window: `folio_ref_count()` >= `folio_mapcount()` still holds
  through the page cache references, but the count is below
  `folio_expected_ref_count()` plus the held references when
  `count - ref_from_caller` > 0.
- `mm/memory.c` callers take the reference first, for example
  `finish_fault()`, `copy_present_ptes()`, `insert_page_into_pte_locked()`.
- Two unlocked reads bound nothing, in either order: an unmap between the
  reads lowers both counts, a map raises both, so the second value can be
  lower or higher than what matched the first.
- Stable comparison, large anon folio: `__wp_can_reuse_large_anon_folio()`
  compares under `folio_lock_large_mapcount()`; that is also the only place
  that asserts `folio_large_mapcount()` <= `folio_ref_count()`, with
  `VM_WARN_ON_ONCE_FOLIO()`.
- Stable comparison, one PTE: `write_protect_page()` in `mm/ksm.c` compares
  after `ptep_clear_flush()` under the PTL, so GUP-fast cannot find the page
  through that PTE.

**Taking a reference**

- `folio_try_get()`: is `folio_ref_add_unless_zero(folio, 1)` in
  `include/linux/page_ref.h`; there is no folio_ref_add_unless() in this
  tree.
- `folio_get()` on a zero count: caught only with `CONFIG_DEBUG_VM`;
  otherwise `VM_BUG_ON_FOLIO()` compiles out and the count goes from 0 to 1.
- `folio_try_get()` context: checks none itself. Page cache lookups hold
  `rcu_read_lock()`; GUP-fast runs with IRQs off, which
  `try_grab_folio_fast()` checks only with `VM_WARN_ON_ONCE()`;
  `page_idle_get_folio()` starts from `pfn_to_online_page()` and holds
  neither.
- **Potentially unsafe usage**: `folio_get()` on a folio the caller took no
  reference on.
  - Unsafe: when the folio was found through something that holds no
    reference, or whose reference nothing held keeps in place: an LRU list,
    the deferred split list, a PFN, the xarray under RCU. The count may be 0,
    freed or frozen.
  - Safe: under the page table lock while a present PTE maps the folio, as
    `copy_present_ptes()` does; `zap_present_folio_ptes()` clears the PTE
    under that lock before the mapping's reference is dropped.
  - Safe: `folio_try_get()` instead, as `isolate_lru_folios()` does under the
    lruvec lock and `deferred_split_isolate()` under the list lock.

**Expected reference count**

- Swap cache term: added for any folio with `folio_test_swapcache()` true,
  anon or not; it sits outside the `!folio_test_anon()` block.
- shmem folio in the swap cache: counted by the swap cache term;
  `shmem_delete_from_page_cache()` in `mm/shmem.c` has set `folio->mapping`
  to NULL, so the page cache term is 0.
- `PG_private_2`: no term for it, although `folio_start_private_2()` in
  `include/linux/netfs.h` takes a reference; such a folio compares as having
  one extra reference until `folio_end_private_2()`.
- Typed pages: `WARN_ON_ONCE()` and return 0 when `page_has_type()` is true,
  except for hugetlb folios.
- GUP pins held by others: not a precondition; they are what a mismatch
  detects.
- Caller's own pin: added by the caller; `collect_longterm_unpinnable_folios()`
  in `mm/gup.c` passes 1 when `folio_has_pincount()` is true, otherwise
  `GUP_PIN_COUNTING_BIAS`.
- `folio_migrate_mapping()`: the addend is `extra_count + 1`; `extra_count`
  is for extra references the caller knows of, for example 1 in `fs/aio.c`.
- **Potentially unsafe usage**: comparing `folio_ref_count()` with
  `folio_expected_ref_count()` and no addend.
  - Unsafe: when the caller holds its own reference (from `folio_try_get()`,
    `folio_get()`, GUP or LRU isolation); the function has no term for it, so
    the comparison always reports an extra reference.
  - Safe: when the caller holds no reference and found the folio through a
    present PTE under the page table lock, as `collapse_scan_pmd()` in
    `mm/khugepaged.c` does.
  - Safe: when the caller holds no reference and walks the page cache under
    the xarray lock, as `memfd_tag_pins()` in `mm/memfd.c` does.
- Per-CPU LRU batch reference: no term for it;
  `__folio_batch_add_and_move()` in `mm/folio.c` takes it with `folio_get()`.
- `lru_add_drain()`: drains the calling CPU only; a batch on another CPU
  keeps its reference until that CPU drains, which `lru_add_drain_all()` or
  `lru_cache_disable()` forces.
- `folio_isolate_lru()`: does not drain; a batch that took its reference
  while `PG_lru` was set, for example through `folio_activate()` (with
  `CONFIG_SMP`), keeps it after isolation.
- Freeze value in migration: `__folio_migrate_mapping()` in `mm/migrate.c`
  freezes on the same `expected_count` that was compared.
- Freeze value in split: `__folio_freeze_and_split_unmapped()` in
  `mm/huge_memory.c` freezes on `folio_cache_ref_count(folio) + 1`, which has
  no mapcount or `PG_private` term; in `__folio_split()`
  `folio_expected_ref_count()` is only the racy check before
  `unmap_folio()`.

**Freezing and exact counts**

- `folio_ref_unfreeze()`: stores the count it is given, which need not be the
  frozen one. `remove_mapping()` passes 1 and `__folio_migrate_mapping()`,
  for a folio with a mapping, passes `expected_count - nr`, which drops the
  cache references.
- Failed `folio_try_get()`: does not tell frozen from freed.
  `deferred_split_isolate()` in `mm/huge_memory.c` treats it as freed and
  unlinks the folio.
- `__folio_freeze_and_split_unmapped()`: for that reason, for an anon folio
  of order > 1, takes the `deferred_split_lru` lock before
  `folio_ref_freeze()`, with count `folio_cache_ref_count(folio) + 1`.
- `ksm_get_folio()`: the opposite case; it spins on `folio_try_get()` while
  `folio_test_swapcache()` is set, because the folio may be frozen for
  migration.

**Recording a pin**

- `folio_has_pincount()`: with `CONFIG_64BIT` true for every large folio;
  otherwise true only for `folio_order(folio) > 1`.
- 32-bit order-1 folio: has no `_pincount`, so a pin adds
  `GUP_PIN_COUNTING_BIAS` to the reference count, as on a small folio.
- Unit: one pin per page, not per call. Pinning n pages of one large folio
  adds n to the reference count and n to `_pincount`.
- Zero folio: a pin changes neither counter. `try_grab_folio()`,
  `try_grab_folio_fast()`, `folio_add_pin()` and `gup_put_folio()` return
  early, so a pin never makes `folio_maybe_dma_pinned()` true for it.
- False while a pin is being taken: GUP-fast takes the plain reference in
  `try_get_folio()` and adds the bias or `_pincount` afterwards.
- Callers that cannot accept that: `folio_needs_cow_for_dma()` asserts, with
  `VM_BUG_ON()`, that `write_protect_seq` is held;
  `__folio_try_share_anon_rmap()` needs the PTE cleared first and issues
  `smp_mb()`.
- Folio without a pin count: any 1024 references read as pinned, `FOLL_GET`
  references included.

**Mapcount fields**

- `_nr_pages_mapped`, with `CONFIG_PAGE_MAPCOUNT`: 0 when unmapped, not -1;
  see `prep_compound_head()` in `mm/internal.h`. It carries
  `ENTIRELY_MAPPED` while a PMD/PUD mapping exists.
- Per-page read: there is no page_mapcount() in this tree.
  `folio_precise_page_mapcount()` in `fs/proc/internal.h` is `BUILD_BUG()`
  without `CONFIG_PAGE_MAPCOUNT`, so each caller tests
  `IS_ENABLED(CONFIG_PAGE_MAPCOUNT)` first and falls back to
  `folio_average_page_mapcount()` or `folio_maybe_mapped_shared()`.
- `CONFIG_PAGE_MAPCOUNT`: `def_bool !NO_PAGE_MAPCOUNT` in `mm/Kconfig`; code
  tests either symbol.
- `CONFIG_NO_PAGE_MAPCOUNT`: selectable only inside
  `if TRANSPARENT_HUGEPAGE`, so `CONFIG_MM_ID` is set with it.
- With `CONFIG_NO_PAGE_MAPCOUNT`: rmap does not change the per-page
  `_mapcount` of a large folio, and `folio_nr_pages_mapped()` returns -1.
- 32-bit order-1 folio: has no `_entire_mapcount`; `folio_entire_mapcount()`
  returns 0 for it.
- hugetlb: its rmap helpers in `include/linux/rmap.h` change only
  `_entire_mapcount` and `_large_mapcount`, both once per mapping;
  `_nr_pages_mapped` and the mm-id fields are not used.

**Mapped tests**

- There is no page_mapped() and no page_mapcount() in this tree. "Is this
  page's folio mapped" is `folio_mapped(page_folio(page))`.
- One page, in one VMA: `page_vma_mapped_walk()`. `page_mapped_in_vma()` in
  `mm/page_vma_mapped.c` is built only with `CONFIG_MEMORY_FAILURE` and
  returns the address or -EFAULT.
- With `CONFIG_NO_PAGE_MAPCOUNT`: no helper answers whether one page of a
  large folio is mapped without a page table walk.

**Per-mm mapcount tracking**

- Shared bit: read with
  `test_bit(FOLIO_MM_IDS_SHARED_BITNUM, &folio->_mm_ids)`; there is no
  folio_test_large_maybe_mapped_shared() in this tree.
- Lock, with `CONFIG_MM_ID`, non-hugetlb folio: slots, shared bit and
  `_large_mapcount` change under `folio_lock_large_mapcount()`, a bit
  spinlock in `_mm_ids`, except in `folio_set_large_mapcount()` on a new
  folio; the PTL does not serialise different MMs.
  `folio_maybe_mapped_shared()` reads without it.
- Clearing: `folio_sub_return_large_mapcount()` clears the bit when the
  unmapping MM has no slot left and one slot's count equals the new total,
  not only at full unmap.
- `CONFIG_NO_PAGE_MAPCOUNT`: plays no part in `folio_maybe_mapped_shared()`.
- hugetlb: `folio_mapcount() > 1`; hugetlb folios have no mm-id tracking.
- True for a folio one MM maps, all cases:
  - large, non-hugetlb, without `CONFIG_MM_ID`: always, even unmapped; that
    test comes before the `mapcount <= 1` test
  - large: more than two MMs mapped it and the one left has mappings that no
    slot counts; the bit stays set until the folio is fully unmapped
  - large, 32-bit: the per-MM count overflowed, which frees the slot and sets
    the bit
  - small or hugetlb: the same MM maps it more than once, such as a page
    cache folio in two VMAs or a KSM folio
- False for a folio several MMs map: hugetlb with a shared page table, which
  counts once. `queue_folios_hugetlb()` in `mm/mempolicy.c` and
  `pagemap_hugetlb_range()` in `fs/proc/task_mmu.c` pair the test with
  `hugetlb_pmd_shared()`.

## The mapping and private fields

**The mapping field**

- Flag names: there is no PAGE_MAPPING_KSM or PAGE_MAPPING_MOVABLE in the
  code here; the only names are `FOLIO_MAPPING_ANON` (0x1),
  `FOLIO_MAPPING_ANON_KSM` (0x2), `FOLIO_MAPPING_KSM` (both bits) and
  `FOLIO_MAPPING_FLAGS` (mask of both), in `include/linux/page-flags.h`.
- `FOLIO_MAPPING_ANON_KSM` is bit 1 alone, not the KSM encoding; a KSM folio
  is `(mapping & FOLIO_MAPPING_FLAGS) == FOLIO_MAPPING_KSM`.
- Movable-ops pages: nothing is encoded in `mapping`; they are found with
  `page_has_movable_ops()` (`PG_movable_ops` plus page type), and the ops
  come from `page_movable_ops()` in `mm/migrate.c`.
- `folio_test_anon()`: true for KSM folios too; `folio_anon_vma()` returns
  NULL for KSM.
- `folio_mapping()` test order: slab, then swap cache, then flag bits. An
  anon folio in the swap cache therefore returns `&swap_space`, not NULL.
- `folio_mapping()` does no masking: any bit of `FOLIO_MAPPING_FLAGS` gives
  NULL; `folio_raw_mapping()` in `mm/internal.h` is the helper that masks.
- `swap_address_space()` in `mm/swap.h`: ignores its argument and returns the
  single `swap_space`, whose initialiser sets only `a_ops`
  (`mm/swap_state.c`), so `->host` is NULL; without `CONFIG_SWAP` it returns
  NULL.
- Swap-cache folio, raw field: an anon folio keeps its tagged anon_vma; a
  shmem folio has NULL (`shmem_delete_from_page_cache()`), so NULL plus
  `folio_test_swapcache()` is not truncation; `get_futex_key()` tests for
  this.
- Tail pages: `page->mapping` is `TAIL_MAPPING`, not NULL
  (`prep_compound_tail()` in `mm/internal.h`), except in tails 1 and 2, and
  tail 3 of a hugetlb folio, where `struct folio` fields overlay the word;
  see `free_tail_page_prepare()` in `mm/page_alloc.c`.
- DAX folio: NULL with non-zero `folio->share` means shared by several files;
  see `dax_folio_is_shared()` in `fs/dax.c`.
- Anon pointer lifetime: the anon_vma in `mapping` is trusted only while
  `folio_mapped()`; `folio_get_anon_vma()` and `folio_lock_anon_vma_read()`
  in `mm/rmap.c` also warn, with `CONFIG_DEBUG_VM`, if the folio is not
  locked.
- NULL on a looked-up folio is not only truncation:
  `replace_page_cache_folio()`, `collapse_file()` and
  `shmem_delete_from_page_cache()` also clear it.
- `move_to_new_folio()` clears it too, on a non-anon source, but migration
  fails while the lookup's reference is held (`folio_ref_freeze()` in
  `__folio_migrate_mapping()`).
- NULL after those paths: the data is still in the file under another folio
  or a swap entry, so a lookup retries instead of treating the index as a
  hole, as `__filemap_get_folio_mpol()` and `filemap_fault()` do.
- `FGP_LOCK` lookups (`filemap_lock_folio()`, `FGP_WRITEBEGIN`): the recheck
  and retry are already done in `__filemap_get_folio_mpol()` in
  `mm/filemap.c`; `__filemap_get_folio()` is an inline wrapper in
  `include/linux/pagemap.h`.
- Callers that lock separately get no recheck from the lookup; the literal
  pattern is in `invalidate_inode_pages2_range()`.
  `truncate_inode_pages_range()` has no compare of its own;
  `find_lock_entries()` and `truncate_inode_folio()` do it.
- The folio lock is the lock the clearing paths share: `page_cache_delete()`
  also holds the `i_pages` lock, but `move_to_new_folio()` and
  `collapse_file()` clear the field with only the folio lock.
- **Potentially unsafe usage**: dereferencing `folio->mapping` as a
  `struct address_space *` on a folio held only by a reference.
  - Unsafe: when nothing excludes removal; the field can become NULL between
    the test and the use, and may be a tagged anon or KSM pointer.
  - Safe: folio locked and `folio->mapping == mapping` checked after locking,
    as `filemap_fault()` does; the clearing paths assert the folio lock (for
    example `page_cache_delete()`).
  - Safe: `PG_writeback` set; `truncate_inode_pages_range()` waits for
    writeback, `find_lock_entries()` skips such folios and
    `migrate_folio_unmap()` waits or gives up. `__folio_end_writeback()`
    relies on this.
  - Safe: a page of the folio is mapped and the page table lock is held, as
    `zap_present_folio_ptes()` calling `folio_mark_dirty()`;
    `truncate_cleanup_folio()` unmaps before removal and
    `filemap_unaccount_folio()` asserts the folio is unmapped.
  - Safe: one `READ_ONCE()` under RCU or with IRQs off, NULL and flag bits
    tested, used only to read the `struct address_space` or inode, as
    `gup_fast_folio_allowed()` and `get_futex_key()` do. This relies on
    `destroy_inode()` in `fs/inode.c`, which uses `call_rcu()` unless the
    filesystem has `->destroy_inode` and no `->free_inode`.

**The private field**

- Owner by folio kind:

| Folio | What the word holds | Where |
|---|---|---|
| page cache | filesystem data; not always a pointer | for example `(void *)EXTENT_FOLIO_PRIVATE` in btrfs, `NETFS_FOLIO_COPY_TO_CACHE` |
| swap cache | `folio->swap` | `__folio_migrate_mapping()` copies it |
| hugetlb | bitmap of `enum hugetlb_page_flags` | `include/linux/hugetlb.h` |
| migration destination | `folio->migrate_info` | `__migrate_folio_record()` in `mm/migrate.c` |

- hugetlb folios from a hugetlbfs lookup: the field holds flag bits, not a
  pointer, with `PG_private` clear; `folio_migrate_flags()` leaves it alone
  on hugetlb and sets it to NULL on every other source folio.
- Release is keyed on flags, not on the field: `folio_needs_release()` in
  `mm/internal.h` is true for `PG_private`, `PG_private_2` or a mapping with
  `AS_RELEASE_ALWAYS`.
- A value stored without `PG_private` is invisible to `folio_needs_release()`,
  `folio_expected_ref_count()` and `folio_detach_private()`; in-tree code
  does this for values that need no release, for example
  `erofs_onlinefolio_init()` (a counter, valid only while the folio is
  locked).
- `PG_private` without `folio_attach_private()`: `nfs_inode_add_request()`
  sets the flag and the field by hand under `mapping->i_private_lock`.
- Attach reference accounting: `folio_expected_ref_count()` adds one for
  `PG_private` only, and only for non-anon folios; `mapping_evict_folio()`
  adds one for `folio_has_private()`, which also covers `PG_private_2`.
- `PG_private` can remain set on a folio whose `mapping` is NULL;
  `migrate_folio_unmap()` and `try_to_free_buffers()` handle that case.
- Migration moves the data rather than freeing it: `filemap_migrate_folio()`
  detaches from the source and attaches to the destination with both folios
  locked; in `mm/migrate.c` only `fallback_migrate_folio()` calls
  `filemap_release_folio()`.
- Large-folio split of a non-anon folio: calls `filemap_release_folio()` on
  the locked folio first and fails with `-EBUSY` if that fails; see
  `mm/huge_memory.c`.
- `mapping->i_private_lock` excludes `try_to_free_buffers()` and the attach
  in `create_empty_buffers()` and `grow_dev_folio()`; it does not exclude
  migration, which detaches without it.
- **Potentially unsafe usage**: reading `folio->private` of a folio returned
  by a page-cache lookup and dereferencing it.
  - Unsafe: with only a reference; `filemap_release_folio()` or truncation
    can detach or free the data.
  - Safe: folio locked and `folio->mapping` equal to the mapping searched, in
    a filesystem that detaches only under the folio lock; a lookup with
    `FGP_LOCK` gives both, as `iomap_get_folio()` does.
    `filemap_release_folio()` and `try_to_free_buffers()` assert the folio
    lock; `nfs_inode_remove_request()` clears the field under
    `mapping->i_private_lock` alone.
  - Safe: `PG_writeback` set, in a filesystem that keeps the data attached
    until it ends writeback, as `iomap_finish_folio_write()`;
    `filemap_release_folio()` and `try_to_free_buffers()` return false under
    writeback, and truncation waits for it.
  - Safe: buffer heads under `mapping->i_private_lock` when the caller also
    excludes truncation and migration, as `block_dirty_folio()` requires of
    its callers (folio lock, or a mapped page with the page table lock).
  - Safe: buffer heads under `mapping->i_private_lock` with a test of
    `BH_Migrate` on the head, as the atomic path of
    `__find_get_block_slow()` in `fs/buffer.c` does; this pairs with
    `buffer_migrate_folio_norefs()`.

## The folio lock

**Scope and lock order**

- Top comment of `mm/filemap.c`: names the folio lock once, as `->lock_page`,
  in the chain `->mmap_lock` → `->invalidate_lock` → `->lock_page`; it gives
  no position relative to `i_mmap_rwsem` or the `i_pages` lock.
- Header comment of `mm/rmap.c`: holds the full chain, with `folio_lock`
  above `mapping->i_mmap_rwsem` and the `i_pages` lock near the bottom.
- `invalidate_lock` between `mmap_lock` and the folio lock: `filemap_fault()`
  takes it only when the lookup finds no folio or one not uptodate, and on a
  retry; an uptodate cached folio is locked without it.
- Order checking: none at run time; `folio_lock()`, `folio_trylock()`,
  `__folio_lock()` and `folio_unlock()` make no lockdep call.
- Folio data: buffered writes are serialized by the lock, since
  `generic_perform_write()` copies between `write_begin` and `write_end`;
  stores through a user mapping and DMA are not.
- `generic_perform_write()`: does not fault the source in before
  `write_begin`; it copies with `copy_folio_from_iter_atomic()` (page faults
  disabled) and calls `fault_in_iov_iter_readable()` only after `write_end`
  returned 0.

**Rechecking after locking**

- Folio held by the lookup's reference: cannot be reclaimed, migrated or split
  by the paths that call `folio_ref_freeze()`, which fails on the extra
  reference; for example `__remove_mapping()` in `mm/vmscan.c`,
  `__folio_migrate_mapping()` in `mm/migrate.c`,
  `__folio_freeze_and_split_unmapped()` in `mm/huge_memory.c`.
- `filemap_remove_folio()` and `folio_unmap_invalidate()`: remove the folio
  whatever its refcount, so the lookup's reference does not stop truncation
  or invalidation.
- Index after locking: asserted, not rechecked;
  `VM_BUG_ON_FOLIO(!folio_contains())` in `filemap_fault()`,
  `find_lock_entries()` and `truncate_inode_pages_range()` is compiled out
  without `CONFIG_DEBUG_VM`.
- `page_cache_delete()`: clears `folio->mapping` and leaves `folio->index`
  set, so the index alone never shows a truncated folio.
- `find_lock_entries()`: uses `folio_trylock()` only and skips a folio it
  cannot lock; after the lock it tests `folio->mapping` and writeback.
- `filemap_fault()` with a locked folio that is not uptodate and without
  `invalidate_lock`: unlocks, puts and redoes the lookup under
  `invalidate_lock` before it reads the folio.
- `folio_matches_swap_entry()` in `mm/swap.h`: the swap-cache recheck;
  `do_swap_page()` calls it right after `folio_lock_or_retry()`.
- **Potentially unsafe usage**: `folio_lock()` on a folio from an unlocked
  lookup, then use without testing `folio->mapping`.
  - Unsafe: when the code then dereferences `folio->mapping` or treats the
    folio as the file's data at that index; `page_cache_delete()` may have
    set `folio->mapping` to NULL.
  - Safe: when the work under the lock reads the mapping itself and accepts
    NULL, as `folio_mark_dirty()` does through `folio_mapping()`; see
    `folio_mark_dirty_lock()`.

**Completing a read**

- Flag update: one XOR that flips both bits, in every architecture's
  `xor_unlock_is_negative_byte()`; the generic
  `arch_xor_unlock_is_negative_byte()` in `include/asm-generic/bitops/lock.h`
  is `raw_atomic_long_fetch_xor_release()`, there is no two-step fallback.
- Error flag: this tree has no PG_error page flag; a failed read shows on the
  folio only as unlocked without `PG_uptodate`.
- Last completion of a partial read: either `iomap_finish_folio_read()` or
  the submitter in `iomap_read_end()` calls `folio_end_read()`, whichever
  brings `ifs->read_bytes_pending` to zero under `ifs->state_lock`.
- **Unsafe usage**: setting `PG_uptodate` on a folio whose read will be ended
  by `folio_end_read(folio, true)`; the XOR then clears the flag, and only
  `VM_BUG_ON_FOLIO()` in `folio_end_read()` checks for it.
  - Safe: leave the flag alone while the read is pending, as
    `iomap_set_range_uptodate()` does when `ifs->read_bytes_pending` is
    non-zero.
  - Safe: `folio_mark_uptodate()` then `folio_unlock()` when no
    `folio_end_read()` will follow, as `iomap_read_end()` unlocks when
    `ifs->read_bytes_pending` is already zero.
- **Potentially unsafe usage**: touching the folio after `folio_end_read()`.
  - Unsafe: in a completion handler for a folio taken with
    `readahead_folio()`, which drops the reference before the I/O; the lock
    was all that kept the folio in the cache.
  - Safe: when the caller holds its own reference, as `aio_setup_ring()` in
    `fs/aio.c` does from `__filemap_get_folio()`.

**Locking several folios**

- Ordering rule: stated in the kerneldoc of `folio_lock()` in
  `include/linux/pagemap.h`: ascending index within one `struct
  address_space`; across two, the one at the lower address first.
- `vfs_lock_two_folios()` in `fs/remap_range.c`: compares `folio->index`
  only, never the mapping; locks once when both arguments are the same folio.
- There is no lock_two_folios() helper in this tree; `vfs_lock_two_folios()`
  is static to `fs/remap_range.c`.
- `move_pages_ptes()` in `mm/userfaultfd.c`: locks the source folio only;
  for a present PTE, `folio_trylock()` under the PTE lock, and on failure for
  a small folio drops the PTE lock, calls `folio_lock()` and retries; for a
  large folio it returns `-EAGAIN`.
- There is no unmap_and_move() here; `migrate_folio_unmap()` in
  `mm/migrate.c` locks the source folio and takes the destination with
  `folio_trylock()` only.
- `migrate_pages_batch()`: batches only for `MIGRATE_ASYNC`, where
  `migrate_folio_unmap()` gives up when `folio_trylock()` fails; for other
  modes `migrate_pages_sync()` passes one folio per call, and a
  `VM_WARN_ON_ONCE()` checks the list length.
- `migrate_folio_unmap()` under `PF_MEMALLOC`: never blocks in
  `folio_lock()`, in any mode.
- `unpin_user_pages_dirty_lock()` in `mm/gup.c`: does not call
  `folio_mark_dirty_lock()`; it open-codes lock, `folio_mark_dirty()`, unlock
  per folio, and takes no lock for a folio that is already dirty.
- **Potentially unsafe usage**: blocking in `folio_lock()` while holding the
  lock of another folio.
  - Unsafe: when another task can lock the second folio and nothing fixes
    the order in which the two are taken, as with folios from a GUP array,
    whose order is unrelated to the `folio_lock()` rule.
  - Safe: when the second folio was just allocated and never published, as
    `migrate_device_coherent_folio()` in `mm/migrate_device.c` locks the
    result of `folio_alloc()`.
  - Safe: when the two folios are always taken in one fixed order, as
    `mext_folio_double_lock()` in `fs/ext4/move_extent.c` locks the folio of
    the inode at the lower address first, for two different inodes; the
    kerneldoc of `folio_lock()` states the order.

## Flags

**The flags word**

- `folio->flags` and `page->flags`: type `memdesc_flags_t`, a struct with the
  single member `unsigned long f`, in `include/linux/mm_types.h`; code writes
  `folio->flags.f`.
- Fields above the flags, from the top: section, node, zone, last cpupid,
  KASAN tag, MGLRU generation, MGLRU refs; see `LRU_GEN_PGOFF` and
  `LRU_REFS_PGOFF` in `include/linux/mmzone.h`.
- Bits left unused between the flags and the MGLRU refs: hold an allocation
  tag index when `mem_profiling_compressed` is on; see `alloc_tag_sec_init()`
  in `mm/alloc_tag.c`.
- `PF_NO_TAIL` and `PF_NO_COMPOUND`: assert only in modifying accessors
  (`enforce` is 1), never in tests.
- Without `CONFIG_DEBUG_VM_PGFLAGS`: `VM_BUG_ON_PGFLAGS()` compiles to nothing,
  so a write through a tail lands on the head with `PF_NO_TAIL` and on the
  page given with `PF_NO_COMPOUND`.
- Flags declared only with `FOLIO_FLAG()` and its single-operation forms: have
  no page accessor, so nothing redirects a tail for them. For example there is
  no PageActive(), PageReferenced(), PageSwapBacked(), PageUnevictable(),
  PageMlocked() or PageSwapCache() in this tree.

**Flags on the second page**

- Large-folio check: the only one is
  `VM_BUG_ON_PGFLAGS(n > 0 && !test_bit(PG_head, ...))` in `folio_flags()` and
  `const_folio_flags()`, compiled in only with `CONFIG_DEBUG_VM_PGFLAGS`;
  there is no `VM_BUG_ON_FOLIO()` in the accessors.
- `PF_SECOND` and `FOLIO_PF_SECOND`: defined, but no accessor in this tree is
  declared with them; all three second-page flags use
  `FOLIO_FLAG(name, FOLIO_SECOND_PAGE)`.
- `PF_SECOND`: takes `&page[1]` of the page it is given after asserting
  `PageHead(page)`; it does not look up the head.
- Bit choice: not one of the low 8 bits, which hold the order
  (`folio_large_order()` reads `_flags_1 & 0xff`), and not a bit whose page
  accessor is `PF_ANY`, since those are set on a tail page's own word, as
  `SetPageAnonExclusive()` does with `PG_owner_2`.
- `PAGE_FLAGS_SECOND` in `include/linux/page-flags.h`: a new second-page flag
  must be added to it; `__free_pages_prepare()` clears the mask from `page[1]`
  before the tail pages are checked against `PAGE_FLAGS_CHECK_AT_FREE`.
- Accessor forms: only atomic test, set and clear exist for `large_rmappable`,
  `partially_mapped` and `has_hwpoisoned`; no non-atomic form is declared.
- Order byte: `folio_set_order()` in `mm/internal.h` and `folio_reset_order()`
  in `include/linux/mm.h` rewrite it with a plain read-modify-write of
  `_flags_1`, which can lose an atomic flag update made to that word at the
  same time; `__split_folio_to_order()` calls `folio_set_order()` with the
  refcount frozen.
- **Potentially unsafe usage**: using a second-page accessor with no folio
  reference.
  - Unsafe: when nothing stops a split or a free, after which `page[1]` is
    another folio's head or a free page.
  - Safe: with a reference held; `__folio_freeze_and_split_unmapped()` in
    `mm/huge_memory.c` must win `folio_ref_freeze()` before
    `__split_folio_to_order()` runs.
  - Safe: at refcount 0 with the `deferred_split_lru` list lock held and the
    folio still on the list, as `deferred_split_isolate()` and
    `__folio_unqueue_deferred_split()` do; `__folio_put()` and
    `folios_put_refs()` call `folio_unqueue_deferred_split()`, which takes
    that lock, before the pages are freed.
  - Safe: at refcount 0 in the path that dropped the last reference, before
    it frees the pages, as `__folio_put()` does through
    `folio_unqueue_deferred_split()`; `folio_try_get()` and
    `folio_ref_freeze()` both fail on a zero count.
  - Safe: on the copy made by `snapshot_page()`, as `stable_page_flags()` in
    `fs/proc/page.c` does; the second page is inside the
    `struct page_snapshot`.

**Flag ownership**

- LRU code location: there is no mm/swap.c; `lru_add()`,
  `folio_batch_move_lru()` and `folio_mark_accessed()` are in `mm/folio.c`.

| Flag | Set | Cleared | Rule in this tree |
|---|---|---|---|
| writeback | `folio_test_set_writeback()` in `__folio_start_writeback()` | xor in `__folio_end_writeback()` | set asserts folio locked; xarray tags only if `mapping_use_writeback_tags()` |
| lru | `folio_set_lru()` in `folio_batch_move_lru()`, after the move function | `folio_test_clear_lru()`; `__folio_clear_lru_flags()` | `folio_test_clear_lru()` is atomic and needs no lruvec lock; the set in `folio_batch_move_lru()` and the final clear at refcount 0 are under it |
| active | `lru_activate()`; `__lru_cache_activate_folio()` | LRU move functions | lruvec lock on the LRU; in the local `lru_add` batch only the per-CPU local lock |
| swapbacked | `__folio_set_swapbacked()` on new folios; `ttu_anon_lazyfree_folio()`, `__discard_anon_folio_pmd_locked()` | `lru_lazyfree()` | clear runs at batch drain under the lruvec lock, not the folio lock |
| swapcache | `__swap_cache_do_add_folio()` | `__swap_cache_do_del_folio()` | folio lock plus the `struct swap_cluster_info` lock; there is no swap xarray |
| mlocked | `mlock_folio()`, `mlock_new_folio()` | `__munlock_folio()`; `__free_pages_prepare()` | atomic ops, except the non-atomic clear in `__free_pages_prepare()`; `__munlock_folio()` takes the lruvec lock only if `folio_test_clear_lru()` succeeded |
| unevictable | `lru_add()`, `__mlock_folio()`, `__mlock_new_folio()` | `lru_add()`, `__munlock_folio()`, `__mlock_folio()` | in these functions, under the lruvec lock |
| private | `folio_attach_private()` | `folio_detach_private()` | helpers take and drop a folio reference and make no lock assertion |

- `folio_xor_flags_has_waiters()`: `folio_unlock()`, `folio_end_read()` and
  `__folio_end_writeback()` flip their bits with it, so the bit must be known
  set (clear for uptodate in `folio_end_read()`) and no other path may change
  it at the same time; only `VM_BUG_ON_FOLIO()` checks this.
- `munlock_folio()`: does not clear the flag; it queues the folio, and
  `__munlock_folio()` clears it when the batch drains.
- `folio_test_swapcache()`: true only if swapbacked is also set, because
  `PG_swapcache` aliases `PG_owner_priv_1`.
- `PAGEFLAG(Private, private, PF_ANY)`: `SetPagePrivate()` on a tail page sets
  the tail's own bit.
- With `lru_gen_enabled()`: `lru_gen_add_folio()` clears `PG_active` when the
  folio goes on a generation list and `lru_gen_del_folio()` sets it again for
  an active generation when not reclaiming, both by `set_mask_bits()` on the
  whole word.
- With `lru_gen_enabled()`: `folio_mark_accessed()` only calls
  `lru_gen_inc_refs()`, which updates `PG_referenced`, the refs field and
  `PG_workingset`.
- `__folio_clear_active()` and `__folio_clear_unevictable()`: used only at
  refcount 0, in `__folio_clear_lru_flags()` and in the dead-folio branch of
  `folio_batch_move_lru()` after `folio_ref_freeze(folio, 1)`.
- An isolated folio that still has references: use the atomic forms, as
  `lru_move_tail()` and `folio_migrate_flags()` do.

**Flag tests without a reference**

- `folio_flags()` and `const_folio_flags()`: make no poison check, so no
  `folio_test_*()` accessor runs `PF_POISONED_CHECK()`; of the flag accessors,
  only the page accessors (through their policy) and `PageHead()` do, and only
  with `CONFIG_DEBUG_VM_PGFLAGS`.
- Tail pointer through a folio accessor: with `CONFIG_DEBUG_VM_PGFLAGS`,
  `folio_flags()` asserts `compound_info & 1` is clear, and for index 1 that
  `PG_head` is set.
- Tail pointer through a page test accessor: no assertion on the tail;
  `PF_HEAD` and `PF_NO_TAIL` read the head, `PF_ANY` and `PF_NO_COMPOUND` read
  the page given.
- `PagePoisoned()`: true only for a memmap that `page_init_poison()` filled,
  at memmap allocation and in `remove_pfn_range_from_zone()`
  (`mm/memory_hotplug.c`).
- `page_init_poison()`: empty without `CONFIG_DEBUG_VM`, and the `vm_debug`
  boot parameter can turn it off, see `setup_vm_debug()` in `mm/debug.c`.
- Freed page: no check fires on a flag test; `__free_pages_prepare()` clears
  `PAGE_FLAGS_CHECK_AT_PREP`, which is every flag except `PG_hwpoison`, from
  the word.
- `free_page_is_bad()` and `check_new_pages()` in `mm/page_alloc.c`: run only
  when the `check_pages_enabled` static key is on, which is the default with
  `CONFIG_DEBUG_VM`.
- `snapshot_page()` in `mm/util.c`: copies the page and its folio into a
  `struct page_snapshot` with no reference; `__dump_page()`,
  `stable_page_flags()` and `get_kpage_count()` work on the copy.
- `snapshot_page_is_faithful()`: false when the copy fell back to treating the
  page as a single page.

**Adding a page flag**

- Names table: `__dump_folio()` in `mm/debug.c` has
  `BUILD_BUG_ON(ARRAY_SIZE(pageflag_names) != __NR_PAGEFLAGS + 1)`, so a
  non-alias enum entry without an entry in `__def_pageflag_names` fails the
  build.
- Name wrapper for a config-confined flag, such as `IF_HAVE_PG_MLOCK()` in
  `include/trace/events/mmflags.h`: its `#if` must be the same condition as
  the one around the enum entry, or the build fails in one of the
  configurations.
- Aliases declared after `__NR_PAGEFLAGS`, such as
  `PG_readahead = PG_reclaim`: get no name entry.
- Bit-count build check: the `#error "Not enough bits in page flags"` in
  `include/linux/page-flags-layout.h`; it counts `LRU_GEN_WIDTH` but not
  `LRU_REFS_WIDTH`.
- `LRU_REFS_WIDTH`: `min()` of `__LRU_REFS_WIDTH` and the bits left over, so a
  new flag can shrink it with no build error.
- Node field: with `CONFIG_SPARSEMEM_VMEMMAP` a node that does not fit is
  `#error "Vmemmap: No space for nodes field in page flags"`; it is dropped
  to `NODE_NOT_IN_PAGE_FLAGS` only otherwise.
- `arch/sparc/mm/init_64.c`: has `BUILD_BUG_ON(NR_PAGEFLAGS > 32)`.
- Position: `folio_unlock()` and `folio_end_read()` in `mm/filemap.c` have
  `BUILD_BUG_ON(PG_waiters != 7)`, `BUILD_BUG_ON(PG_locked > 7)` and
  `BUILD_BUG_ON(PG_uptodate > 7)`, so a new entry cannot go among the first
  eight.
- `mminit_verify_pageflags_layout()` in `mm/mm_init.c`: a boot-time check,
  built only with `CONFIG_DEBUG_MEMORY_INIT`; it prints the widths and
  `BUG_ON()`s only on the section, node and zone fields.
- `PAGE_FLAGS_CHECK_AT_PREP`: is `PAGEFLAGS_MASK` without `__PG_HWPOISON`
  (plus the MGLRU masks), so there is nothing to add; every new flag must be
  clear at allocation and `__free_pages_prepare()` wipes it at free.
- A flag that must survive free and allocation: needs the same exemption as
  `__PG_HWPOISON`.
- `PAGE_FLAGS_CHECK_AT_FREE`: an explicit list; add the flag only if finding
  it set at free is a bug.
- Split and migration: `__split_folio_to_order()` in `mm/huge_memory.c`
  copies an explicit list of head flags to each new folio, and
  `folio_migrate_flags()` in `mm/migrate.c` copies flag by flag; a new flag is
  dropped by both unless added.
- Config-confined examples in this tree: `PG_mlocked`, `PG_hwpoison`,
  `PG_young` with `PG_idle`, `PG_arch_2`, `PG_arch_3`; there is no
  PG_uncached.

## The LRU

**Per-CPU LRU batching**

- Move batches (`lru_deactivate_file`, `lru_deactivate`, `lru_lazyfree`,
  `lru_activate`, `lru_move_tail`): queueing does not clear `PG_lru` or take
  the folio off its list.
- Queue-time test, for example in `folio_deactivate()`: a plain
  `folio_test_lru()`; a folio that fails it is not queued.
- Move batches at drain: `folio_batch_move_lru()` calls
  `folio_test_clear_lru()`; a folio isolated while queued is skipped there and
  only loses the batch reference.
- `lru_activate`: the member name of the activate batch; it exists only under
  `CONFIG_SMP`.
- Batch capacity: `FOLIO_BATCH_SIZE` in `include/linux/folio_batch.h`; there
  is no PAGEVEC_SIZE.
- New folio in a `VM_LOCKED` VMA with no `VM_SPECIAL` bit:
  `folio_add_lru_vma()` queues it on `mlock_fbatch` in `mm/mlock.c`, not on
  `lru_add`; that batch also holds a reference, and is drained on the same
  conditions as in `__folio_batch_add_and_move()`: batch full,
  `folio_may_be_lru_cached()` false, or `lru_cache_disabled()` true.

**Draining LRU batches**

- `lru_add_drain()`, `lru_cache_disable()`, `lru_cache_enable()`: in
  `mm/internal.h`; of the drain calls, `include/linux/swap.h` has only
  `lru_add_drain_all()` and `lru_cache_drain_for_folio()`.
- mlock batch: `lru_add_drain()` drains it with `mlock_drain_local()`, the
  per-CPU work of `lru_add_drain_all()` does too, and `mm/mlock.c` tests
  `lru_cache_disabled()` before it leaves a folio queued.
- `lru_cache_disable()`: waits with `synchronize_rcu_expedited()`, then, under
  `CONFIG_SMP`, calls `__lru_add_drain_all(true)`.
- `__lru_add_drain_all(true)`: the flag only skips the generation early exit;
  work is still queued only on CPUs where `cpu_needs_drain()` is true.
- `lru_cache_drain_for_folio()` in `mm/folio.c`: drains for one folio, and
  only when `folio_ref_count()` differs from `folio_expected_ref_count()`
  plus the caller's own references.
- `lru_cache_drain_for_folio()` order: `lru_add_drain()`, recheck, then
  `lru_add_drain_all()`; with a non-NULL `drained`, each level runs at most
  once over a series of folios.
- `lru_cache_drain_for_folio()` on a large folio: returns at once, since
  `folio_may_be_lru_cached()` is false.
- `collect_longterm_unpinnable_folios()` in `mm/gup.c`: calls
  `lru_cache_drain_for_folio()` per folio; it does not call
  `lru_add_drain_all()` directly and does not call `lru_cache_disable()`.
- CMA user of the `lru_cache_disable()` and `lru_cache_enable()` bracket:
  `__alloc_contig_migrate_range()` in `mm/page_alloc.c`.
- Between `lru_cache_disable()` and `lru_cache_enable()`: batches stay empty,
  but `folio_isolate_lru()` can still return false, because another isolator
  or a drain in progress has cleared `PG_lru`.
- **Potentially unsafe usage**: draining once, then isolating folios.
  - Unsafe: when the code has no path for `folio_isolate_lru()` returning
    false, or relies on batches staying empty after `lru_add_drain()` or
    `lru_add_drain_all()` returns; `__folio_batch_add_and_move()` queues
    again on any CPU unless `lru_cache_disabled()` is true.
  - Safe: between `lru_cache_disable()` and `lru_cache_enable()`, with the
    failure reported, as `do_pages_move()` in `mm/migrate.c`:
    `__add_folio_for_migration()` returns `-EBUSY`.
  - Safe: a drain as an optimisation, with the failure handled per folio,
    as `migrate_device_unmap()` in `mm/migrate_device.c`, which clears
    `MIGRATE_PFN_MIGRATE` for that entry.
  - Safe: `lru_cache_drain_for_folio()` then `folio_isolate_lru()`, skipping
    the folio on false, as `collect_longterm_unpinnable_folios()`.

**LRU placement flags**

- `folio_lruvec_lock_irq()`, `folio_lruvec_lock_irqsave()` and
  `folio_lruvec_lock()`, in `mm/memcontrol.c` under `CONFIG_MEMCG`: return
  with `lruvec->lru_lock` and the RCU read lock both held; so do the inline
  forms in `include/linux/memcontrol.h` without `CONFIG_MEMCG`.
- Unlock: `lruvec_unlock_irq()`, `lruvec_unlock_irqrestore()` or
  `lruvec_unlock()` in `include/linux/memcontrol.h`; each drops the spinlock
  and the RCU read lock.
- Lruvec binding: clearing `PG_lru` does not fix the folio's lruvec; the
  memcg, and so the result of `folio_lruvec()`, can change through
  `memcg_reparent_objcgs()` until `lru_lock` is held.
- Lock helpers under `CONFIG_MEMCG`: retry until `lruvec_memcg()` equals
  `folio_memcg()`, so only an lruvec returned by them, or matched with
  `folio_matches_lruvec()` under the lock, is the folio's.
- Folio on a list: its list and placement flags change under `lru_lock`;
  `folio_batch_move_lru()` and `folio_isolate_lru()` clear `PG_lru` before
  they take it.
- Folio off the list: its holder changes placement flags without `lru_lock`;
  for example `shrink_folio_list()` calls `folio_set_active()` on an isolated
  folio, and `__lru_cache_activate_folio()` on one in the local `lru_add`
  batch.
- `lruvec_add_folio()`: does not touch `PG_lru`; `folio_batch_move_lru()`
  calls `folio_set_lru()` after it, `move_folios_to_lru()` before it, both
  inside the lock.
- `folio_isolate_lru()`: returns `bool`; false with nothing changed when
  `PG_lru` was already clear; it returns no errno.
- `folio_isolate_lru()` with a folio on an MGLRU generation list:
  `lru_gen_del_folio()` clears the `LRU_GEN_MASK` bits and sets `PG_active`
  when `lru_gen_is_active()` is true for the old generation.
- `isolate_folio()` in `mm/vmscan.c`: MGLRU reclaim passes `reclaiming` true
  to `lru_gen_del_folio()`, which then does not set `PG_active`.
- `folio_update_gen()`: rewrites the generation bits with `try_cmpxchg()`
  under the page table lock only, without `lru_lock`; `sort_folio()` moves
  the folio to the matching list later.
- `folio_isolate_lru()` caller: holds a reference, does not hold `lru_lock`,
  has IRQs enabled (`lruvec_unlock_irq()` enables them); a prior
  `folio_test_lru()` is not required.
- `VM_BUG_ON_FOLIO()` on a zero refcount in `folio_isolate_lru()`: a `BUG()`,
  and compiled out without `CONFIG_DEBUG_VM`.
- `folio_isolate_lru()` and `folio_putback_lru()`: declared in
  `mm/internal.h`; every caller is in `mm/`.
- **Potentially unsafe usage**: clearing `PG_lru` on a folio with no
  reference held.
  - Unsafe: when another task can drop the last reference at the same time;
    `__page_cache_release()` tests `folio_test_lru()` at refcount zero to
    decide whether to unlink the folio.
  - Safe: `folio_try_get()` first, then `folio_test_clear_lru()`, with
    `folio_put()` on failure, as `isolate_lru_folios()` does under
    `lru_lock`.
  - Safe: the caller already holds a reference, which `folio_isolate_lru()`
    asserts with `VM_BUG_ON_FOLIO()`.
  - Safe: `__folio_clear_lru_flags()` under `lru_lock` by the path that saw
    `folio_put_testzero()` return true, as `move_folios_to_lru()` does;
    `folio_try_get()` fails on such a folio.

**Lazyfree folios**

- `folio_test_lazyfree()` in `include/linux/page-flags.h`: the predicate for
  this state; `shrink_folio_list()` and `try_to_unmap_one()` use it.
- `VM_DROPPABLE` VMA: `folio_add_new_anon_rmap()` leaves `PG_swapbacked`
  clear, so its anon folios are lazyfree from their first mapping, with no
  `MADV_FREE`.
- `folio_mark_lazyfree()`: silently skips a folio with `PG_lru` clear, such as
  one isolated or still in another CPU's `lru_add` batch;
  `madvise_free_single_vma()` calls `lru_add_drain()` first, which covers
  this CPU only.
- `folio_mark_lazyfree()` on an active folio: accepted; `lru_lazyfree()`
  clears `PG_active`.
- `lru_lazyfree()`: repeats the tests at drain; a folio that fails them, or
  was isolated while queued, is left unchanged.
- `ttu_anon_lazyfree_folio()` in `mm/rmap.c`: holds the dirty and refcount
  tests; `try_to_unmap_one()` reaches it through `ttu_anon_folio()`.
- `ttu_anon_lazyfree_folio()` returning false: `try_to_unmap_one()` restores
  the PTEs with `set_ptes()` and aborts the walk.
- `VM_DROPPABLE` in `ttu_anon_lazyfree_folio()`: the dirty test is skipped, so
  a dirty folio is discarded; only the refcount test there can keep it.
- Refcount test failing in `ttu_anon_lazyfree_folio()` with a clean folio: the
  folio stays lazyfree, and `shrink_folio_list()` sets `PG_active` on it at
  `activate_locked`.
- PMD-mapped lazyfree folio: `try_to_unmap_one()` calls
  `unmap_huge_pmd_locked()` in `mm/huge_memory.c`, which applies the same
  dirty and refcount tests in `__discard_anon_folio_pmd_locked()`.
- PMD-mapped marking: `madvise_free_huge_pmd()` calls
  `folio_mark_lazyfree()`.

## PFN scanners

**Speculative access from a PFN**

- Page-level tests before the reference: `PageLRU()` and other `PF_HEAD` tests
  resolve the head themselves and do not assert on a tail.
- `folio_test_lru()` and the other `folio_test_*()` flag tests before the
  reference: they go through `const_folio_flags()`, which under
  `CONFIG_DEBUG_VM_PGFLAGS` asserts that the folio is not a tail.
  `isolate_migratepages_block()` uses `PageLRU(page)` before the reference
  and `folio_test_lru(folio)` only after it.
- Two ways to take the reference, with different rechecks:

| Reference taken on | Helper | Recheck `page_folio(page) == folio` |
|---|---|---|
| `page_folio(page)` | `folio_try_get()` | required; see `damon_get_folio()` |
| the scanned page itself | `folio_get_nontail_page()` | none; the folio is that page; see `isolate_migratepages_block()` |

- `folio_get_nontail_page()` in `include/linux/mm.h`: returns NULL when the
  scanned page's own `_refcount` is 0, so a tail PFN yields nothing rather
  than a reference on its head.
- `isolate_migratepages_block()` after the reference: rechecks
  `folio_test_lru()`, then `folio_test_clear_lru()`, then the order under the
  lruvec lock; it never compares `page_folio(page)`.
- `damon_get_folio()` in `mm/damon/ops-common.c`: reads only `page_folio()`
  before `folio_try_get()` and tests everything else after it.
- `split_huge_pages_all()` in `mm/huge_memory.c`: a zone walker also rechecks
  `folio_zone(folio)` after the reference.
- Scanner that never takes a reference: use `snapshot_page()` in `mm/util.c`,
  which copies the page and folio and retries on an inconsistent copy; see
  `stable_page_flags()` in `fs/proc/page.c`.
- There is no page_order_unsafe() here; `buddy_order_unsafe()` in
  `mm/page_alloc.h` does that.

**Order, size and stepping**

- `_nr_pages` in `struct folio`: present only when `NR_PAGES_IN_LARGE_FOLIO`
  is defined, which `include/linux/mm_types.h` does for `CONFIG_MEMCG` or
  `CONFIG_SLAB_OBJ_EXT`; it does not depend on `CONFIG_64BIT`. Without it
  `folio_large_nr_pages()` computes `1L << folio_large_order()`.
- `folio_nr_pages()` with no reference, under `NR_PAGES_IN_LARGE_FOLIO`: can
  return 0 or a value that is not `1 << order`, because `_nr_pages` is stored
  apart from the order bits. `__free_pages_prepare()` zeroes both before it
  clears `PG_head`, and `prep_compound_page()` sets `PG_head` before
  `folio_set_order()` runs.
- `folio_order()` and `folio_nr_pages()` on a pointer that has become a tail:
  `const_folio_flags()` hits `VM_BUG_ON_PGFLAGS()`, compiled in only under
  `CONFIG_DEBUG_VM_PGFLAGS`.
- `compound_order()` and `compound_nr()`: raw `test_bit()` of `PG_head`, no
  assertion.
- There is no MAX_ORDER here; the buddy limit is `MAX_PAGE_ORDER`.
- Two bounds, with different effect:

| Bound | Defined in | Covers gigantic folios | Used by |
|---|---|---|---|
| `MAX_PAGE_ORDER` | `include/linux/mmzone.h` | no; walker advances one page | `isolate_migratepages_block()` |
| `MAX_FOLIO_ORDER`, `MAX_FOLIO_NR_PAGES` | `include/linux/mmzone.h` | yes | `page_is_unmovable()`, `scan_movable_pages()` |

- Walker that carries a `struct page *` along with the PFN: bound the step to
  the range end before stepping, as `isolate_freepages_block()` does.
- Walker that calls `pfn_to_page()` again each iteration behind a
  `pfn < end` test: may overshoot and clamp after the loop, as
  `isolate_migratepages_block()` does.
- With a reference held: read `folio_nr_pages()` before an operation that
  changes it; `split_huge_pages_all()` reads it before `split_folio()`.
- **Unsafe usage**: stepping by `folio_nr_pages()` or `1UL << order` read
  from an unreferenced folio with no check on the value.
  - Safe: `compound_order()` on the scanned page, bounded by
    `MAX_PAGE_ORDER`, as `isolate_migratepages_block()` does for THP.
  - Safe: `compound_order()` on the `page_folio()` head, bounded by
    `MAX_FOLIO_ORDER`, with the step aligned to the folio end, as
    `page_is_unmovable()` in `mm/page_isolation.c` does.
  - Safe: `folio_nr_pages()` rejected when below 1, above
    `MAX_FOLIO_NR_PAGES` or not a power of two, as `scan_movable_pages()`
    in `mm/memory_hotplug.c` does.
  - Safe: after `folio_try_get()` and the `page_folio()` recheck, as
    `do_migrate_range()` does.

**PFN validity**

- Without `CONFIG_MEMORY_HOTPLUG`: `pfn_to_online_page()` is a macro in
  `include/linux/memory_hotplug.h`, equal to `pfn_valid()` then
  `pfn_to_page()`; it adds nothing.
- `pfn_valid()` on an early section: returns 1 for every PFN of the section,
  since the test is `early_section(ms) || pfn_section_valid(ms, pfn)`.
- `pfn_to_online_page()`: applies `pfn_section_valid()` to early sections
  too, so it returns NULL for a hole in a boot-time section that
  `pfn_valid()` accepts.
- `pfn_section_valid()` without `CONFIG_SPARSEMEM_VMEMMAP`: a stub that
  returns 1.
- ZONE_DEVICE in `pfn_to_online_page()`: a section holding only device
  memory lacks `SECTION_IS_ONLINE` and fails `online_section()`. The
  `get_dev_pagemap()` lookup runs only when `online_device_section()` is
  true, that is `SECTION_IS_ONLINE` plus `SECTION_TAINT_ZONE_DEVICE`.
- `rcu_read_lock_sched()` in `pfn_valid()`: protects `ms->usage` only, which
  `section_deactivate()` in `mm/sparse-vmemmap.c` frees with `kfree_rcu()`.
  It does not keep the memmap alive after `pfn_valid()` returns.
- `pfn_valid()` not from `include/linux/mmzone.h`: under `CONFIG_FLATMEM` a
  range test against `max_mapnr` in `include/asm-generic/memory_model.h`;
  under `CONFIG_HAVE_ARCH_PFN_VALID` the arch supplies it, with sparsemem
  too, and `pfn_to_online_page()` calls it as an extra test.
- `pfn_to_page()` on an unchecked PFN: pointer arithmetic under
  `CONFIG_FLATMEM` and `CONFIG_SPARSEMEM_VMEMMAP`, so nothing fails before
  the first read of the page. Under `CONFIG_SPARSEMEM` alone it dereferences
  the `struct mem_section`, which `__nr_to_section()` may return as NULL.
- Validity granularity: one subsection under `CONFIG_SPARSEMEM_VMEMMAP`, one
  section otherwise; see `next_valid_pfn()`. `for_each_valid_pfn()` in
  `include/linux/mmzone.h` walks a range and rechecks at those boundaries.
- `pageblock_pfn_to_page()` is in `mm/page_alloc.h`; with `zone->contiguous`
  set it returns `pfn_to_page(start_pfn)` with no check.
- `isolate_migratepages_block()` calls `pfn_to_page()` per PFN, and
  `isolate_freepages_block()` calls it once and then steps the pointer, both
  with no test; they rely on their callers passing the block through
  `pageblock_pfn_to_page()` first.

## Page cache lookup

**Page cache storage**

- Value entries in `i_pages` are of three kinds: workingset shadow, shmem swap
  entry (`swp_to_radix_entry()`), DAX entry.
- Kind of a value entry: not encoded in the entry; decided by the mapping.
  Test `shmem_mapping()` or `dax_mapping()` before decoding, as
  `mincore_page()` in `mm/mincore.c` and `truncate_folio_batch_exceptionals()`
  in `mm/truncate.c` do.
- Swap cache: not looked up through `i_pages` in this tree.
  `swap_cache_get_folio()` and `swap_cache_get_shadow()` in `mm/swap_state.c`
  read the swap table (`mm/swap_table.h`); the initialiser of `swap_space`
  sets only `a_ops`.
- Sibling entries: `xas_load()`, `xa_load()`, `xas_find()` and
  `xas_find_marked()` never return one; `xas_next()` and `xas_prev()` return
  the raw slot and can (see Multi-index entries).
- hugetlb folios: stored as ordinary multi-index entries at base-page indices.
  `hugetlb_add_to_page_cache()` and `filemap_lock_hugetlb_folio()` take an
  index in huge-page units and shift it by `huge_page_order()`.

**Lookup functions and FGP flags**

- `__filemap_get_folio()`: an inline in `include/linux/pagemap.h` that passes
  a NULL policy to `__filemap_get_folio_mpol()`; the body to read is
  `__filemap_get_folio_mpol()` in `mm/filemap.c`.
- `write_begin_get_folio()` in `include/linux/pagemap.h`: `FGP_WRITEBEGIN`
  plus `fgf_set_order(len)`, plus `FGP_DONTCACHE` when the iocb has
  `IOCB_DONTCACHE`; returns a folio or `ERR_PTR()`; creates, locks, may sleep.
- There is no FGP_ENTRY flag here. `__filemap_get_folio_mpol()` always treats
  a value entry as "no folio"; the single-index lookup that returns one is
  `filemap_get_entry()`.
- There is no filemap_get_incore_folio() here. `mincore_page()` in
  `mm/mincore.c` calls `filemap_get_entry()` and resolves a shmem swap entry
  itself.
- `struct page` wrappers present: `find_get_page()`, `find_get_page_flags()`,
  `find_lock_page()`, `find_or_create_page()`, `grab_cache_page_nowait()`, all
  over `pagecache_get_page()` in `mm/folio-compat.c`, which maps every
  `ERR_PTR()` to `NULL`, so `-EAGAIN` and `-ENOMEM` are indistinguishable.
- `FGP_WRITE`: never throttles or sleeps. On create it adds `__GFP_WRITE` if
  `mapping_can_writeback()`; on a found folio it clears the idle flag, and
  only when `FGP_ACCESSED` is not set.
- `FGP_NOWAIT` with `FGP_STABLE`: `FGP_NOWAIT` covers the folio lock and the
  allocation only. `folio_wait_stable()` still runs and sleeps on writeback
  when `mapping_stable_writes()` is true.

**Lockless lookup protocol**

- `xas_reload()` after `folio_try_get()`: proves that the folio still covers
  the index only because a split keeps the folio frozen until its slots are
  rewritten. `__folio_freeze_and_split_unmapped()` in `mm/huge_memory.c`
  unfreezes the original folio after all new folios are stored;
  `__folio_migrate_mapping()` in `mm/migrate.c` stores the new folio before
  `folio_ref_unfreeze()`.
- **Unsafe usage**: unfreezing a folio whose `i_pages` slots still point to it
  but which no longer covers those indices.
  - Safe: rewrite every slot first, then `folio_ref_unfreeze()`, as
    `__folio_freeze_and_split_unmapped()` does; `filemap_get_entry()` relies
    on it, since a stale slot would pass its `xas_reload()` comparison.
- After locking: `__filemap_get_folio_mpol()` rechecks only
  `folio->mapping != mapping` and retries. `folio_contains()` is asserted with
  `VM_BUG_ON_FOLIO()`, not rechecked; callers need no index recheck of their
  own.

**Batch lookups**

- `*start` after the call differs per function:

| Function | `*start` on return |
|---|---|
| `find_get_entries()` | index after the last entry returned; unchanged if nothing found |
| `find_lock_entries()` | index after the last entry returned; a skipped folio does not advance it; unchanged if nothing returned |
| `filemap_get_folios()`, `filemap_get_folios_tag()` | batch filled: `folio_next_index()` of the last folio, which can exceed `end`; otherwise `end + 1`, or `(pgoff_t)-1` when `end` is `(pgoff_t)-1` |
| `filemap_get_folios_contig()` | `folio_next_index()` of the last folio; unchanged if nothing found |

- `find_lock_entries()` skips a folio that fails `folio_trylock()`, has
  `folio->mapping != mapping`, or is under writeback; none of these waits.
- `find_lock_entries()` and multi-index value entries: one that begins before
  `*start` is skipped; one that extends past `end` ends the walk.
- `find_get_entries()` at `end`: no clipping; a folio or value entry crossing
  `end` is returned.
- `indices[]`: holds `xas.xa_index`. For the first entry of
  `find_get_entries()` this is the `*start` passed in when that entry covers
  `*start`, which can lie inside the folio; use `folio->index` for the
  folio's first index.
- `filemap_get_folios_dirty()` in `mm/filemap.c`: like `filemap_get_folios()`
  but drops folios it could trylock and found neither dirty nor under
  writeback. Folios are returned unlocked; a folio it could not lock is
  returned unchecked.

**Multi-index entries**

- `xas_next()` and `xas_prev()` return the raw slot; siblings are not
  resolved. `xas_load()` and `xas_reload()` resolve a sibling to the
  canonical entry.
- Entry of order below `XA_CHUNK_SHIFT`: `xas_next()` returns the folio at the
  first index and a sibling entry (`xa_is_sibling()`) at every other index.
- Entry of order `XA_CHUNK_SHIFT` or more: `__xas_next()` in `lib/xarray.c`
  returns the content of the slot that covers the new index. The folio
  repeats for every index of the canonical slot; indices in sibling slots
  give a sibling entry.
- `xas_load()` landing inside an entry: `xa_offset` becomes the canonical
  slot, `xa_index` stays as asked. `xas_next()` adds one to each without
  resyncing; `filemap_get_read_batch()` calls `xas_advance()` before the next
  `xas_next()`.
- A sibling entry is not NULL, fails `xa_is_value()` and fails `xas_retry()`.
- **Unsafe usage**: passing the return of `xas_next()` to `folio_try_get()` or
  another folio accessor after testing only NULL, `xas_retry()` and
  `xa_is_value()`.
  - Safe: test `xa_is_sibling()` first and, after taking the folio, call
    `xas_advance(&xas, folio_next_index(folio) - 1)`, as
    `filemap_get_read_batch()` and `filemap_get_folios_contig()` in
    `mm/filemap.c` do.
  - Safe: walk with `xas_for_each()` or `xas_find()`, which skip sibling
    slots and return each entry once; `find_get_entry()` does.
  - Safe: for sibling entries, compare the return with `xas_reload()` and
    `xas_reset()` on mismatch, as `iter_xarray_populate_pages()` in
    `lib/iov_iter.c` does; `xas_reload()` resolves a sibling, so a sibling
    never compares equal and the next `xas_next()` is an `xas_load()`.
- `xas_get_order()`: must not be called while the `xa_state` points at a
  sibling slot, so not right after `xas_next()` returned a sibling entry. It
  probes the slots after `xa_offset` for sibling entries.
- Under RCU only: `filemap_cachestat()` reads the size from
  `xas_get_order()` rather than from an unpinned folio, and uses it only for
  counting. Code that stores or splits on the result holds the xa_lock, as
  `shmem_free_swap()` and `__filemap_add_folio()` do.
- Without `CONFIG_XARRAY_MULTI`: `xa_get_order()` and `xas_get_order()` are
  stubs in `include/linux/xarray.h` that return 0.

## Page cache insertion and removal

**Adding to the page cache**

- **Unsafe usage**: passing `filemap_add_folio()` a folio that is locked or
  that another task can already reach.
  - Unsafe: `filemap_add_folio()` sets and (on failure) clears the lock bit
    with non-atomic `__folio_set_locked()` and `__folio_clear_locked()`.
  - Safe: a freshly allocated, unlocked folio, as `filemap_create_folio()`
    does.
  - Safe: `__filemap_add_folio()` on a folio the caller locked itself, as
    `hugetlb_add_to_page_cache()` does; `__filemap_add_folio()` asserts
    locked.
- Folio must not be memcg-charged already: `commit_charge()` in
  `mm/memcontrol.c` has `VM_BUG_ON_FOLIO(folio_memcg_charged(folio))`.
- `filemap_add_folio()` failure: folio comes back unlocked, uncharged,
  `folio->mapping` NULL, refcount as on entry, and `folio->index` left set
  when `__filemap_add_folio()` ran; the caller must not call
  `folio_unlock()`, and `filemap_create_folio()` only does `folio_put()`.
- `mem_cgroup_charge()` failure: its error is returned before the lock bit is
  touched.
- `AS_KERNEL_FILE` mapping: the charge is made with `root_mem_cgroup` active,
  and success raises `NR_KERNEL_FILE_PAGES`; `filemap_unaccount_folio()`
  lowers it.
- Stats: `__filemap_add_folio()` raises `NR_FILE_PAGES` and `NR_FILE_THPS`
  only; `NR_SHMEM` is never touched, since swapbacked folios are asserted out.
- `workingset_refault()`: skipped when `gfp` has `__GFP_WRITE`.
- Success path: `WARN_ON_ONCE(folio_test_active(folio))` before the LRU add.
- `__filemap_add_folio()` direct callers: `hugetlb_add_to_page_cache()` is
  the only one besides `filemap_add_folio()`; that path does no memcg charge,
  no LRU add and no refault handling.
- shmem: does not call `__filemap_add_folio()`; it has
  `shmem_add_to_page_cache()` in `mm/shmem.c`.

**Shadow entries at insertion**

- Scan: `xas_for_each_conflict()`; the order of a value entry comes from
  `xas_get_order()`, sampled for the first entry only.
- Split: `xas_try_split()` under the xa_lock, repeated with orders from
  `xas_try_split_min_order()` until the entry is at the folio's order.
- `__filemap_add_folio()` does not call `xas_split_alloc()` or `xas_split()`;
  nothing is preallocated before the lock on the first pass.
- Split node allocation: `xas_try_split()` tries `GFP_NOWAIT` under the lock;
  on `-ENOMEM` the lock is dropped, `xas_nomem()` allocates with the masked
  `gfp`, and the whole scan restarts at the folio's index and order.
- No "order changed" recheck exists; the restart rescans from scratch.
- Larger value entry in a shmem mapping: unconditional
  `BUG_ON(shmem_mapping(mapping))`, not a `VM_BUG_ON()`.
- Shadows smaller than the folio: overwritten by the multi-index
  `xas_store()` with no split.
- `*shadowp` when the folio covers several shadows: the last one walked;
  the others are dropped unreported.
- `shadowp` may be NULL; `hugetlb_add_to_page_cache()` passes NULL.
- `mapping_set_update()` in `mm/internal.h`: installs
  `workingset_update_node()` only when the mapping is neither DAX nor shmem.

**Removing from the page cache**

- `filemap_free_folio()`: static in `mm/filemap.c`, takes `(mapping, folio)`;
  code outside that file cannot call it.

| Function | Who drops the cache's `folio_nr_pages()` references |
|---|---|
| `filemap_remove_folio()` | itself, via `filemap_free_folio()` |
| `delete_from_page_cache_batch()` | itself, `filemap_free_folio()` per folio |
| `__filemap_remove_folio()` | its caller |
| `folio_unmap_invalidate()` | itself, open-coded `free_folio` then `folio_put_refs()` |
| `__remove_mapping()` | nobody puts; refcount was frozen at `1 + folio_nr_pages()` and is 0 on return |
| `remove_mapping()` | `folio_ref_unfreeze(folio, 1)`, leaving the caller's reference |

- `__remove_mapping()`: calls `a_ops->free_folio` itself; its reclaim caller
  in `mm/vmscan.c` frees the folio.
- `filemap_remove_folio()` and `delete_from_page_cache_batch()`: take
  `mapping->host->i_lock`, then `xa_lock_irq()`.
- `i_lock`: needed for `inode_lru_list_add()`, which asserts it and runs
  when `mapping_shrinkable()`; there is no inode_add_lru() here.
- `__filemap_remove_folio()`: the folio lock is the only lock tested by a
  `VM_BUG_ON_FOLIO()` (in `page_cache_delete()`); the caller must also hold
  the `i_pages` lock for `xas_store()`.
- Shadow: only `__remove_mapping()` passes one to
  `__filemap_remove_folio()`, and only when `reclaimed`,
  `folio_is_file_lru()`, not `mapping_exiting()` and not `dax_mapping()`;
  every other caller passes NULL, and `delete_from_page_cache_batch()`
  stores NULL.
- `delete_from_page_cache_batch()`: does no unmap, invalidate or dirty
  cancel; `truncate_inode_pages_range()` runs `truncate_cleanup_folio()` on
  each folio first.
- Still-mapped folio in `filemap_unaccount_folio()`: `VM_BUG_ON_FOLIO()`
  under `CONFIG_DEBUG_VM`; otherwise alert and taint, and the mapcount is
  reset only for a small folio in a `mapping_exiting()` mapping.

**Large folio support**

- Without `CONFIG_TRANSPARENT_HUGEPAGE`: `mapping_set_folio_order_range()`
  returns at once, and `mapping_min_folio_order()` and
  `mapping_max_folio_order()` return 0 whatever `mapping->flags` holds.
- Max-only setter: none; use `mapping_set_folio_order_range()`.
- **Potentially unsafe usage**: calling an order setter on a mapping that is
  already in use.
  - Unsafe: while folios can be added or are cached; the setter is a plain
    read-modify-write of `mapping->flags`, which also holds bits changed
    with `set_bit()`, and `__filemap_add_folio()` asserts each folio against
    the minimum.
  - Safe: in the inode constructor, as `btrfs_set_inode_mapping_order()`
    callers do.
  - Safe: with the inode lock and `filemap_invalidate_lock()` held and the
    cache emptied first, as `set_blocksize()` in `block/bdev.c` does, and
    `ext4_change_inode_journal_flag()` under the inode lock taken by
    `vfs_fileattr_set()`.
- Maximum order: nothing in `__filemap_add_folio()` checks it; of the order,
  only the minimum and the index alignment are asserted, so clamping is left
  to the code that allocates, as `__filemap_get_folio_mpol()` does.
- Split floor: `__folio_split()` in `mm/huge_memory.c` returns `-EINVAL` when
  the new order is below `mapping_min_folio_order()`.
- `min_order_for_split()`: in `mm/huge_memory.c`; returns 0 for an anon
  folio or one whose `folio->mapping` is NULL.
- PMD-size folios: test `mapping_pmd_folio_support()`, not
  `mapping_large_folio_support()`.

**Truncation and invalidation**

- `truncate_inode_partial_folio()` split failure: a dirty folio stays and
  the function returns false; a clean folio is removed whole by
  `truncate_inode_folio()`.
- After false: `truncate_inode_pages_range()` narrows `start` or `end` so
  pass 2 skips that folio.
- Split helper: `folio_split()` to `mapping_min_folio_order()`, in
  `folio_split_or_unmap()`; on failure a non-shmem folio is unmapped with
  `try_to_unmap()`.
- Zeroing of the in-range part: skipped when `mapping_inaccessible()`.
- There is no invalidate_complete_folio2() here; `folio_unmap_invalidate()`
  in `mm/truncate.c` does that job, and returns 1 on removal.
- `invalidate_inode_pages2_range()` return: 0, `-EBUSY`, or the error from
  `a_ops->launder_folio`; the last failing folio's code wins.
- `invalidate_inode_pages2_range()` leaves a folio when: laundering fails,
  `filemap_release_folio()` fails, or the folio is dirty at the recheck
  under `i_lock` and the xa_lock.
- Mapped folios: being mapped is never a reason for
  `folio_unmap_invalidate()` to leave a folio; it unmaps, then
  `BUG_ON(folio_mapped(folio))`.
- Folio whose `folio->mapping` changed before the lock: skipped by
  `invalidate_inode_pages2_range()` without setting an error.
- Large folio overlapping the range: `invalidate_inode_pages2_range()`
  invalidates it whole; it does not zero or split.
- `mapping_evict_folio()`: makes no `folio_mapped()` or
  `mapping_unevictable()` test; a mapped folio fails the refcount test
  `folio_ref_count() > folio_nr_pages() + folio_has_private() + 1`.
- `mapping_evict_folio()` return: pages removed, from `remove_mapping()`,
  which can still fail on its own refcount freeze and dirty recheck.
- `mapping_try_invalidate()` return: pages evicted plus one per value entry,
  not a folio count.
- Value entries in a shmem mapping: left alone by
  `truncate_inode_pages_range()` and `invalidate_inode_pages2_range()`;
  `truncate_folio_batch_exceptionals()` and `clear_shadow_entries()` return
  early.
- DAX entries: truncate hits `WARN_ON_ONCE()` and
  `dax_delete_mapping_entry()`; invalidate uses
  `dax_invalidate_mapping_entry_sync()` and sets `-EBUSY` on failure.

## Allocating and freeing

**Allocating a folio**

- `filemap_alloc_folio()`: takes three arguments, `(gfp, order, policy)`; the
  third is a `struct mempolicy *`, NULL at every caller except
  `__filemap_get_folio_mpol()`.
- `filemap_alloc_folio()` with a non-NULL `policy`: allocates through
  `folio_alloc_mpol_noprof()` with `NO_INTERLEAVE_INDEX`, and applies neither
  cpuset spreading nor the task mempolicy.
- `filemap_alloc_folio()` without `CONFIG_NUMA`: the inline in
  `include/linux/pagemap.h` ignores `policy`.
- `__filemap_get_folio_mpol()`: the only path that hands a caller's policy to
  `filemap_alloc_folio()`; `virt/kvm/guest_memfd.c` uses it.
- `folio_alloc()`: uses `default_policy`, not the task mempolicy, when
  `in_interrupt()` or `__GFP_THISNODE` is set; see
  `alloc_frozen_pages_noprof()` in `mm/mempolicy.c`.
- `vma_alloc_folio()` without `CONFIG_NUMA`: the inline in
  `include/linux/gfp.h` ignores `vma` and `addr`, and does not add
  `__GFP_NOWARN` for `VM_DROPPABLE`; only the `mm/mempolicy.c` body adds it.
- There is no folio_prep_large_rmappable() here; `page_rmappable_folio()` in
  `mm/internal.h` sets the large-rmappable flag on any large folio, page
  cache folios included.
- `_deferred_list`: initialised by `prep_compound_head()` only for order > 1;
  an order-1 folio has none.
- Contents: `post_alloc_hook()` zeroes when `want_init_on_alloc()` is true,
  which is `__GFP_ZERO` or `init_on_alloc` enabled, and
  `want_init_on_free()` is false.
- User folios: `alloc_anon_folio()` and `vma_alloc_anon_folio_pmd()` zero by
  hand, with `folio_zero_user()`, only when `user_alloc_needs_zeroing()`.
- `vma_alloc_zeroed_movable_folio()`, generic version in
  `include/linux/highmem.h`: passes no `__GFP_ZERO`; it calls
  `clear_user_highpage()` under the same test.
- memcg: uncharged unless `__GFP_ACCOUNT`; with it and
  `memcg_kmem_online()`, `__alloc_frozen_pages_noprof()` kmem-charges the
  page, and a failed charge frees it and returns NULL.
- Large anon folio, order > 1: the allocator does not allocate the memcg's
  sublist of `deferred_split_lru`; callers call
  `folio_memcg_alloc_deferred()` after `mem_cgroup_charge()`, for example
  `alloc_anon_folio()` and `vma_alloc_anon_folio_pmd()`.
- Without `folio_memcg_alloc_deferred()`, when the memcg has no sublist yet:
  `lock_list_lru_of_memcg()` hits `VM_WARN_ON()` unless the memcg is dying,
  and returns the sublist of the nearest ancestor that has one, so the folio
  is queued there.

**Freeing a folio**

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

## Model gaps

### Other mistakes models make

- Models take a caller of `lruvec_stat_mod_folio()` to need `rcu_read_lock()`
  for the memcg lookup. `lruvec_stat_mod_folio()` in `mm/memcontrol.c` takes
  `rcu_read_lock()` itself.
- Models take `folio_end_writeback()` never to lock the folio or change the
  cache. For a `PG_dropbehind` folio in task context it trylocks and may
  remove the folio via `folio_unmap_invalidate()`;
  `folio_end_writeback_no_dropbehind()` does not.
- Models take `put_page()` to be a plain wrapper. On a slab or large-kmalloc
  page `put_page()` drops nothing; see `include/linux/mm.h`.
- Models take swap cache lookup to recheck like `filemap_get_entry()`.
  `swap_cache_get_folio()` in `mm/swap_state.c` only does `folio_try_get()`.
- Models name swap_cache_add_folio(). There is no swap_cache_add_folio()
  here; `__swap_cache_add_folio()` needs the cluster locked.
- Models take a lookup to leave `PG_dropbehind` alone.
  `__filemap_get_folio_mpol()` clears it on any folio it returns to a lookup
  without `FGP_DONTCACHE`.

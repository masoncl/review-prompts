# MM Folio Lifecycle and Page Cache

## Lazyfree Folio Reclaim State Transitions

Lazyfree folios (`folio_test_lazyfree()`: anonymous and
`!folio_test_swapbacked()`) may be discarded without writeback if clean. After
the PTE/PMD clear, the reclaim path loads `folio_ref_count()` and
`folio_mapcount()` first, then `smp_rmb()`, then tests dirty; loading dirty
before the refcount loses data (see the comment in `__remove_mapping()`). It
then *acts* on dirty first, and only calls `folio_set_swapbacked()` when the
folio is genuinely dirty:

1. **Dirty** (not `VM_DROPPABLE`): `folio_set_swapbacked()` and remap
2. **Extra references** (`ref_count != 1 + map_count`): remap and abort,
   but do NOT `folio_set_swapbacked()` -- elevated refcount (e.g., speculative
   `folio_try_get()`) does not mean dirty
3. **Clean, no extra refs**: discard

Both PTE (`ttu_anon_lazyfree_folio()` in `mm/rmap.c`, called via
`ttu_anon_folio()` from `try_to_unmap_one()`; on failure `try_to_unmap_one()`
does the remap) and PMD (`__discard_anon_folio_pmd_locked()` in
`mm/huge_memory.c`, which remaps itself) paths must follow this order. The PMD
path also has an unordered early dirty test before the clear; that is only an
early-out. The `smp_mb()` after the PTE/PMD clear pairs with GUP-fast; the
`smp_rmb()` between the refcount and dirty reads follows the ordering
documented in `__remove_mapping()`.

**REPORT as bugs**: `folio_set_swapbacked()` in lazyfree reclaim without first
confirming dirty, or unconditionally on any abort including elevated refcount.

## Folio Tail Page Overlay Layout

`struct folio` overlays metadata onto tail page `struct page` slots. Tail pages
have `->mapping = TAIL_MAPPING`; metadata-carrying tail pages overwrite it. Two
consumers must stay in sync when fields are rearranged across tail page
boundaries:

- `free_tail_page_prepare()` in `mm/page_alloc.c` -- skips `TAIL_MAPPING`
  check per metadata-carrying tail page
- `__dump_folio()` in `mm/debug.c` -- debug printing

Common failure: updating one consumer but missing the other (no compile-time
coupling between them). `snapshot_page()` in `mm/util.c`, which feeds
`__dump_folio()`, copies a fixed number of tail pages and needs the same care.

## Folio Mapcount vs Refcount Relationship

**Invariant**: `folio_ref_count(folio) >= folio_mapcount(folio)`. Extra
refcount comes from swapcache, page cache, GUP pins, LRU isolation, etc.
`folio_expected_ref_count()` in `include/linux/mm.h` counts the swapcache,
pagecache, `PG_private` and mapcount references; it does not count GUP pins,
LRU isolation or the caller's own reference.

- Exclusivity check: `folio_ref_count() == folio_expected_ref_count()`, after
  adding any references the caller itself holds, means no unexpected holders.
  In-tree callers write `+ 1` or `- 1` for their own pin, or plain `==` when
  they hold none (lazyfree path uses simpler `ref_count == 1 + map_count`)
- Sanity assertion: `mapcount > refcount` is the corrupted/impossible state
  to warn on, NOT `mapcount < refcount` (which is normal)

## Non-Folio Compound Pages

`page_folio()` blindly casts the compound head to `struct folio *` with no
runtime validity check. Driver-allocated compound pages (via `vm_insert_page()`
with `alloc_pages(GFP_* | __GFP_COMP, order > 0)`) have `PG_head` set so
`folio_test_large()` returns true, but `folio->mapping` and LRU state are
uninitialized. Calling folio operations (`folio_lock()`, `split_huge_page()`,
`mapping_min_folio_order()`) on these produces crashes or corruption.

Validation gates (`HWPoisonHandlable()`, `PageLRU()`, null-mapping checks)
reject non-folio pages. When a code path calls `page_folio()` on pages from
driver mappings, verify a gate has filtered non-folio compound pages.
`folio_test_large()` alone is insufficient -- it checks `PageHead()`, set for
any compound page.

## Folio Reference Count Expectations

`folio_expected_ref_count()` in `include/linux/mm.h` calculates expected
refcount from pagecache, swapcache, `PG_private`, and mappings. Compare against
`folio_ref_count()` to detect unexpected references from any source. Per-CPU
batching (LRU pagevecs in `mm/folio.c`, mlock/munlock batches in `mm/mlock.c`)
holds transient `folio_get()` references invisible to flag checks.
`lru_add_drain_all()` drains all CPUs' batches; code detecting unexpected
references should drain and recheck before concluding the folio is not
migratable. `lru_cache_drain_for_folio()` in `mm/folio.c` does the compare,
drain and recompare (see its caller `collect_longterm_unpinnable_folios()` in
`mm/gup.c`).

**REPORT as bugs**: `folio_test_lru()` as the *only* test that decides a folio
has no LRU-cache references before an operation that fails on extra references
(migration for longterm pin, split). A folio with `PG_lru` set can still sit in
the activate (SMP), move-tail, deactivate, deactivate-file and lazyfree batches
in `mm/folio.c` and in the mlock/munlock batch in `mm/mlock.c`.
`!folio_test_lru()` as a cheap hint to try a drain, with a refcount recheck
afterwards as in `wp_can_reuse_anon_folio()`, is fine.

## Folio Order vs Page Count

`round_up()`, `round_down()`, `ALIGN()` require the actual page count
(`1 << order`), not the order exponent. Hard to catch in testing when only a
few orders are exercised.

```c
// CORRECT                     // WRONG
round_up(index, 1 << order)    round_up(index, order)
ALIGN(addr, PAGE_SIZE << order)
```

**REPORT as bugs**: alignment argument is a raw `order` variable instead of
`1 << order` or `PAGE_SIZE << order`.

## Folio Lock Strategy After GUP

After GUP pins a specific folio that the caller must process (it cannot skip
it), use `folio_lock()` or `folio_lock_killable()`, not `folio_trylock()`.
Transient lock contention from concurrent migration/compaction is expected, not
a permanent error. `folio_trylock()` is correct only in scan/iteration paths
that can skip locked folios (e.g., `shrink_folio_list()`,
`folio_referenced()`). This does not conflict with "Large Folio Split Refcount
Precondition" in mm-largepage.md: that one is about many tasks taking a
reference, blocking on the lock and retrying `split_folio()` on the same folio
without bound.

When page table re-validation fails after GUP (e.g., `folio_walk_start()`
returns a different folio), retry GUP from scratch rather than returning an
error -- the page table change is a transient race.

## Speculative Folio Access in PFN-Scanning Code

`page_folio()` in PFN-scanning loops is speculative -- compound page structure
may change concurrently. Accessing folio flags or size before stabilizing
causes `VM_BUG_ON_PGFLAGS()` in `const_folio_flags()` (`CONFIG_DEBUG_VM_PGFLAGS`
only) or garbage reads.

**Required pattern** (see `split_huge_pages_all()` in `mm/huge_memory.c`):
```c
folio = page_folio(page);                        // speculative
if (!folio_try_get(folio))                       // stabilize
    continue;
if (unlikely(page_folio(page) != folio))         // re-validate
    goto put_folio;
// NOW safe to access folio flags and state
```

**REPORT as bugs**: folio size, order or mapcount reads, or flag tests whose
result is acted on, on an unreferenced folio from `page_folio()` in
PFN-scanning loops. A flag test used only as a pre-filter and followed by
`folio_try_get()` and a recheck, as in `page_idle_get_folio()`, is fine.

## PFN Range Iteration and Large Folios

`PAGE_SIZE`-stepping PFN loops that call `page_folio()` break with large
folios: either tail pages are rejected (folio missed if head PFN is outside
range) or the same folio is processed `folio_nr_pages()` times (double
accounting, duplicate list insertion).

**Correct patterns:** For non-idempotent per-folio actions (reclaim,
migration), step by `folio_size(folio)` when found, `PAGE_SIZE` otherwise
(see `damon_pa_pageout()` in `mm/damon/paddr.c`). For per-PFN bitmaps
(page_idle), keep `PAGE_SIZE` stepping but skip tail pages.

**REPORT as bugs**: PFN iteration with `page_folio()` + non-idempotent
operations + unconditional `PAGE_SIZE` stepping.

## Lockless Page Cache Folio Access

Compound-state-dependent folio properties (`folio_mapcount()`,
`folio_nr_pages()`, `folio_order()`) read tail-page fields and, under RCU
without a reference, race with concurrent split/free. The stabilization
protocol (see `filemap_get_entry()` in `mm/filemap.c`): `folio_try_get(folio)`
then `xas_reload()` to verify the folio is still at the same slot; retry on
failure.

No reference needed for: xarray metadata only (`xas_get_mark()`,
`xas_get_order()`) or opaque pointer use. Every head-page flag test generated
by the `PAGEFLAG()` / `FOLIO_FLAG(..., FOLIO_HEAD_PAGE)` macros, including
`folio_test_lru()`, `folio_test_dirty()` and `folio_test_writeback()`, is the
same plain `test_bit()` on `folio->flags` with no compound branching.
Second-page flags (`folio_test_large_rmappable()`,
`folio_test_partially_mapped()`, `folio_test_has_hwpoisoned()`) read the first
tail page and belong with the compound-state-dependent group above, as do tests
that read `->mapping` or the page type (`folio_test_anon()`,
`folio_test_hugetlb()`). Without a reference the result may be stale or belong
to reused memory, and `CONFIG_DEBUG_VM_PGFLAGS` kernels hit
`VM_BUG_ON_PGFLAGS()` in `const_folio_flags()` if the memory became a tail
page. Core code tolerates this for advisory checks
(`filemap_range_has_writeback()`, `page_idle_get_folio()`). Anything running
under RCU alone that acts on the result must take the reference first.

**REPORT as bugs**: `folio_mapcount()`, `folio_nr_pages()`, etc. in
`xas_for_each()` loops under `rcu_read_lock()` without prior
`folio_try_get()` + `xas_reload()`.

## folio->private Validity After Page Cache Lookup

Consumers of `filemap_get_folio()` or `filemap_lock_folio()` cannot assume
`folio->private` is valid. A race between lookup and reclaim exists in
which `release_folio()` frees `folio->private` but a task in parallel can
find the folio in the cache, increment its refcount, and cause
`__remove_mapping()` to fail. Filesystems that allocate state in
`folio->private` and free it in `release_folio()` must re-validate (and
re-attach if needed) private data after acquiring a folio from the page
cache. For btrfs, this means calling `set_folio_extent_mapped()` before
accessing `folio->private`.

## Page Cache Batch Iteration: find_get_entries vs find_lock_entries

`indices[i]` from both `find_get_entries()` and `find_lock_entries()` may not
be the canonical base of a multi-order entry. `xas_descend()` in `lib/xarray.c`
follows sibling entries to the canonical slot but does NOT update
`xas->xa_index`, which retains the original search position. Callers must
compute the base: `base = xas.xa_index & ~((1 << xas_get_order(&xas)) - 1)`.

`find_lock_entries()` filters entries whose base is outside `[*start, end]`;
`find_get_entries()` does not. Callers of `find_get_entries()` that assume
`indices[i]` is the canonical base will infinite-loop in truncation paths when
the entry spans beyond the iteration range.

## XArray Multi-Index Iteration with xas_next()

`xas_next()` visits every slot including siblings of multi-order entries,
causing duplicate folio processing, or returning internal sibling entries that
must be filtered with `xa_is_sibling()`. `xas_find()` / `xas_find_marked()`
skip siblings internally. When using `xas_next()`, call
`xas_advance(&xas, folio_next_index(folio) - 1)` after processing to skip
remaining slots. See `filemap_get_read_batch()` in `mm/filemap.c`. The bug is
invisible for order-0 folios.

## Page Cache Information Disclosure

Any interface revealing per-file page cache state (resident, dirty, writeback,
evicted) must gate access behind a write-permission check to prevent
side-channel attacks. Required: `f->f_mode & FMODE_WRITE`, or
`file_owner_or_capable(f)` (not `inode_owner_or_capable(&nop_mnt_idmap, ...)`,
which ignores idmapped mounts and was the bug e187bc02f8fa fixed), or
`file_permission(f, MAY_WRITE) == 0` (see `can_do_mincore()` in `mm/mincore.c`,
`can_do_cachestat()` in `mm/filemap.c`). This applies to new syscalls, ioctls,
and procfs/sysfs interfaces even when using file descriptors rather than
virtual address ranges.

## Page Cache XArray Setup (`mapping_set_update()`)

An `XA_STATE()` on a non-shmem, non-DAX `mapping->i_pages` that adds, removes
or splits entries (changes a node's `count` or `nr_values`) must call
`mapping_set_update(&xas, mapping)` first (defined in `mm/internal.h`). This
sets callbacks for workingset shadow node tracking (`workingset_update_node()`
in `mm/workingset.c`). Without it, xa_nodes are not added to their memcg's
`struct list_lru`, leaking nodes under memory pressure.

The macro is a no-op for shmem and DAX mappings, so `mm/shmem.c` and `fs/dax.c`
correctly omit it. Paths that only delete may call
`xas_set_update(&xas, workingset_update_node)` directly, as `mm/truncate.c`
does after excluding shmem and DAX mappings itself. Folio-for-folio replacement
(`replace_page_cache_folio()`, `__folio_migrate_mapping()`) needs neither. Main
`filemap.c` paths, `collapse_file()` in `mm/khugepaged.c` and `__folio_split()`
in `mm/huge_memory.c` do it correctly; new code outside `filemap.c` that
inserts into an ordinary mapping is where it gets missed.

## Per-CPU LRU Cache Batching

Large folios are never in per-CPU LRU caches (immediately drained on add; see
`__folio_batch_add_and_move()` in `mm/folio.c`). Per-folio draining is done by
`lru_cache_drain_for_folio(folio, extra_refs, &drained)` in `mm/folio.c`
(declared in `include/linux/swap.h`). It returns early for
`!folio_may_be_lru_cached(folio)` (large folios; an mm-internal helper in
`mm/internal.h` that returns `!folio_test_large()`), compares
`folio_ref_count()` with `folio_expected_ref_count() + extra_refs`, and
escalates from `lru_add_drain()` to `lru_add_drain_all()`. See its caller
`collect_longterm_unpinnable_folios()` in `mm/gup.c`. Open-coded per-folio
`lru_add_drain_all()` should use this helper.

## Folio Eviction and Invalidation Guards

Removing a folio from page cache without checking dirty/writeback under the
folio lock causes data loss or in-flight IO corruption. Both flags change
asynchronously; checks must be after `folio_lock()`, not before.

**Required pattern** (see `mapping_evict_folio()` in `mm/truncate.c`; it does
not lock, every caller passes a locked folio, e.g. `mapping_try_invalidate()`
gets them from `find_lock_entries()`):
```c
folio_lock(folio);
if (folio_test_dirty(folio) || folio_test_writeback(folio))
	goto skip;
/* safe to remove from page cache */
```

For forceful invalidation, `folio_unmap_invalidate()` in `mm/truncate.c`
has a late dirty check but does not guard against writeback, and the folio
is already unmapped by that point.

## Quick Checks

- **Folio reference before flag tests or mapping**: `folio_test_*()` on an
  unreferenced folio silently reads another object's flags if the memory was
  reused, and hits `VM_BUG_ON_PGFLAGS()` in `const_folio_flags()` (only under
  `CONFIG_DEBUG_VM_PGFLAGS`) if it became a tail page. `folio_try_get()` must
  precede flag tests whose result is acted on in speculative lookups (advisory
  tests are tolerated, see "Lockless Page Cache Folio Access");
  `folio_get()` must precede `set_pte_at()`
- **Compound page tail pages**: in tail pages `->mapping` is `TAIL_MAPPING`,
  `->private` is expected to be 0 and `__folio_index` is meaningless, and in
  the first three tails all three slots may hold folio metadata instead, so
  reading page-cache fields from a tail page yields garbage silently. Bit 0 of
  `compound_info` (the word after `flags`, which overlays `lru.next`) marks a
  tail. Call `compound_head()` or `page_folio()` first. The folio API avoids
  this entirely
- **`folio_page()` vs PTE-mapped subpage**: `folio_page(folio, 0)` returns the
  head page, not the subpage a specific PTE maps. In PTE batch loops within a
  large folio, use `vm_normal_page()` for the actual subpage unless the batch
  starts at folio offset 0. Per-page state checks (e.g., `PageAnonExclusive()`)
  on the wrong subpage yield wrong results
- **`folio_page()` index bounds**: `folio_page(folio, n)` does unchecked
  arithmetic; `n >= folio_nr_pages(folio)` accesses past the struct page array.
  When `n` is computed from byte-offset arithmetic in truncation/split paths,
  verify boundary cases don't produce a one-past-the-end index
- **Compound page metadata after potential refcount drop**: reading
  `compound_order()`/`folio_nr_pages()` after a call that may drop the last
  reference returns garbage (page may be freed). Snapshot metadata before
  the refcount-dropping call. See `isolate_migratepages_block()` in
  `mm/compaction.c`
- **PFN advancement after page-to-folio conversion**: `folio_nr_pages()`
  is wrong for advancing PFN when starting from a tail page. Use
  `pfn += folio_nr_pages(folio) - folio_page_idx(folio, page) - 1`. See
  `isolate_migratepages_block()` in `mm/compaction.c`
- **`page_size()` / `compound_order()` on non-compound high-order pages**:
  `compound_order()` returns 0 for non-compound pages (no `PG_head`). Use
  `PAGE_SIZE << order` (not `page_size(page)`) when the page was allocated
  without `__GFP_COMP`. The folio API is safe (folios are always compound
  or order-0)
- **`_mapcount` +1 bias convention**: `_mapcount` is initialized to -1
  (zero mappings); logical mapcount = `_mapcount + 1`. All accessors
  (`folio_mapcount()`, etc.) add 1. When code reads `_mapcount` directly,
  verify the consumer expects raw (-1 based) or logical (0 based) — a
  mismatch is an off-by-one masked by range checks
- **Refcount as semantic state**: `page_count()`/`folio_ref_count()` are
  lifetime counters, not semantic indicators. Speculative references (GUP,
  memory-failure, page_idle) transiently inflate them. Use dedicated
  counters/flags for semantic state (`PageAnonExclusive()`, `pt_share_count`).
  Flag code branching on refcount == specific value for non-lifetime logic.
  Exclusivity tests against `folio_expected_ref_count()` or `1 + map_count`
  are lifetime logic and are fine
- **`folio_end_read()` on already-uptodate folios**: uses XOR for
  `PG_uptodate`, so calling with `success=true` on an already-uptodate folio
  toggles the flag off. Paths that may encounter uptodate folios must use
  `folio_unlock()` instead
- **Page/folio access after failed refcount drop**: when
  `put_page_testzero()`/`folio_put_testzero()` returns false, the caller has
  no reference — another CPU may free the page immediately. Any access after
  the failed testzero is use-after-free. Save needed metadata (flags, order,
  tags) **before** the refcount drop. See `___free_pages()` for the pattern
- **`folio->mapping` NULL for non-anonymous folios**: `folio->mapping` is
  NULL for shmem folios in swap cache and for truncated folios. Code that
  branches on `!folio_test_anon()` then dereferences `folio->mapping` will
  NULL-deref on these. NULL-check before accessing mapping members
- **XArray multi-order entry atomicity**: `xa_get_order()` under
  `rcu_read_lock()` then acting on the order under `xa_lock` is a TOCTOU race
  (entry order can change between operations). Combine `xas_load()`,
  `xas_get_order()`, and `xas_store()` in one `xas_lock_irq()` section.
  **REPORT as bugs**: `xa_get_order()` result read under RCU and later used to
  store or split entries under `xa_lock`. Using it only as an iteration hint,
  as `find_get_entries()` does, is harmless
- **Folio lock state at error labels**: when a function acquires
  `folio_lock()` early and jumps to an error label, the cleanup must call
  `folio_unlock()`. Many MM functions have multiple error labels with
  different lock states; verify the folio is actually locked at each label
  that calls `folio_unlock()`, and not unlocked at labels that skip it
- **Folio state recheck after lock acquisition**: `folio_lock()` may sleep
  (for non-trylock variants). Folio state checked before locking (mapping,
  flags, refcount, truncation) may have changed. Always re-validate folio
  state after acquiring the lock, particularly `folio->mapping != NULL`
  (folio was not truncated)
- **Zone device page metadata reinitialization**: zone device pages
  (ZONE_DEVICE) bypass `prep_new_page()`, so stale compound metadata
  (`compound_info`, `_nr_pages`, flags) persists across reuse at different
  orders. `page_pgmap()` is `page_folio(page)->pgmap`, so a stale tail marker
  in `compound_info` first redirects to a stale head and then reads its
  `pgmap`; the two share the first word of the union. Zone device init paths
  must clear all per-page compound metadata before `prep_compound_page()`
- **`page_folio()` / `compound_head()` require the page's real address**:
  when `compound_info_has_mask()` is true (`struct page` size is a power of
  two and `CONFIG_HUGETLB_PAGE_OPTIMIZE_VMEMMAP` is enabled), a tail page's
  `compound_info` holds a mask and `_compound_head()` in
  `include/linux/page-flags.h` computes the head from the address of the page
  it was passed. Calling it on a stack-local copy yields a pointer derived
  from the copy's address. For page snapshots, decode `compound_info` by hand
  against the original page address. See `snapshot_page()` in `mm/util.c`
- **Per-section metadata iteration across large folios**: under
  `CONFIG_SPARSEMEM`, `struct page_ext` arrays are per-section, not contiguous.
  Pointer arithmetic across section boundaries crashes. Use
  `for_each_page_ext()` / `page_ext_iter_next()` which re-derive via
  `page_ext_lookup()` at crossings
- **Page-count accounting in folio conversions**: when converting
  single-page code to large-folio, every `counter++` and hardcoded `1` for
  "pages processed" must become `folio_nr_pages(folio)`. Common mistake:
  updating most sites but missing one, causing undercounting for large folios
- **Folio order vs mapping entry order**: swapin paths must verify
  `folio_order()` matches the mapping entry order. Readahead can insert
  order-0 folios for slots covered by a large mapping entry; inserting
  without splitting the large entry silently loses data. See
  `shmem_split_large_entry()` in `mm/shmem.c`
- **`kmap_local_page()` maps only a single page**: on CONFIG_HIGHMEM,
  accessing beyond `PAGE_SIZE` from the returned address faults — adjacent
  pages in a high-order allocation are not mapped. Silent on 64-bit (direct
  map is contiguous). For multi-page access, iterate with
  `kmap_local_page(page + i)`. `kmap_local_folio()` also maps one page only
- **`pfn_valid()` vs `pfn_to_online_page()`**: `pfn_valid()` only confirms
  a struct page exists for the PFN; the page may be offline (memory hotplug
  removed). `pfn_to_online_page()` additionally verifies the page is in an
  online memory section. Use `pfn_to_online_page()` in hwpoison, migration,
  and any path that will access page metadata. See `pfn_to_online_page()`
  in `mm/memory_hotplug.c`
- **`pfn_to_page()` on boundary PFNs**: only safe on PFNs with valid
  `struct page`. Under `CONFIG_SPARSEMEM` without `VMEMMAP`, dereferences
  section metadata that may be invalid for non-existent sections, causing
  a crash. PFN-range loops must check termination before `pfn_to_page()`,
  not after. Latent on VMEMMAP/FLATMEM where it's simple pointer arithmetic

# Memory Management Subsystem Details

## PTE State Consistency

Incorrect PTE flag combinations cause data corruption (dirty data silently
dropped), security holes (writable pages that should be read-only), and kernel
crashes on architectures that trap invalid combinations. Review any code that
constructs or modifies PTEs for these invariants.

**Invariants** (software-enforced, not hardware):
- Writable PTEs must be dirty: a clean+writable PTE is invalid
  - For shared mappings, `can_change_shared_pte_writable()` in `mm/mprotect.c`
    enforces this by only returning true when `pte_dirty(pte)` (clean shared
    PTEs need a write-fault for filesystem writenotify)
  - For private/anonymous mappings, code paths use `pte_mkwrite(pte_mkdirty(entry))`
    to set both together (see `do_anonymous_page()` in `mm/memory.c`,
    `migrate_vma_insert_page()` in `mm/migrate_device.c`)
  - **Exception -- MADV_FREE**: `madvise_free_pte_range()` in `mm/madvise.c`
    clears the dirty bit via `clear_young_dirty_ptes()` but preserves write
    permission, intentionally creating a clean+writable PTE. This allows the
    page to be reclaimed without writeback (it's clean and lazyfree), but if
    the process writes new data before reclaim, the page becomes dirty again
    without a full write-protect fault. On x86, `pte_mkclean()` only clears
    `_PAGE_DIRTY_BITS` and does not touch `_PAGE_RW`, so hardware sets dirty
    directly with no fault at all. On arm64, `pte_mkclean()` sets `PTE_RDONLY`
    but preserves `PTE_WRITE`; with FEAT_HAFDBS hardware clears `PTE_RDONLY`
    on write (no fault), without it a minor fault resolves quickly since
    `pte_write()` is still true
- Dirty implies accessed as a software convention: `pte_mkdirty()` does NOT
  set the accessed bit (x86, arm64), so code paths must set both explicitly
- Non-accessed+writable is invalid on architectures without hardware A/D bit
  management (on x86, hardware sets accessed automatically on first access)

**Migration entries** (`include/linux/swapops.h`):
- Encode A/D bits via `SWP_MIG_YOUNG_BIT` and `SWP_MIG_DIRTY_BIT`
- Only available when `migration_entry_supports_ad()` returns true (depends on
  whether the architecture's swap offset has enough free bits; controlled by
  `swap_migration_ad_supported` in `mm/swapfile.c`)
- `make_migration_entry_young()` / `make_migration_entry_dirty()` preserve
  original PTE state into the migration entry
- `remove_migration_pte()` in `mm/migrate.c` restores A/D bits: dirty is set
  only if both the migration entry AND the folio are dirty (avoids re-dirtying
  a folio that was cleaned during migration)

**NUMA balancing** (see `change_pte_range()` in `mm/mprotect.c`):
- Skips PTEs already `pte_protnone()` to avoid double-faulting
- Checks `folio_can_map_prot_numa()` before applying NUMA hint faults

**Swap entries** (see `try_to_unmap_one()` in `mm/rmap.c`):
- Only exclusive, soft-dirty, and uffd-wp flags survive in swap PTEs;
  all other PTE state is lost on swap-out
- `pte_swp_clear_flags()` in `include/linux/swapops.h` strips these flags
  to extract the bare swap entry for comparison (see `pte_same_as_swp()`
  in `mm/swapfile.c`)

**Non-present PTE type dispatch** (see `check_pte()` in
`mm/page_vma_mapped.c`, `softleaf_type()` in `include/linux/leafops.h`):

Non-present PTEs encode several distinct swap entry types via the
`softleaf_type` / `swp_type` field. Each type has different semantics and must
be handled in the correct branch of any dispatch logic. Accepting an entry type
in the wrong branch causes semantic confusion (e.g., treating a
device-exclusive entry as a migration entry), which may silently produce wrong
behavior even if the types share the PFN-encoding property.

The distinct non-present PTE categories are:
- **Migration** (`SOFTLEAF_MIGRATION_READ`, `_READ_EXCLUSIVE`, `_WRITE`):
  page temporarily unmapped during folio migration; checked via
  `softleaf_is_migration()` / `is_migration_entry()`
- **Device-private** (`SOFTLEAF_DEVICE_PRIVATE_READ`, `_WRITE`): page migrated
  to un-addressable device memory (HMM); checked via
  `softleaf_is_device_private()` / `is_device_private_entry()`
- **Device-exclusive** (`SOFTLEAF_DEVICE_EXCLUSIVE`): CPU access temporarily
  revoked for device atomic operations, page remains in host memory; checked
  via `softleaf_is_device_exclusive()` / `is_device_exclusive_entry()`
- **HW poison** (`SOFTLEAF_HWPOISON`): page has uncorrectable memory error;
  checked via `softleaf_is_hwpoison()` / `is_hwpoison_entry()`
- **Marker** (`SOFTLEAF_MARKER`): metadata-only entry (e.g., uffd-wp marker,
  poison marker); checked via `softleaf_is_marker()` / `is_pte_marker()`

When reviewing code that adds a new swap entry type or modifies dispatch logic
over non-present PTEs, verify that each branch accepts only the entry types
whose semantics match that branch's purpose. A common mistake is grouping
device-exclusive with migration (both involve temporarily unmapped pages with
PFNs) even though their refcount behavior, resolution paths, and semantics
are entirely different. `softleaf_has_pfn()` in `include/linux/leafops.h`
shows which types encode a PFN -- sharing this property does not make types
interchangeable in dispatch logic.

**Flag transfer on non-present-to-present PTE reconstruction:**

Every code path that converts a non-present PTE (swap, migration, or
device-exclusive entry) to a present PTE must carry over the soft-dirty
and uffd-wp bits. These bits have different encodings in swap PTEs vs
present PTEs, so they require explicit read-then-write transfer:
```c
if (pte_swp_soft_dirty(old_pte))
    newpte = pte_mksoft_dirty(newpte);
if (pte_swp_uffd_wp(old_pte))
    newpte = pte_mkuffd_wp(newpte);
```
This pattern is required in `do_swap_page()`, `restore_exclusive_pte()` in
`mm/memory.c`, `remove_migration_pte()`, `try_to_map_unused_to_zeropage()`
in `mm/migrate.c`, and `unuse_pte()` in `mm/swapfile.c`. When converting
between non-present entries (swap-to-swap), use the swap-side writers
instead: `pte_swp_mksoft_dirty()` and `pte_swp_mkuffd_wp()` (see
`copy_nonpresent_pte()` in `mm/memory.c`)

**Soft dirty vs hardware dirty in PTE move/remap:**

Soft dirty (`pte_mksoft_dirty()` / `pte_swp_mksoft_dirty()`) is a
userspace-visible tracking bit for `/proc/pid/pagemap` and CRIU, distinct
from hardware dirty (`pte_mkdirty()`). PTE move operations (mremap,
userfaultfd UFFDIO_MOVE) must set soft dirty on the destination to signal
the mapping changed, while preserving the source PTE's hardware dirty state.
Common mistakes:
- Using `pte_mkdirty()` when the intent is to mark the PTE as "touched" for
  userspace tracking -- this should be `pte_mksoft_dirty()`
- Handling present PTEs but forgetting `pte_swp_mksoft_dirty()` for swap PTEs
- Using `#ifdef CONFIG_MEM_SOFT_DIRTY` instead of
  `pgtable_supports_soft_dirty()`, which also handles runtime detection (e.g.,
  RISC-V ISA extensions)

See `move_soft_dirty_pte()` in `mm/mremap.c` for the reference implementation
handling both present and swap cases.

## Special vs Normal Page Table Mappings

Marking a normal refcounted folio's page table entry as "special" causes
`vm_normal_page()` (and `vm_normal_page_pmd()` / `vm_normal_page_pud()`)
to return NULL, hiding the folio from page table walkers, GUP, and refcount
management. GUP-fast checks `pte_special()` / `pmd_special()` /
`pud_special()` early and bails out, falling back to slow GUP.

**Invariant** (see `__vm_normal_page()` in `mm/memory.c`):
- Normal refcounted folios must NOT have their page table entry marked
  special (`pte_mkspecial()` / `pmd_mkspecial()` / `pud_mkspecial()`)
- Only raw PFN mappings (VM_PFNMAP, VM_MIXEDMAP without struct page),
  devmap entries (`pte_mkdevmap()` / `pmd_mkdevmap()` / `pud_mkdevmap()`),
  and the shared zero folios may be marked special
- Use `folio_mk_pmd()` / `folio_mk_pud()` when constructing entries for
  normal refcounted folios; these helpers produce a plain huge entry
  without setting the special bit (see `include/linux/mm.h`)
- Use `pfn_pmd()` + `pmd_mkspecial()` or `pfn_pud()` + `pud_mkspecial()`
  only for raw PFN mappings

**Common mistake**: When a `vmf_insert_folio_*()` function reuses a
PFN-oriented helper (e.g., `insert_pfn_pud()`), the helper's
unconditional `pXd_mkspecial()` call applies to the folio mapping too.
The fix is to split the entry-construction logic so the folio path uses
`folio_mk_pXd()` without the special bit, while the PFN path retains
`pXd_mkspecial()` (see `insert_pmd()` and `insert_pud()` in
`mm/huge_memory.c` for the correct pattern using `struct folio_or_pfn`).

## Page Table Entry to Folio/Page Conversion Preconditions

Applying a present-entry conversion function to a non-present page table
entry (migration entry, swap entry, or poisoned entry) interprets swap
metadata bits as a physical page frame number, producing a bogus
`struct page *` that causes an invalid address dereference.

**Functions that require a present entry:**
- `pmd_folio(pmd)` / `pmd_page(pmd)` -- expand to `pfn_to_page(pmd_pfn(pmd))`,
  which is only valid when `pmd_present(pmd)` or `pmd_trans_huge(pmd)` or
  `pmd_devmap(pmd)` (see `include/linux/pgtable.h`)
- `pte_page(pte)` / `vm_normal_page()` -- only valid when `pte_present(pte)`

**Correct conversion for non-present entries:**
- Migration entries: `pmd_to_swp_entry()` or `pte_to_swp_entry()` to extract
  the `swp_entry_t`, then `pfn_swap_entry_folio()` to get the folio (see
  `include/linux/swapops.h`)
- Alternatively, if the folio comparison is not needed for a non-present
  entry (e.g., because a migration entry is locked and cannot refer to the
  target folio), skip the conversion entirely

**Review pattern:** When code handles multiple PMD/PTE states in a combined
conditional (e.g., `if (pmd_trans_huge(*pmd) || is_pmd_migration_entry(*pmd))`),
verify that subsequent operations like `pmd_folio()` or `pmd_page()` are
guarded to execute only on the present-entry cases. A common mistake is
adding a non-present entry type to an existing condition without adjusting
the folio extraction that follows.

## Lazyfree Folio Reclaim State Transitions

Setting a lazyfree folio back to swapbacked when it was not actually dirtied
causes the folio to be unnecessarily treated as swap-eligible on subsequent
reclaim attempts instead of being cheaply discarded, degrading performance.
More critically, it can interact with speculative references to create a race
where clean lazyfree folios are permanently stuck as swapbacked, preventing
efficient reclaim of MADV_FREE memory.

Lazyfree folios (anonymous folios marked with `MADV_FREE`, identified by
`!folio_test_swapbacked(folio)`) may be discarded during reclaim without
writeback if they are still clean. The reclaim path must distinguish three
cases, and the decision order matters:

1. **Folio is dirty** (and not `VM_DROPPABLE`): the folio was redirtied
   via the page table or a GUP reference. Set `folio_set_swapbacked()`
   and remap -- the folio must go through normal swap-out on a future
   reclaim attempt.
2. **Extra references** (`ref_count != 1 + map_count`): a GUP pin,
   speculative reference (e.g., from `deferred_split_scan()`), or other
   temporary reference is held. Remap the PTE/PMD and abort, but do
   **not** call `folio_set_swapbacked()` -- the elevated refcount does
   not mean the folio was dirtied. Reclaim will retry later when the
   extra reference is dropped.
3. **Clean and no extra references**: discard the folio (decrement
   `MM_ANONPAGES`, proceed to `discard:` label).

**Why order matters:** checking refcount before dirty status, or
unconditionally setting swapbacked on any abort, conflates "temporarily
pinned" with "genuinely redirtied." A speculative `folio_try_get()` can
transiently elevate the refcount without dirtying the folio, so falling
through to `folio_set_swapbacked()` on refcount mismatch alone is wrong.

**Both PTE and PMD paths must follow this order:**
- PTE path: the `!folio_test_swapbacked(folio)` block in
  `try_to_unmap_one()` in `mm/rmap.c`
- PMD path: `__discard_anon_folio_pmd_locked()` in `mm/huge_memory.c`

**Required barrier protocol** (same as `__remove_mapping()` in
`mm/vmscan.c`):
- `smp_mb()` between clearing the PTE/PMD and reading `folio_ref_count()`
  -- synchronizes with GUP-fast's `inc refcount; barrier; read PTE` sequence
- `smp_rmb()` between reading `folio_ref_count()` and reading
  `folio_test_dirty()` -- ensures a concurrent `write_to(page);
  folio_set_dirty(); folio_put()` sequence cannot escape unnoticed (refcount
  must be read before dirty flag)

**REPORT as bugs**: code in lazyfree reclaim paths that calls
`folio_set_swapbacked()` on a path that did not first confirm the folio
is dirty, or that unconditionally sets swapbacked when reclaim is aborted
for any reason (including elevated refcount).

## PTE Batching

Batching consecutive PTEs that map the same large folio into a single
`set_ptes()` call propagates the first PTE's permission bits to all entries
in the batch, because `set_ptes()` only advances the PFN and preserves all
other bits. If the batch includes PTEs with different permissions (e.g.,
writable vs read-only), the result silently overwrites the intended
permissions, causing security bypasses.

`folio_pte_batch()` in `mm/util.c` is a simplified wrapper that calls
`folio_pte_batch_flags()` in `mm/internal.h` with `flags=0`. With no flags,
differences in writable, dirty, and soft-dirty bits are ignored and PTEs
with different permissions are batched together.

**FPB flags** (defined as `fpb_t` in `mm/internal.h`) control which PTE bits
are compared vs ignored during batching:

| Flag | Effect |
|------|--------|
| `FPB_RESPECT_WRITE` | Include the writable bit in comparison; PTEs with different write permissions will not batch |
| `FPB_RESPECT_DIRTY` | Include the dirty bit in comparison |
| `FPB_RESPECT_SOFT_DIRTY` | Include the soft-dirty bit in comparison |
| `FPB_MERGE_WRITE` | After batching, if any PTE was writable, set the writable bit on the output PTE |
| `FPB_MERGE_YOUNG_DIRTY` | After batching, merge young and dirty bits from all PTEs into the output |

- `folio_pte_batch()` (no flags): safe only when the caller does not stamp the
  first PTE's permission bits onto other entries (e.g., `zap_present_ptes()`
  which clears all PTEs, or `folio_unmap_pte_batch()` which unmaps)
- `folio_pte_batch_flags()` with `FPB_RESPECT_WRITE`: required when the caller
  uses `set_ptes()` to write the batched PTE value back (see `move_ptes()` in
  `mm/mremap.c`, `change_pte_range()` in `mm/mprotect.c`)

**REPORT as bugs**: Code that uses `folio_pte_batch()` (without flags) to
determine a batch count and then passes that count to `set_ptes()`, because
the first PTE's writable/dirty/soft-dirty bits will be stamped onto all
entries in the batch.

**Batched PTE operation boundaries:**

Passing an uncapped `max_nr` to `folio_pte_batch()` causes out-of-bounds reads
past the end of a page table. The `max_nr` parameter must be capped so that
scanning stays within a single page table and a single VMA. The standard
expression is `(pmd_addr_end(addr, vma->vm_end) - addr) >> PAGE_SHIFT`. Code
that reaches PTE-level iteration through the standard walker hierarchy
(`zap_pmd_range()` -> `zap_pte_range()`) receives a pre-capped `end`. Code
that operates directly at PTE level via `page_vma_mapped_walk()` must perform
its own PMD boundary capping.

**REPORT as bugs**: Any caller of `folio_pte_batch()` that derives `max_nr`
from `folio_nr_pages()` without capping at the PMD boundary.

## page_vma_mapped_walk() Non-Present Entries

Calling PTE accessor functions (`pte_young()`, `pte_dirty()`, `pte_write()`,
`ptep_clear_flush_young()`, etc.) on a non-present entry returned by
`page_vma_mapped_walk()` produces undefined results because swap entries
encode bits differently than present PTEs. This class of bug went undetected
because the non-present entries only appear with device-exclusive or
device-private ZONE_DEVICE pages.

`page_vma_mapped_walk()` in `mm/page_vma_mapped.c` can return `true` with
`pvmw.pte` pointing to non-present entries. The `check_pte()` helper accepts
three PTE types when `PVMW_MIGRATION` is not set:

| Entry type | `pte_present()` | How to identify |
|------------|-----------------|-----------------|
| Normal present PTE | true | `pte_present(ptep_get(pvmw.pte))` |
| Device-exclusive swap entry | false | `softleaf_is_device_exclusive(...)` |
| Device-private swap entry | false | `softleaf_is_device_private(...)` |

**Rules for rmap walk callbacks** (functions passed to `rmap_walk()` or using
`page_vma_mapped_walk()`):
- When `pvmw.pte` is set, always check `pte_present(ptep_get(pvmw.pte))`
  before calling present-PTE accessors (`pte_pfn()`, `pte_dirty()`,
  `pte_write()`, `pte_young()`, `pte_soft_dirty()`, `pte_uffd_wp()`)
- Non-present PFN swap PTEs (device-exclusive and device-private entries)
  require the swap-PTE accessor family instead: `swp_offset_pfn()` for PFN,
  `is_writable_device_private_entry()` for writability, `pte_swp_soft_dirty()`
  and `pte_swp_uffd_wp()` for flags. Both families accept `pte_t` with no
  compile-time distinction, so using the wrong family silently reads wrong
  bits. See `try_to_migrate_one()` and `try_to_unmap_one()` in `mm/rmap.c`
  for the correct dispatching pattern
- Non-present PFN swap PTEs represent pages that are "old" and "clean" from
  the CPU's perspective; MMU notifiers handle device-side access tracking

## Large Folio State Tracking

Misunderstanding which flags are per-page vs per-folio leads to bugs where code
checks or sets state on the wrong struct page. A common mistake is assuming all
flags work like small pages when operating on subpages of a large folio.

The Tracking Level column indicates where the state lives. **Per-folio** means a
single value on the head page applies to the entire folio. **Per-page** means
each subpage carries its own independent value. **PTE-level** means the state is
in the page table entry, not in struct page at all. **Mixed** means the
granularity depends on how the folio is mapped.

| State | Tracking Level | Details |
|-------|---------------|---------|
| PageAnonExclusive | **Mixed** | Per-page for PTE-mapped THP; per-folio (head page) for PMD-mapped and HugeTLB (see `PG_anon_exclusive` in `include/linux/page-flags.h` and `RMAP_EXCLUSIVE` handling in `__folio_add_rmap()` in `mm/rmap.c`) |
| PG_hwpoison | **Per-page** | Marks the specific corrupted subpage (`PF_ANY`); distinct from `PG_has_hwpoisoned` (`PF_SECOND`) which only indicates at least one subpage is poisoned. Both needed: per-page flag identifies which page, per-folio flag enables fast folio-level check |
| PG_dirty | **Per-folio** | Single flag on head page via `PF_HEAD` policy; PTE-level dirty bits tracked separately in page table entries |
| Accessed/young | **PTE-level** | Tracked in page table entries, not in struct page; folio-level `PG_referenced` on head page is a separate LRU aging flag |
| Reference count | **Per-folio** | Single `_refcount` on head page shared by all subpages (see `folio_ref_count()` in `include/linux/page_ref.h`) |
| Mapcount | **Per-page** | Each subpage has `_mapcount` by default; `CONFIG_NO_PAGE_MAPCOUNT` (experimental) eliminates per-page mapcounts, using only folio-level `_large_mapcount` and `_entire_mapcount` (see `include/linux/mm_types.h`) |

**Page flag policies** control which struct page within a folio carries each flag.
Using the wrong page silently reads stale data or corrupts unrelated state. See
the "Page flags policies wrt compound pages" comment block in `include/linux/page-flags.h`:
- `PF_HEAD`: flag operations redirect to head page (most flags)
- `PF_ANY`: flag is relevant for head, tail, and small pages
- `PF_NO_TAIL`: modifications only on head/small pages, reads allowed on tail
- `PF_SECOND`: flag stored in the first tail page (e.g., `PG_has_hwpoisoned`,
  `PG_large_rmappable`, `PG_partially_mapped`)

**Atomic vs non-atomic page flag operations:**

Non-atomic flag operations (`__set_bit` / `__clear_bit`, generated by
`__FOLIO_SET_FLAG` / `__FOLIO_CLEAR_FLAG` in `include/linux/page-flags.h`)
perform a read-modify-write on the entire `unsigned long` flags word. They
are only safe when the caller has exclusive access to the whole flags word --
not merely when access to the individual bit is serialized by a lock. Multiple
page flags share the same `unsigned long`, so a lock that serializes one
flag does NOT protect against concurrent modification of a different flag in
the same word by code running under a different lock.

This is especially important for `PF_SECOND` flags (stored on the first tail
page): `PG_has_hwpoisoned`, `PG_large_rmappable`, `PG_partially_mapped`, and
`PG_anon_exclusive` (via `PF_ANY` on tail pages) all share the same flags
word and are modified by different subsystems under different locks.

**REPORT as bugs**: Code that uses non-atomic page flag operations
(`__folio_set_*` / `__folio_clear_*` / `__SetPage*` / `__ClearPage*`) on a
page whose flags word can be concurrently modified by another code path,
unless the caller holds exclusive access to the entire page (e.g., during
allocation before the page is visible, or during final freeing).

## Page Cache Reference Counting for Large Folios

Using `folio_put()` instead of `folio_put_refs(folio, folio_nr_pages(folio))`
when dropping a large folio's page cache references leaks
`folio_nr_pages(folio) - 1` references, preventing the folio from ever being
freed. This is a silent memory leak that only manifests with large folios
(order > 0) in the page cache, so it is easily missed with order-0 testing.

**Page cache reference convention:**

When a folio is added to the page cache, `__filemap_add_folio()` in
`mm/filemap.c` adds `folio_nr_pages(folio)` extra references via
`folio_ref_add(folio, nr)`. A page-cache folio's refcount includes
1 (base) + `folio_nr_pages()` (page cache) + any other holders. For order-0
folios this is just 1 + 1 = 2, but for an order-2 folio it is 1 + 4 = 5.

**Correct removal pattern:**

`filemap_free_folio()` in `mm/filemap.c` is the standard function for
releasing page cache references after removal: it calls
`folio_put_refs(folio, folio_nr_pages(folio))`. Code that calls
`__filemap_remove_folio()` directly (bypassing `filemap_free_folio()`)
must drop the correct number of refs manually.

**REPORT as bugs**: Any call to `folio_put()` (single-ref drop) immediately
after `__filemap_remove_folio()` on a folio that may have order > 0. The
correct call is `folio_put_refs(folio, folio_nr_pages(folio))`.

## Folio Tail Page Overlay Layout

Moving or adding fields in `struct folio` that overlay a new tail page's
`->mapping` offset without updating all layout-dependent consumers causes
"corrupted mapping in tail page" errors from `free_tail_page_prepare()`,
or stale metadata surviving across HVO vmemmap restore.

`struct folio` (in `include/linux/mm_types.h`) is a series of
`struct page`-sized unions (`page`, `__page_1`, `__page_2`, `__page_3`).
Each tail page slot beyond page[0] overlays folio-internal metadata onto
the `struct page` fields at that offset. `prep_compound_tail()` in
`mm/internal.h` initializes `->mapping` to `TAIL_MAPPING` for all tail
pages; metadata-carrying tail pages later overwrite `->mapping` with
their own data.

**Layout consumers that must stay in sync:**

| Consumer | File | What it encodes |
|----------|------|-----------------|
| `free_tail_page_prepare()` | `mm/page_alloc.c` | `switch (page - head_page)` skips the `TAIL_MAPPING` check for each metadata-carrying tail page |
| `NR_RESET_STRUCT_PAGE` | `mm/hugetlb_vmemmap.c` | Number of struct pages HVO must reset from a clean copy when restoring vmemmap; must cover all tail pages whose `->mapping` may not be `TAIL_MAPPING` |
| `__dump_folio()` | `mm/debug.c` | Prints folio-specific fields from known tail page offsets |

When reviewing patches that rearrange `struct folio` fields across tail
page boundaries, verify that ALL consumers listed above are updated to
reflect the new layout. The common failure mode is updating
`free_tail_page_prepare()` but missing `NR_RESET_STRUCT_PAGE` (or vice
versa), because these are in separate files with no compile-time coupling.

## Large Folio PTE Installation

Failing to handle a non-empty PTE range when installing a large folio causes
a livelock: the fault retries endlessly, finding the same populated PTEs each
time, never installing the PTE for the faulting address. This is especially
dangerous because it manifests as a hung process with no kernel warning.

When a fault handler prepares to install PTEs for a multi-page folio, it
checks `pte_range_none()` under the page table lock to verify the entire
range is empty (see `finish_fault()` and `do_anonymous_page()` in
`mm/memory.c`). If any PTE in the range is already populated, the handler
must ensure forward progress for the faulting address:

**Correct strategies when `pte_range_none()` returns false:**
- **Page cache folios** (shmem, file-backed in `finish_fault()`): fall back
  to installing a single PTE for just the faulting page within the folio.
  The folio already exists in the page cache and cannot be discarded, so the
  handler must succeed at single-PTE granularity
- **Freshly allocated anonymous folios** (`do_anonymous_page()`): release
  the folio and return to the fault entry point, which retries allocation
  at a potentially smaller size via `alloc_anon_folio()`
- **PMD-level mapping** (`do_set_pmd()`): return `VM_FAULT_FALLBACK` so
  the caller retries at PTE granularity

**REPORT as bugs**: Code that returns `VM_FAULT_NOPAGE` (retry) when
`pte_range_none()` fails for a page cache folio without reducing `nr_pages`
or switching to single-PTE installation, as this creates an infinite retry
loop.

## Folio Mapcount vs Refcount Relationship

Reversing a mapcount-vs-refcount comparison direction in assertions or
exclusivity checks causes either spurious warnings on normal operation or
silent acceptance of corrupted state. Multiple code paths across MM compare
these counters; each must get the direction correct.

**Invariant**: `folio_ref_count(folio) >= folio_mapcount(folio)`. Each page
table mapping holds exactly one reference, so every unit of mapcount has a
corresponding unit of refcount. Additional non-mapping references increase
refcount beyond mapcount.

**Sources of extra refcount** (refcount without corresponding mapcount):
- Swapcache, page cache, `PG_private` (file-backed), GUP pins, LRU
  isolation, in-progress operations (migration, split, writeback)

See `folio_expected_ref_count()` in `include/linux/mm.h`, which computes the
expected refcount as `folio_mapcount(folio)` plus all known non-mapping
reference sources.

**Common comparison patterns**:
- Exclusivity: `mapcount == refcount` means no external users hold the folio
  (see `__wp_can_reuse_large_anon_folio()` in `mm/memory.c`)
- Sanity assertions: `mapcount > refcount` is the impossible/corrupted
  condition to warn on, NOT `mapcount < refcount` (which is normal)

## SLAB_TYPESAFE_BY_RCU and VMA Recycling

Dereferencing a parent/owner pointer from a `SLAB_TYPESAFE_BY_RCU` object
after dropping the object's refcount causes use-after-free when the object has
been recycled to a different owner. The owner can exit and free its backing
structure in the window between the refcount drop and the dereference.

The VMA cache is created with `SLAB_TYPESAFE_BY_RCU` (see `vma_state_init()`
in `mm/vma_init.c`), which means a VMA's slab memory remains valid through an
RCU read-side critical section even after `vm_area_free()`, but the VMA can be
reallocated to a completely different `mm_struct` during that window.

**Per-VMA lock lookup protocol** (see `lock_vma_under_rcu()` and
`vma_start_read()` in `mm/mmap_lock.c`):
1. `mas_walk()` under `rcu_read_lock()` finds a VMA in the maple tree
2. `vma_start_read()` increments `vma->vm_refcnt`
3. If `vma->vm_mm != mm` (VMA was recycled), the refcount must be dropped --
   but `vma_refcount_put()` dereferences `vma->vm_mm` for `rcuwait_wake_up()`
4. The foreign `mm` must be stabilized with `mmgrab()` before calling
   `vma_refcount_put()`, then released with `mmdrop()` afterward

**REPORT as bugs**: Code paths in `lock_vma_under_rcu()`, `lock_next_vma()`,
or `vma_start_read()` that call `vma_refcount_put()` on a VMA whose `vm_mm`
does not match the caller's `mm` without first stabilizing the foreign `mm`
via `mmgrab()`.

## Hugetlb Folio Type Transition Races

Accessing hugetlb-specific folio metadata (such as calling `folio_hstate()`)
after an unlocked `folio_test_hugetlb()` check causes a NULL pointer
dereference when another CPU concurrently clears the hugetlb type and frees
the folio.

`__update_and_free_hugetlb_folio()` in `mm/hugetlb.c` calls
`__folio_clear_hugetlb()` under `hugetlb_lock`, which clears the hugetlb
page type. After the type is cleared, `folio_hstate()` (in
`include/linux/hugetlb.h`) calls `size_to_hstate(folio_size())` which returns
NULL because the folio size no longer matches any registered hstate.

```c
// WRONG: TOCTOU race
if (folio_test_hugetlb(folio)) {
    h = folio_hstate(folio);  // May return NULL if type cleared concurrently
}

// CORRECT: Check and use under the same lock
spin_lock_irq(&hugetlb_lock);
if (folio_test_hugetlb(folio)) {
    h = folio_hstate(folio);
}
spin_unlock_irq(&hugetlb_lock);
```

An unlocked `folio_test_hugetlb()` is acceptable as a preliminary fast-path
filter (to avoid taking the lock), but the result must not be trusted for
subsequent hstate derivation without re-checking under the lock. Code outside
`mm/hugetlb.c` that encounters hugetlb pages through lockless PFN iteration
(such as `has_unmovable_pages()` in `mm/page_isolation.c`) must use
`size_to_hstate()` with a NULL check instead of `folio_hstate()`.

## Large Folio Split Minimum Order

Splitting a file-backed large folio below the mapping's minimum folio order
fails with `-EINVAL`. Callers that assume a successful split always yields
order-0 folios will hit warnings, operate on unexpectedly large folios, or
mishandle error paths on LBS (large block size) filesystems.

File-backed address spaces can set a minimum folio order via
`mapping_set_folio_min_order()` (see `mapping_min_folio_order()` in
`include/linux/pagemap.h`). The split infrastructure in `__folio_split()` in
`mm/huge_memory.c` enforces this: if `new_order < min_order`, the split returns
`-EINVAL`.

**Split API behavior:**
- `split_huge_page()` and `split_folio_to_list()` always request order-0.
  They will fail for file-backed folios whose mapping has min order > 0.
- `try_folio_split_to_order()` takes an explicit `new_order` parameter. Its
  documentation states: "Use `min_order_for_split()` to get the lower bound
  of `@new_order`" (see `include/linux/huge_mm.h`).
- `min_order_for_split()` in `mm/huge_memory.c` returns
  `mapping_min_folio_order(folio->mapping)` for file-backed folios and 0 for
  anonymous folios.

**Review checklist for folio split callers:**
- If code calls `split_huge_page()` or `split_folio_to_list()` and then
  assumes the result is order-0 (e.g., `WARN_ON(folio_test_large(folio))`),
  verify it handles `-EINVAL` from mappings with min order > 0
- If code needs to split to the lowest possible order, it must call
  `min_order_for_split()` first and pass that order explicitly to
  `try_folio_split_to_order()` or `split_huge_page_to_list_to_order()`
- After a successful split to non-zero order, the resulting folios are still
  large (`folio_test_large()` returns true); code must not assume they are
  base pages

## GFP Flags Context

Using the wrong GFP flag causes sleeping in atomic context (deadlock/BUG),
filesystem or IO recursion (deadlock), or silent allocation failures when the
caller assumes success. Verify the allocation context matches the flag.

The Reclaim column indicates which memory reclaim mechanisms are available.
"kswapd only" means the allocation wakes the background kswapd thread but never
blocks waiting for reclaim to complete. "Full" means the caller may also perform
direct reclaim synchronously, blocking until pages are freed.

| Flag | Sleeps | Reclaim | Key Flags | Use Case |
|------|--------|---------|-----------|----------|
| GFP_ATOMIC | No | kswapd only | `__GFP_HIGH \| __GFP_KSWAPD_RECLAIM` | IRQ/spinlock context, lower watermark access |
| GFP_KERNEL | Yes | Full (direct + kswapd) | `__GFP_RECLAIM \| __GFP_IO \| __GFP_FS` | Normal kernel allocation |
| GFP_NOWAIT | No | kswapd only | `__GFP_KSWAPD_RECLAIM \| __GFP_NOWARN` | Non-sleeping, likely to fail |
| GFP_NOIO | Yes | Direct + kswapd, no IO | `__GFP_RECLAIM` | Avoid block IO recursion |
| GFP_NOFS | Yes | Direct + kswapd, no FS | `__GFP_RECLAIM \| __GFP_IO` | Avoid filesystem recursion |

See "Useful GFP flag combinations" in `include/linux/gfp_types.h`.

**Notes:**
- `__GFP_RECLAIM` = `__GFP_DIRECT_RECLAIM | __GFP_KSWAPD_RECLAIM`
- GFP_NOIO can still direct-reclaim clean page cache and slab pages (no physical IO)
- Prefer `memalloc_nofs_save()`/`memalloc_noio_save()` over GFP_NOFS/GFP_NOIO
- `__GFP_KSWAPD_RECLAIM` (present in `GFP_NOWAIT` and `GFP_ATOMIC`) triggers
  `wakeup_kswapd()` in `mm/vmscan.c`, which calls `wake_up_interruptible()`
  and enters the scheduler via `try_to_wake_up()`. This means even non-sleeping
  allocations can take scheduler and timer locks. Code that allocates under
  scheduler-internal locks (e.g., hrtimer base lock, runqueue lock) or with
  preemption disabled must strip `__GFP_KSWAPD_RECLAIM` or use bare flags like
  `__GFP_NOWARN` to avoid lock recursion. See `gfp_nested_mask()` in
  `include/linux/gfp.h` for the standard approach to constraining nested
  allocation flags
- `current_gfp_context()` in `include/linux/sched/mm.h` strips `__GFP_IO`
  and/or `__GFP_FS` when the task runs under a scoped
  `memalloc_noio_save()` or `memalloc_nofs_save()` constraint. After
  narrowing, a `GFP_KERNEL` allocation becomes `GFP_NOIO` or `GFP_NOFS`,
  which still include `__GFP_DIRECT_RECLAIM` (can sleep). Testing the
  narrowed value against a composite constant like
  `(gfp & GFP_KERNEL) != GFP_KERNEL` misclassifies these as atomic,
  because the stripped `__GFP_IO`/`__GFP_FS` bits cause the comparison to
  fail. Use the single-flag helpers instead: `gfpflags_allow_blocking(gfp)`
  tests `__GFP_DIRECT_RECLAIM` (can this allocation sleep?),
  `gfpflags_allow_spinning(gfp)` tests `__GFP_RECLAIM` (can this
  allocation take locks?). See `include/linux/gfp.h`

**Placement constraints** (see "Page mobility and placement hints" in
`include/linux/gfp_types.h`):
- `GFP_ZONEMASK` (`__GFP_DMA | __GFP_HIGHMEM | __GFP_DMA32 | __GFP_MOVABLE`)
  selects the physical memory zone. Code that intercepts allocations and serves
  memory from a pre-allocated pool (e.g., KFENCE in `mm/kfence/core.c`, swiotlb
  in `kernel/dma/swiotlb.c`) must skip requests with zone constraints it cannot
  satisfy
- `__GFP_THISNODE` forces the allocation to the requested NUMA node with no
  fallback. It is NOT part of `GFP_ZONEMASK` -- checking only `GFP_ZONEMASK`
  misses this constraint. Pool-based allocators on NUMA systems must also check
  `__GFP_THISNODE` when their pool pages may not reside on the caller's
  requested node
- When stripping placement flags for validation, use the full set as in
  `__alloc_contig_verify_gfp_mask()` in `mm/page_alloc.c`:
  `GFP_ZONEMASK | __GFP_RECLAIMABLE | __GFP_WRITE | __GFP_HARDWALL |
  __GFP_THISNODE | __GFP_MOVABLE`

## __GFP_ACCOUNT

Incorrect memcg accounting lets a container allocate kernel memory without being
charged, bypassing its memory limit. Review any new `__GFP_ACCOUNT` usage or
`SLAB_ACCOUNT` cache creation.

- Slabs created with `SLAB_ACCOUNT` are charged to memcg automatically via
  `memcg_slab_post_alloc_hook()` in `mm/slub.c`, even without explicit
  `__GFP_ACCOUNT` in the allocation call

**Validation:**
1. When using `__GFP_ACCOUNT`, ensure the correct memcg is charged
   - `old = set_active_memcg(memcg); work; set_active_memcg(old)`
2. Most usage does not need `set_active_memcg()`, but:
   - Kthreads switching context between many memcgs may need it
   - Helpers operating on objects (e.g., BPF maps) with stored memcg may need it
3. Ensure new `__GFP_ACCOUNT` usage is consistent with surrounding code

## VM Committed Memory Accounting

Missing the undo call after a successful `security_vm_enough_memory_mm()`
permanently inflates the `vm_committed_as` counter. Under strict overcommit
(`vm.overcommit_memory=2`), each leaked charge reduces the system's capacity
for new mappings, eventually causing legitimate `mmap()`, `brk()`, and shmem
operations to fail with `-ENOMEM` even when physical memory is available.

`security_vm_enough_memory_mm()` in `security/security.c` is not just a
check -- on success, it calls `__vm_enough_memory()` in `mm/util.c`, which
increments the global `vm_committed_as` percpu counter via `vm_acct_memory()`.
The caller must call `vm_unacct_memory()` on every subsequent error path to
release the charge.

**Common wrappers** that internally call `security_vm_enough_memory_mm()`:
- `shmem_acct_size()` / `shmem_unacct_size()` in `mm/shmem.c` (shmem file setup)
- `shmem_acct_blocks()` / `shmem_unacct_blocks()` in `mm/shmem.c` (shmem page allocation)

**Where to check** (see callers of `security_vm_enough_memory_mm()` and
`vm_unacct_memory()` across `mm/mmap.c`, `mm/vma.c`, `mm/mprotect.c`,
`mm/mremap.c`, `mm/shmem.c`):
- Every error path after a successful `security_vm_enough_memory_mm()` or
  wrapper must call `vm_unacct_memory()` or the corresponding wrapper
- When adding a new check or error path between an accounting call and the
  code that consumes the reservation, verify the new path includes the undo
- Reordering checks so that side-effect-free validations precede accounting
  calls eliminates the need for cleanup on those paths

## Mempool Allocation Guarantees

Callers that assume `mempool_alloc()` always succeeds will NULL-deref if they
pass a flag without `__GFP_DIRECT_RECLAIM`. Conversely, NULL checks after a call
with `GFP_KERNEL` are dead code. Match the error handling to the flag.

`mempool_alloc()` cannot fail when `__GFP_DIRECT_RECLAIM` is set -- it retries
forever via the `repeat_alloc` loop after failing both the underlying allocator
and the pool reserve (see `mempool_alloc_noprof()` in `mm/mempool.c`).

**Cannot fail (retry forever):** GFP_KERNEL, GFP_NOIO, GFP_NOFS (all include
`__GFP_DIRECT_RECLAIM` via `__GFP_RECLAIM`)

**Can fail:** GFP_ATOMIC, GFP_NOWAIT (no `__GFP_DIRECT_RECLAIM`)

## Writeback Tags

Incorrect tag handling causes data loss (dirty pages skipped during sync) or
writeback livelock (sync never completes because new dirty pages keep appearing).
Review any code that starts writeback or implements `->writepages`.

Page cache tags defined as `PAGECACHE_TAG_*` in `include/linux/fs.h`:

| Tag | XA Mark | Purpose |
|-----|---------|---------|
| PAGECACHE_TAG_DIRTY | XA_MARK_0 | Folio has dirty data needing writeback |
| PAGECACHE_TAG_WRITEBACK | XA_MARK_1 | Folio is currently under IO |
| PAGECACHE_TAG_TOWRITE | XA_MARK_2 | Folio tagged for current writeback pass |

**Tag lifecycle:**
1. `folio_mark_dirty()` sets PAGECACHE_TAG_DIRTY
2. `tag_pages_for_writeback()` in `mm/page-writeback.c` copies DIRTY to TOWRITE
   for data-integrity syncs, preventing livelocks from new dirty pages
3. `folio_start_writeback()` (macro for `__folio_start_writeback(folio, false)`,
   defined in `include/linux/page-flags.h`):
   - Sets PAGECACHE_TAG_WRITEBACK
   - Clears PAGECACHE_TAG_DIRTY if the folio's dirty flag is not set
   - Clears PAGECACHE_TAG_TOWRITE (because `keep_write` is false)
4. To preserve PAGECACHE_TAG_TOWRITE, call `__folio_start_writeback(folio, true)`

**Tag selection** (see `wbc_to_tag()` in `include/linux/writeback.h`):
- `wbc_to_tag()` returns PAGECACHE_TAG_TOWRITE for `WB_SYNC_ALL` or
  `tagged_writepages` mode, PAGECACHE_TAG_DIRTY otherwise
- Data-integrity syncs (`WB_SYNC_ALL`) iterate TOWRITE so pages dirtied after
  the sync starts are not included

## Cgroup Writeback Domain Abstraction

Using `global_wb_domain` directly in code that receives a
`dirty_throttle_control *dtc` produces incorrect dirty throttling values when
the dtc represents a memcg domain. In the cgroup writeback path, dirty limits,
thresholds, and position ratios differ between the global and memcg domains;
hardcoding global values causes wrong backpressure calculations and misleading
tracepoint output.

`balance_dirty_pages()` in `mm/page-writeback.c` maintains two
`dirty_throttle_control` instances: `gdtc` (global, initialized with
`GDTC_INIT`) and `mdtc` (memcg, initialized with `MDTC_INIT`). Each carries
a `dom` field pointing to the appropriate `wb_domain`:

| dtc variant | `dom` field | Initialized by |
|-------------|-------------|----------------|
| `gdtc` | `&global_wb_domain` | `GDTC_INIT(wb)` |
| `mdtc` | `mem_cgroup_wb_domain(wb)` | `MDTC_INIT(wb, &gdtc_stor)` |

`balance_dirty_pages()` selects `sdtc = mdtc` when the memcg domain's
`pos_ratio` is lower (more constrained), then passes `sdtc` to subroutines
and trace events. Any code consuming a `dirty_throttle_control *dtc` must
use domain-polymorphic accessors:

- `dtc_dom(dtc)` to get the correct `wb_domain` (see `mm/page-writeback.c`)
- `hard_dirty_limit(dtc_dom(dtc), dtc->thresh)` for the domain-specific hard
  dirty limit
- `dtc->thresh`, `dtc->bg_thresh`, `dtc->dirty`, `dtc->limit` for
  domain-specific throttling values already computed for that dtc

**REPORT as bugs**: Code in functions or trace events that receives a
`dirty_throttle_control *dtc` but directly accesses `global_wb_domain` fields
(e.g., `global_wb_domain.dirty_limit`) for values that should be
domain-specific. The only legitimate direct uses of `global_wb_domain` are in
code that explicitly operates on the global domain (e.g., `global_dirty_limits()`
or the `global_dirty_state` trace event).

## Page Cache Batch Iteration: find_get_entries vs find_lock_entries

Callers that iterate page cache entries using `find_get_entries()` and handle
multi-order entries (large folio swap entries) must account for the fact that
the returned indices may not be the canonical base index of the entry. Getting
this wrong causes infinite retry loops in truncation paths.

**Key difference:**

| Function | Filters multi-order boundary crossings | `indices[i]` value |
|----------|----------------------------------------|--------------------|
| `find_lock_entries()` | Yes -- skips entries whose base is before `*start` or extends beyond `end` | `xas.xa_index` (may not be canonical base) |
| `find_get_entries()` | No -- returns all entries in range without filtering | `xas.xa_index` (may not be canonical base) |

**Why `indices[i]` may not be the canonical base:**

`find_get_entry()` calls `xas_find()` which calls `xas_load()` which calls
`xas_descend()`. When `xas_descend()` encounters a sibling entry, it follows
it to the canonical slot and updates `xas->xa_offset`, but does **not** update
`xas->xa_index` (see `xas_descend()` in `lib/xarray.c`). So after loading a
multi-order entry, `xas.xa_index` retains the original search position, not
the entry's aligned base.

Example: iterating from index 18 finds a multi-order entry at base 16
(order 3, 8 pages spanning [16, 23]):
- `xas_descend` resolves sibling at offset 18 to canonical offset 16
- `xas.xa_offset = 16` but `xas.xa_index` remains 18
- `indices[i] = 18`, not 16

**To compute the canonical base**, callers must do what `find_lock_entries()`
does:
```c
nr = 1 << xas_get_order(&xas);
base = xas.xa_index & ~(nr - 1);   /* or round_down(xas.xa_index, nr) */
```

## XArray Multi-Index Iteration with xas_next()

Iterating page cache entries with `xas_load()`/`xas_next()` over an xarray
containing large folios (multi-index entries) returns duplicate or sibling
entries for the same folio, because `xas_next()` increments by one slot at a
time. Callers that fail to advance past the remaining slots of a multi-index
entry will process the same folio multiple times.

**`xas_next()` vs `xas_find()` with multi-index entries:**

| Iterator | Skips siblings | Caller must advance |
|----------|---------------|---------------------|
| `xas_next()` | No -- visits every slot including siblings | Yes -- use `xas_advance(&xas, folio_next_index(folio) - 1)` after processing |
| `xas_find()` / `xas_find_marked()` | Yes -- skips `xa_is_sibling()` entries internally | No |

After successfully processing a multi-index entry (e.g., adding a folio to a
batch), call `xas_advance(&xas, folio_next_index(folio) - 1)` to reposition
the xarray state to the last slot of the current entry. The next `xas_next()`
call then advances to the first slot of the following entry. See
`filemap_get_read_batch()` and `filemap_get_folios_contig()` in `mm/filemap.c`
for the correct pattern. For order-0 folios the bug is invisible since each
entry occupies one slot.

## Page Cache Information Disclosure

Exposing page cache residency information without access control creates a
side channel that lets unprivileged processes infer other processes' file
access patterns. Any interface that reveals whether specific file pages are
cached, dirty, or under writeback must gate access behind a write-permission
check.

**Required access control** (see `can_do_mincore()` in `mm/mincore.c` and
`can_do_cachestat()` in `mm/filemap.c`):
- The calling process must have write access to the file (`f->f_mode &
  FMODE_WRITE`), or be the file owner (`inode_owner_or_capable()`), or
  pass a `file_permission(f, MAY_WRITE)` check
- This check was added to `mincore()` by commit 134fca9063ad to close a
  known side channel; `cachestat()` required the same fix later

**When to check**: review any new syscall, ioctl, or procfs/sysfs
interface that reports per-file or per-page cache state (resident, dirty,
writeback, evicted). The access control must be present even if the
interface uses a file descriptor rather than a virtual address range.

## kmemleak Tracking Symmetry

Freeing an object that was never registered with kmemleak causes a warning
"Trying to color unknown object ... as Black" when `CONFIG_DEBUG_KMEMLEAK` is
enabled. The kmemleak subsystem expects symmetric registration and
deregistration.

**When kmemleak registration is skipped:**

SLUB skips `kmemleak_alloc_recursive()` when `gfpflags_allow_spinning(flags)`
returns false (see `slab_post_alloc_hook()` in `mm/slub.c`).
`gfpflags_allow_spinning()` in `include/linux/gfp.h` checks
`!!(gfp_flags & __GFP_RECLAIM)`, i.e., whether at least one of
`__GFP_DIRECT_RECLAIM` or `__GFP_KSWAPD_RECLAIM` is set. Since `GFP_ATOMIC`
includes `__GFP_KSWAPD_RECLAIM`, kmemleak IS called for `GFP_ATOMIC`
allocations. The only standard API that skips kmemleak is `kmalloc_nolock()`,
which passes flags without any reclaim bits.

**Symmetric API requirement:**

| Allocation | Free | Tracking |
|------------|------|----------|
| `kmalloc(GFP_KERNEL)` | `kfree()`, `kfree_rcu()` | Symmetric (both tracked) |
| `kmalloc_nolock()` | `kfree_nolock()` | Symmetric (both skip tracking) |

`kfree_nolock()` deliberately skips `kmemleak_free_recursive()` (see
`kfree_nolock()` in `mm/slub.c`). Conversely, `kfree_rcu()` defers freeing
via `kvfree_call_rcu()` in `mm/slab_common.c`, which calls `kmemleak_ignore()`
to mark the object as not-a-leak before the grace period. If the object was
never registered, `kmemleak_ignore()` triggers the "unknown object" warning
via `paint_ptr()` in `mm/kmemleak.c`.

**All kmemleak state-change APIs require prior registration:**

`kmemleak_not_leak()`, `kmemleak_ignore()`, and `kmemleak_no_scan()` all
look up the object internally via `paint_ptr()` / `make_gray_object()` in
`mm/kmemleak.c` and warn ("Trying to color unknown object") if the object
was never registered. When an allocation path conditionally skips kmemleak
registration (e.g., `!gfpflags_allow_spinning()`), all subsequent kmemleak
state-change calls on that object must be guarded by the same condition.

**REPORT as bugs**: Code that allocates with `kmalloc_nolock()` but frees with
`kfree()` or `kfree_rcu()`, as this creates a kmemleak tracking imbalance.
The reverse (allocating with `kmalloc()` and freeing with `kfree_nolock()`)
also skips kmemleak deregistration, causing false leak reports. Also report
unconditional `kmemleak_not_leak()` / `kmemleak_ignore()` calls on objects
that may have been allocated without kmemleak registration.

## Swap Cache Residency

Accessing swap cache state without understanding the folio lifecycle during
swapin causes double-free (removing a folio from swap cache while IO is still
pending), data corruption (mapping a folio whose swap entry has been reused),
or missed reclaim (failing to free swap space for reclaimable folios).

A folio enters the swap cache via `add_to_swap()` during reclaim and remains
until explicitly removed. During swapin, `swap_cache_get_folio()` in
`mm/swap_state.c` checks the swap cache first; a hit avoids re-reading from
disk. After swapin completes, the folio stays in the swap cache as long as
swap-backed references exist.

**Swap cache removal conditions:**
- `folio_free_swap()` in `mm/swap_state.c` removes the folio only when
  `folio_swapcount(folio) == 0` AND `folio_ref_count(folio) == 1 + nr_pages`
  (only the caller and the swap cache hold references)
- The folio's swap entry is consumed when the last swap-backed PTE pointing
  to it is removed; `swap_free()` then decrements the swap count
- `__remove_mapping()` in `mm/vmscan.c` can remove swap cache folios during
  reclaim if the swap count is zero

**Large folio swapin conflicts:**
- Large folio swapin (mTHP) allocates a new large folio and attempts to
  insert it into the swap cache. If any subpage's swap entry is already
  occupied (by a small folio from a racing swapin), the insertion fails
- The swapin path must distinguish `xa_is_value()` entries (shadow/swap
  entries) from actual folio entries in the swap cache xarray
- `shmem_swapin_folio()` and `swap_cluster_readahead()` in `mm/swap_state.c`
  must handle these races gracefully by falling back to smaller order or
  retrying

**Swap entry reuse (ABA problem):**

Swap entries are recycled: once a swap entry's reference count drops to
zero, the swap allocator can reassign the same `swp_entry_t` value to a
completely different folio. This creates an ABA problem for lockless swap
cache lookups. For present PTEs, `pte_same()` validates folio identity
because the PFN uniquely identifies the physical page. For swap PTEs,
`pte_same()` only confirms the swap entry value has not changed -- the
entry can be freed and reused for a different folio between the lookup
and lock acquisition. After locking a folio obtained from
`filemap_get_folio()` on a swap address space, verify
`folio_test_swapcache(folio)` is still true and `folio->swap.val` still
matches the expected entry. After acquiring the PTE lock, if the earlier
lookup returned NULL, check `SWAP_HAS_CACHE` in
`si->swap_map[swp_offset(entry)]` to detect a folio that was added to
the swap cache after the lookup. See `move_swap_pte()` in
`mm/userfaultfd.c` for both revalidation patterns.

## Swap Device Lifetime

Accessing a `swap_info_struct` without a reference allows `swapoff` to free it
concurrently, causing use-after-free. `swapoff()` calls `percpu_ref_kill()` on
`si->users` followed by `synchronize_rcu()` before freeing structures.

- `get_swap_device(entry)` in `mm/swapfile.c` validates the entry and takes a
  `percpu_ref` on `si->users`. Returns NULL if the device is being swapped off.
  Must be paired with `put_swap_device(si)` (in `include/linux/swap.h`)
- `__swap_entry_to_info(entry)` in `mm/swap.h` returns the `swap_info_struct`
  pointer WITHOUT taking a reference -- only safe when the caller already holds
  a reference or is inside an RCU read-side section
- `__read_swap_cache_async()` in `mm/swap_state.c` uses
  `__swap_entry_to_info()` internally without pinning the device. All callers
  must hold a device reference for the entry being read
- **Cross-device readahead hazard**: readahead code that iterates page table
  entries (VMA readahead) may encounter swap entries from different devices than
  the target. The caller typically holds a device reference only for the target
  entry's device. Each entry from a different device must be separately pinned
  with `get_swap_device()` or skipped on failure (see `swap_vma_readahead()` in
  `mm/swap_state.c`)

## Memory Failure Folio Handling

Incorrect hwpoison handling causes kernel crashes (dereferencing freed
folios), silent data corruption (failing to isolate a poisoned page), or
accounting bugs (double-counting or under-counting hardware errors).

**`memory_failure()` return value contract** (see `memory_failure()` in
`mm/memory-failure.c`):

| Return | Meaning | `kill_me_maybe()` action (x86 MCE) |
|--------|---------|-------------------------------------|
| `0` | Page successfully recovered (offlined, truncated, or dropped) | `set_mce_nospec()` + `sync_core()`, no signal |
| `-EHWPOISON` | Page already poisoned; SIGBUS already sent if `MF_ACTION_REQUIRED` | No further action |
| `-EOPNOTSUPP` | `hwpoison_filter()` filtered the event | No further action |
| Other negative | Recovery failed | "Memory error not recovered", kill process |

Architecture MCE handlers like `kill_me_maybe()` in
`arch/x86/kernel/cpu/mce/core.c` branch on these specific values. Any
unrecognized negative return falls through to "Memory error not recovered"
followed by process termination. When modifying internal helpers whose
return value propagates through `memory_failure()`, verify that "page was
successfully recovered without needing a signal" returns `0`, not a
negative error code like `-EFAULT`.

**Large folio hwpoison specifics:**
- `PG_hwpoison` is set per-page (`PF_ANY`), but `PG_has_hwpoisoned` is
  set on the first tail page (`PF_SECOND`) as a folio-level indicator
- `folio_test_has_hwpoisoned()` is a fast check that avoids scanning all
  subpages; it MUST be set whenever any subpage has `PG_hwpoison`
- When splitting a poisoned large folio, `PG_has_hwpoisoned` must be
  propagated to the correct sub-folio (see `__split_huge_page()` in
  `mm/huge_memory.c`)
- Code handling memory failure for large folios must not assume the folio
  order at entry. The folio may be split concurrently; always re-check
  `folio_test_large()` after acquiring the folio lock

**HWPoison content access guard:**

Accessing the content of a hardware-poisoned page from kernel context triggers
a Machine Check Exception (MCE) that is not recoverable in-kernel, causing a
kernel panic. Any code path that reads or writes page data must check
`PageHWPoison()` before accessing the content.

- `PageHWPoison(page)`: per-page check; use when iterating individual subpages
  and skipping only the poisoned ones (e.g., `try_to_map_unused_to_zeropage()`
  in `mm/migrate.c` skips the poisoned subpage but continues scanning others)
- `folio_contain_hwpoisoned_page(folio)`: folio-level early-exit; use when any
  poisoned subpage makes the entire operation unsafe (e.g., `thp_underused()`
  in `mm/huge_memory.c` bails out because scanning subpage content is not safe)
- Content-accessing functions that need guards include `pages_identical()`,
  `memcmp_pages()`, `memchr_inv()` on mapped page data, `copy_page()`, and
  any `kmap_local_page()` followed by a read
- **REPORT as bugs**: code that reads page content in THP split, migration,
  KSM, or compaction paths without first checking `PageHWPoison()` on pages
  that could have been marked poisoned by a concurrent `memory_failure()` call

## Non-Folio Compound Pages

Treating a driver-allocated compound page as a folio causes crashes, data
corruption, or undefined behavior. `page_folio()` blindly casts the compound
head page to `struct folio *` without verifying that the page was set up as a
folio by the MM subsystem. Code that calls folio operations (`folio_lock()`,
`split_huge_page()`, `min_order_for_split()`) or accesses folio-specific
fields (`folio->mapping` for `mapping_min_folio_order()`) on such a page
operates on uninitialized or stale data.

**How non-folio compound pages appear:**
- Drivers call `vm_insert_page()`, `vm_insert_pages()`, or
  `vmf_insert_page_mkwrite()` (see `mm/memory.c`) with pages from
  `alloc_pages(GFP_*, order)` where order > 0
- These pages have `PG_head` set (via `prep_compound_page()` in
  `mm/page_alloc.c`), so `folio_test_large()` returns true, but they are
  not on the LRU and their `mapping` field is not set up for folio operations

**Why `page_folio()` does not catch this:** `page_folio()` follows the
`compound_head` pointer and casts to `struct folio *`. The cast always succeeds
because `struct folio` overlays `struct page` in memory. There is no runtime
check that the page is a valid folio.

**Validation gate pattern:** Functions like `HWPoisonHandlable()` in
`mm/memory-failure.c` and `PageLRU()` checks serve as validation gates that
reject pages not managed by the MM folio infrastructure. When code paths bypass
these gates (e.g., via early-return optimizations or flag-based conditional
skips), non-folio compound pages can reach folio operations unchecked.

**Review guidance:**
- When a code path calls `page_folio()` on a page from a driver mapping, verify
  that a validation gate (e.g., `HWPoisonHandlable()`, `PageLRU()`,
  `folio_test_anon()` with null-mapping checks) has rejected non-folio pages
- `folio_test_large()` returning true does NOT guarantee the page is a valid
  folio -- it only checks `PageHead`, which is set for any compound page

## Memcg Charge Lifecycle

Missing or asymmetric memcg charge/uncharge operations corrupt per-cgroup
memory counters, causing containers to exceed their memory limits (under-
charging) or to be unable to allocate despite having free quota (over-
charging that is never unwound).

**Charge-uncharge symmetry:**
- Every `mem_cgroup_charge()` (or implicit charge via `__mem_cgroup_charge()`
  in `mm/memcontrol.c`) must have a corresponding `mem_cgroup_uncharge()`
  on the freeing path. The charge is associated with the folio via
  `folio->memcg_data`
- `folio_unqueue_deferred_split()` must be called before uncharging to avoid
  accessing freed memcg data (see `folio_unqueue_deferred_split()` in
  `mm/huge_memory.c`)
- On migration, the charge is transferred via `mem_cgroup_migrate()` in
  `mm/memcontrol.c`; the old folio is NOT uncharged separately

**Memcg lookup safety:**
- `folio_memcg(folio)` returns the folio's charged memcg; returns NULL for
  uncharged folios
- `css_tryget_online()` on a memcg can fail if the cgroup is being removed.
  Callers must handle the failure case -- typically by falling back to the
  root memcg or skipping the operation
- After a memcg is offlined, folios charged to it retain their
  `folio->memcg_data` pointer. The memcg is not freed until all charges
  are drained (reparented). Code must not assume `folio_memcg()` returns
  an online memcg. Operations that charge, record, or track a memcg
  identity (e.g., swap cgroup recording, counter updates) must use the
  resolved online ancestor from `mem_cgroup_id_get_online()` consistently
  across the entire charge/record/uncharge cycle. Refactorings that
  "simplify" an explicit memcg parameter into an internal `folio_memcg()`
  call introduce a mismatch: the counter targets the resolved (online
  ancestor) memcg, but the recorded ID comes from the original (possibly
  offline) memcg. The uncharge path then decrements the wrong memcg,
  causing a permanent counter leak. This only manifests when cgroups are
  deleted under memory pressure
- `mem_cgroup_from_id()` returns a bare RCU-protected pointer without
  taking a reference -- the pointer is only valid while `rcu_read_lock()`
  is held. To use the memcg outside RCU, call `mem_cgroup_tryget(memcg)`
  before `rcu_read_unlock()`, then `mem_cgroup_put()` when done. Functions
  prefixed `get_mem_cgroup_from_*()` (e.g., `get_mem_cgroup_from_mm()`,
  `get_mem_cgroup_from_folio()`) acquire a reference internally and return
  a pointer safe to use after RCU unlock

**Per-CPU stock drain:**
- Memcg charges are batched in per-CPU stocks for performance. When
  destroying a memcg, all per-CPU stocks must be drained to ensure
  accurate final accounting (see `drain_all_stock()` in `mm/memcontrol.c`)
- Missing stock drain causes the memcg to appear to have outstanding
  charges after all folios have been uncharged, preventing cgroup deletion

## Dual Reclaim Paths: Classic LRU vs MGLRU

The page reclaim subsystem in `mm/vmscan.c` has two parallel
implementations that must maintain the same vmstat accounting, memcg event
counting, and tracepoint coverage. Changes to one path that are not
mirrored in the other cause silent stat drift, missing memcg counters, or
broken tracing when the other reclaim algorithm is active. MGLRU is
runtime-selectable (`/sys/kernel/mm/lru_gen/enabled`), so bugs may go
unnoticed in testing.

**Classic LRU path:**
- `shrink_inactive_list()` -- isolates and reclaims inactive folios
- `shrink_active_list()` -- ages and deactivates active folios

**MGLRU path** (enabled via `CONFIG_LRU_GEN`, active when
`lru_gen_enabled()` returns true):
- `evict_folios()` -- isolates and reclaims folios (mirrors
  `shrink_inactive_list()`)
- `scan_folios()` -- scans and sorts folios by generation

Both paths call `shrink_folio_list()` for the actual folio reclaim, but
each path has its own post-reclaim stat updates using `struct reclaim_stat`
fields (e.g., `stat.nr_demoted`), `mod_lruvec_state()` /
`__count_vm_events()` / `count_memcg_events()` calls, and tracepoints.

**When reviewing patches that modify vmstat counters, memcg event
accounting, or tracepoints in either `shrink_inactive_list()` or
`evict_folios()`**, verify that the corresponding change is also made in
the other function. The same applies to `shrink_active_list()` vs
`scan_folios()` for scanning-phase stats.

## Large Folio i_size Boundary Checks

Mapping file-backed large folios without checking `i_size` breaks POSIX
SIGBUS semantics: accesses within a VMA but beyond `i_size` rounded up to
`PAGE_SIZE` must generate SIGBUS, but over-mapping a large folio silently
serves zero-filled pages for those accesses instead. This is a persistent
source of bugs because folios in the page cache may be much larger than the
file's actual size (e.g., a PMD-sized folio for a small file with
`huge=always` tmpfs, or a large folio from readahead for a file that was
subsequently truncated).

**Invariants:**
- PTEs must not be installed for file pages beyond
  `DIV_ROUND_UP(i_size_read(mapping->host), PAGE_SIZE)`. Code that
  computes the number of PTEs to install from `folio_nr_pages()` or
  `folio_next_index()` must clamp against `i_size`. See
  `filemap_map_pages()` in `mm/filemap.c` which clamps `end_pgoff` to
  `file_end`
- PMD mappings must not be installed when the folio extends past
  `i_size`. Both `filemap_map_pages()` in `mm/filemap.c` and
  `finish_fault()` in `mm/memory.c` check
  `file_end >= folio_next_index(folio)` before allowing PMD mapping via
  `filemap_map_pmd()` or `do_set_pmd()`
- `filemap_map_folio_range()` in `mm/filemap.c` must not expand a
  partial folio mapping to the full folio size when the folio extends
  beyond `i_size`. The "map the large folio fully" optimization is gated
  on `file_end >= folio_next_index(folio)`
- On truncate, if a large folio spanning the new `i_size` cannot be
  split, the folio must be fully unmapped so it will be refaulted with
  PTEs (which respect `i_size` clamping). See `try_folio_split_or_unmap()`
  in `mm/truncate.c`, which calls `try_to_unmap()` on split failure

**Exception -- shmem/tmpfs**: `shmem_mapping()` returns true for
shmem/tmpfs address spaces. These mappings are exempt from the `i_size`
boundary check for PMD mapping and are allowed to map with PMDs across
`i_size`. All three enforcement sites (`filemap_map_pages()`,
`finish_fault()`, and `try_folio_split_or_unmap()`) check
`shmem_mapping()` to preserve this behavior.

**Common mistake**: fault-around and finish-fault code paths that expand
PTE installation to cover the full large folio (for batching efficiency)
without clamping against `i_size`. The folio is valid in the page cache,
so no allocation or lookup failure signals the error -- the bug is purely
that PTEs are installed for pages that should not be accessible.

## Shmem Folio Cache Residency

Confusing `folio_test_swapbacked()` with `folio_test_swapcache()` causes
xarray corruption, incorrect VM statistics accounting, and wrong
branching in migration and reclaim paths, because shmem folios can be in
two different cache states that require different handling.

**The three folio cache states for shmem:**

| State | `swapbacked` | `swapcache` | `folio->mapping` | xarray location |
|-------|-------------|-------------|-------------------|-----------------|
| Shmem in page cache | true | false | shmem inode `address_space` | `mapping->i_pages` (single multi-order entry) |
| Shmem in swap cache | true | true | NULL | swap address space (N individual entries) |
| Anonymous in swap cache | true | true | NULL (anon) | swap address space (N individual entries) |

A shmem folio is in either the page cache or the swap cache, never both
simultaneously. Once moved to swap cache, `folio->mapping` is set to
NULL and the folio is no longer associated with the shmem inode mapping.

**`folio_test_swapbacked()` vs `folio_test_swapcache()`:**
- `folio_test_swapbacked()` tests `PG_swapbacked`: true for all anonymous
  and shmem folios (both page-cache-resident and swap-cache-resident).
  It indicates the folio *can use* swap as backing storage
- `folio_test_swapcache()` tests both `PG_swapbacked` AND `PG_swapcache`:
  true only when the folio is *currently in* the swap cache
- Using `folio_test_swapbacked()` as a proxy for "is in swap cache" is
  wrong because it also matches shmem folios that are in the page cache

**Xarray storage models:**
- **Page cache** (`mapping->i_pages`): stores a single multi-order xarray
  entry for a large folio. Operations use `xas_store()` once
- **Swap cache**: stores N individual entries, one per subpage of the
  folio. Operations must iterate all N slots

Code that branches on cache type to choose between single-entry and
multi-entry xarray operations must use `folio_test_swapcache()`, not
`folio_test_swapbacked()`. See `__folio_migrate_mapping()` in
`mm/migrate.c` which uses `folio_test_swapcache()` to select the
swap-cache-specific replacement path (`__swap_cache_replace_folio()`).

## VMA Anonymous vs File-backed Classification

Using `vma->vm_file` to determine whether a VMA is file-backed causes
incorrect dispatch for VMAs that have a `vm_file` but are treated as
anonymous (e.g., private mappings of `/dev/zero`). This leads to BUG_ON
crashes, unaligned page offsets, or wrong code paths being taken.

**How VMA classification works** (see `include/linux/mm.h`):
- `vma_is_anonymous(vma)` returns `!vma->vm_ops` -- this is the canonical
  test for anonymous VMAs
- `vma_set_anonymous(vma)` sets `vma->vm_ops = NULL` but does NOT clear
  `vma->vm_file`
- A VMA can have `vma->vm_file != NULL` AND be anonymous (`vm_ops == NULL`)

**VMAs where `vm_file` is set but the VMA is anonymous:**
- Private mappings of `/dev/zero`: `mmap_zero_private_success()` in
  `drivers/char/mem.c` calls `vma_set_anonymous(vma)` for private mappings,
  leaving `vm_file` pointing to the `/dev/zero` file. Shared mappings take
  a different path via `shmem_zero_setup()` which sets
  `vm_ops = &shmem_anon_vm_ops`
- Any driver `mmap` handler that calls `vma_set_anonymous()` after the VMA
  is created with a file reference

**Correct usage:**
- To test "is this VMA file-backed?": use `!vma_is_anonymous(vma)`, NOT
  `vma->vm_file != NULL`
- To test "is this VMA anonymous?": use `vma_is_anonymous(vma)`, NOT
  `vma->vm_file == NULL`
- To access the backing file of a file-backed VMA: check
  `!vma_is_anonymous(vma)` first, then use `vma->vm_file`

**REPORT as bugs**: Code that uses `vma->vm_file` (or `!vma->vm_file`) as
a proxy for file-backed (or anonymous) VMA classification in dispatch logic,
conditionals, or assertions. The correct test is `vma_is_anonymous()`.

## VMA Split/Merge Critical Section

Page table structural changes performed outside the `vma_prepare()`/
`vma_complete()` critical section race with concurrent page faults (via VMA
lock) and rmap walks (via file/anon rmap locks). The result is use-after-free,
page table corruption, or re-establishment of state that was just torn down.

The three VMA-modifying paths -- `__split_vma()`, `commit_merge()`, and
`vma_shrink()` in `mm/vma.c` -- all follow this sequence:

1. `vm_ops->may_split()` (validation only, no side effects)
2. `vma_start_write()` (acquire per-VMA lock)
3. `vma_prepare()` (acquire file rmap `i_mmap_lock_write` and anon_vma lock)
4. Page table structural changes: `vma_adjust_trans_huge()`, `hugetlb_split()`
5. VMA range update (`vm_start`/`vm_end`/`vm_pgoff`)
6. `vma_complete()` (release locks acquired in step 3)

**Rules:**
- `vm_ops->may_split()` must only validate whether the split is permitted
  (e.g., alignment checks). It must not modify page tables or other shared
  state, because it runs before the VMA and rmap locks are acquired
- Any page table unsharing, splitting, or teardown required by a VMA split
  must happen between `vma_prepare()` and `vma_complete()`, where the VMA
  write lock and file/anon rmap write locks prevent concurrent page table
  walks (except hardware walks and `gup_fast()`)
- When calling helpers that normally acquire their own locks (e.g.,
  `hugetlb_unshare_pmds()`), use a `take_locks=false` path and assert
  that the needed locks are already held (see `hugetlb_split()` in
  `mm/hugetlb.c`)

## Zone Watermarks and lowmem_reserve

The `lowmem_reserve[]` array in `struct zone` protects lower zones from
being over-consumed by allocations targeting higher zones. Its indexing
direction is counter-intuitive and a persistent source of bugs.

**How `lowmem_reserve` works** (see `setup_per_zone_lowmem_reserve()` in
`mm/page_alloc.c`):
- `zone[i].lowmem_reserve[j]` contains the number of pages that zone `i`
  reserves against allocations whose preferred zone is zone `j`. The value
  protects zone `i`, not zone `j`
- Values are cumulative and monotonically non-decreasing:
  `lowmem_reserve[ZONE_NORMAL] <= lowmem_reserve[ZONE_MOVABLE]`
- A zone's own entry is always 0: `zone[i].lowmem_reserve[i] == 0`
- The reservation is computed as `managed_pages / sysctl_lowmem_reserve_ratio[i]`
  summed cumulatively from higher zones downward

**How it affects watermark checks** (see `__zone_watermark_ok()` in
`mm/page_alloc.c`):
- The effective watermark for zone `i` when the allocation targets zone `j`
  is: `watermark[wmark] + lowmem_reserve[j]`
- This means lower zones (e.g., ZONE_DMA) are harder to allocate from when
  the request targets a higher zone (e.g., ZONE_NORMAL), because the
  reserved amount is larger

**REPORT as bugs**: Code that indexes `lowmem_reserve` with the zone's own
index (always returns 0, disabling the protection), or that assumes
`lowmem_reserve[j]` protects zone `j` rather than the zone whose array
is being read.

**Per-CPU vmstat counter drift:**

`zone_page_state()` in `include/linux/vmstat.h` returns a cached value that
omits pending per-CPU deltas. On systems with many CPUs, the cumulative
error (`num_online_cpus() * threshold`) can exceed the gap between watermark
levels, causing watermark checks to produce wrong answers (e.g., kswapd
stops reclaiming because the zone appears balanced when it is actually below
the min watermark). When `zone->percpu_drift_mark` is set (by
`refresh_zone_stat_thresholds()` in `mm/vmstat.c`) and the cached value is
below it, code must fall back to `zone_page_state_snapshot()`, which sums
all per-CPU deltas for an accurate count. This bug pattern occurs when
refactoring replaces a higher-level watermark API (which encapsulates the
drift check) with direct `zone_page_state()` + `__zone_watermark_ok()`
calls, silently dropping the safety check. See `should_reclaim_retry()`,
`allow_direct_reclaim()`, and `pgdat_balanced()` in `mm/vmscan.c` for the
correct pattern.

## Layered vmstat Accounting (Node vs Memcg)

Stat updates recorded via `lruvec_stat_mod_folio()` or `mod_lruvec_page_state()`
are conditional on the folio's memcg association at call time. When
`folio_memcg(folio)` returns NULL, these functions fall back to
`mod_node_page_state()`, updating only the node-level counter (see
`lruvec_stat_mod_folio()` in `mm/memcontrol.c`). When a memcg is present,
`mod_lruvec_state()` updates both the node counter and the memcg/lruvec counter.
This means the same function call updates different accounting layers depending
on when it is called relative to memcg association.

**Stat reconciliation on deferred memcg charging:** when a folio is allocated
without a memcg (e.g., large kmalloc in softirq context) and stats are recorded
at allocation time, only the node-level counter is incremented. If the folio is
later charged to a memcg (e.g., via `kmem_cache_charge()` in `mm/slub.c`), the
post-charge path must also add the memcg-level stat that was missed. Otherwise
the free path -- which calls `lruvec_stat_mod_folio()` with the memcg now
present -- will decrement both node and memcg counters, causing the memcg
counter to underflow.

The correct pattern subtracts from the global-only counter and re-adds via the
lruvec interface that updates both levels:
```c
// CORRECT: reconcile stats when associating a folio with a memcg after allocation
size = folio_size(folio);
mod_node_page_state(folio_pgdat(folio), NR_SLAB_UNRECLAIMABLE_B, -size);
mod_lruvec_page_state(page, NR_SLAB_UNRECLAIMABLE_B, size);
```

**Key API distinction:**

| Function | Updates node | Updates memcg | Condition |
|----------|-------------|---------------|-----------|
| `mod_node_page_state()` | Yes | No | Always global-only |
| `lruvec_stat_mod_folio()` / `mod_lruvec_page_state()` | Yes | **Only if folio has memcg** | Checks `folio_memcg()` at call time |
| `mod_lruvec_state()` | Yes | Yes | Always both (caller provides lruvec) |

Review any code path that changes a folio's memcg association after allocation
(post-charging, migration, reparenting) for stat counters that were recorded
before the association existed.

## Frozen vs Refcounted Page Allocation

Returning a page with the wrong refcount state causes refcount-underflow
BUG_ON on the first `put_page()`, use-after-free if the page is reclaimed
while the caller still holds a pointer, or silent memory corruption from
operations that assume a nonzero refcount. This contract is enforced by
`set_page_refcounted()` which calls `VM_BUG_ON_PAGE(page_ref_count(page),
page)` -- it catches double-init but not missing init.

`get_page_from_freelist()` in `mm/page_alloc.c` returns pages with
refcount 0 ("frozen" pages). Callers that need normal refcounted pages
must call `set_page_refcounted()` (defined in `mm/internal.h`) after a
successful allocation. The kernel provides two API tiers built on this:

| API tier | Returns | `set_page_refcounted()` | Use case |
|----------|---------|-------------------------|----------|
| `__alloc_frozen_pages_noprof()` | Frozen (refcount 0) | Caller must NOT call it | Callers that manage refcount themselves (e.g., compaction, bulk allocation) |
| `__alloc_pages_noprof()` | Refcounted (refcount 1) | Called internally | Normal page allocation; wraps frozen variant + `set_page_refcounted()` |
| `alloc_frozen_pages_nolock_noprof()` | Frozen (refcount 0) | Caller must NOT call it | Lock-free allocation for special contexts (BPF, tracing) |
| `alloc_pages_nolock_noprof()` | Refcounted (refcount 1) | Called internally | Lock-free wrapper; wraps frozen variant + `set_page_refcounted()` |

**REPORT as bugs**: Any direct caller of `get_page_from_freelist()` or
the `_frozen_` allocation functions that passes the page to code expecting
a normal refcounted page without calling `set_page_refcounted()`.
Conversely, calling `set_page_refcounted()` on a page intended to stay
frozen (refcount 0) is also a bug.

## MGLRU Generation and Tier Bit Consistency

Stale tier bits carried into a new generation cause incorrect aging
decisions: `folio_lru_refs()` in `include/linux/mm_inline.h` reads
`LRU_REFS_MASK` and `PG_referenced` to determine how many times a folio
was accessed through file descriptors, and `folio_update_gen()` in
`mm/vmscan.c` uses `PG_referenced` and `PG_workingset` to decide whether
to promote a folio. If these bits are not cleared when a folio moves to a
new generation, the tier state from the old generation inflates the
access count in the new generation, distorting eviction decisions.

**Generation bits** (`LRU_GEN_MASK` in `include/linux/mmzone.h`):
- Encode which generation a folio belongs to, stored in `folio->flags`
- Set by `lru_gen_add_folio()` in `include/linux/mm_inline.h`,
  `folio_update_gen()` and `folio_inc_gen()` in `mm/vmscan.c`

**Tier bits** (`LRU_REFS_FLAGS` in `include/linux/mmzone.h`):
- `LRU_REFS_MASK`: counter bits incremented by `lru_gen_inc_refs()` in
  `mm/swap.c` to track repeated file descriptor accesses
- `PG_referenced`: first-access marker; set before the counter bits
- `PG_workingset`: set when all counter bits are saturated, indicating a
  hot folio; also used for PSI accounting on workingset refault

**Invariant**: when a folio moves to a new generation, its tier bits
(`LRU_REFS_FLAGS`) must be cleared so that tier tracking starts fresh.
All code paths that change the generation bits must also clear the tier
bits:
- `folio_update_gen()`: clears `LRU_REFS_FLAGS` via
  `new_flags = old_flags & ~(LRU_GEN_MASK | LRU_REFS_FLAGS)`
- `folio_inc_gen()`: clears `LRU_REFS_FLAGS` via the same mask pattern
- `lru_gen_add_folio()`: must clear tier bits when activating a folio
  (indicated by `folio_test_active()`); does not clear `PG_workingset`
  when activation is due to workingset refault to preserve PSI accounting
- `lru_gen_clear_refs()` in `mm/swap.c`: clears `LRU_REFS_FLAGS` and
  `PG_workingset` when "deactivating" a folio

**Review any code that modifies `LRU_GEN_MASK` bits in `folio->flags`**
to verify it also handles `LRU_REFS_FLAGS`. A new code path that sets
generation bits without clearing tier bits will silently produce
incorrect aging behavior that is difficult to detect in testing.

## Folio Lock Strategy After GUP

Using `folio_trylock()` in code paths that have already committed to a specific
folio (e.g., after GUP) exposes transient lock contention as a hard error to
callers, causing spurious failures. Similarly, returning an error instead of
retrying when page table re-validation fails after GUP propagates expected
races (migration, swapout, compaction) as permanent errors.

**The GUP + lock + re-validate pattern:**

Many MM operations follow a sequence: (1) GUP to pin a page and obtain a folio,
(2) acquire the folio lock, (3) re-validate page table state (e.g., via
`folio_walk_start()` in `mm/pagewalk.c`) to confirm the mapping is still as
expected. Between steps 1 and 2, concurrent migration, swapout, compaction, or
THP splitting can temporarily lock the folio or change the page table. These
are expected races, not permanent errors.

**Folio lock API hierarchy** (see `include/linux/pagemap.h`):
- `folio_trylock(folio)`: non-blocking, returns false on contention. Appropriate
  for best-effort paths that can skip the folio (e.g., LRU scanning in
  `shrink_folio_list()`, compaction in `isolate_migratepages_block()`)
- `folio_lock(folio)`: blocks unconditionally until the lock is acquired.
  Appropriate when the caller must operate on this folio and cannot fail
- `folio_lock_killable(folio)`: blocks until the lock is acquired or a fatal
  signal is received (returns `-EINTR`). Appropriate for user-context paths
  that have committed to a specific folio but should be interruptible

**Rules:**
- After GUP pins a specific folio that the caller must operate on, use
  `folio_lock()` or `folio_lock_killable()`, not `folio_trylock()`. Returning
  `-EBUSY` from `folio_trylock()` failure forces callers to implement retry
  logic they may omit
- When page table re-validation fails after GUP (e.g., `folio_walk_start()`
  returns a different folio or NULL), retry the GUP from scratch rather than
  returning an error. The page table change is a transient race, and the
  original page is still pinned (release it before retrying)
- `folio_trylock()` is correct in scan/iteration paths where the code processes
  many folios and can simply skip one that is locked (see `folio_referenced()`
  in `mm/rmap.c`, `madvise_free_pte_range()` in `mm/madvise.c`)

## Large Folio Split Refcount Precondition

Calling `split_folio()` on a large folio while extra references are held
causes it to return -EAGAIN, and if the caller retries in a loop, this
creates a livelock that only manifests under contention from multiple tasks
operating on the same folio.

`split_folio()` calls `__folio_split()` in `mm/huge_memory.c`, which checks
`folio_expected_ref_count(folio) != folio_ref_count(folio) - 1`. The expected
count is computed by `folio_expected_ref_count()` in `include/linux/mm.h`,
summing references from mapcount, page cache, swap cache, and `PG_private`.
The `- 1` accounts for the single caller pin. Any additional `folio_get()`
references -- such as those held by other tasks blocked on `folio_lock()` --
cause this check to fail.

**Dangerous ordering (refcount before lock):**
```c
// WRONG: raises refcount, then blocks on lock; other tasks doing
// the same inflate the refcount, causing split_folio() to fail
folio_get(folio);
folio_lock(folio);          // blocks while holding extra ref
err = split_folio(folio);   // fails: refcount too high
```

**Safe ordering (lock before refcount):**
```c
// CORRECT: lock first so only one task proceeds; then raise refcount
if (!folio_trylock(folio))
    return -EAGAIN;         // no refcount raised, no livelock
folio_get(folio);
err = split_folio(folio);   // expected refcount matches
```

See `madvise_free_huge_pmd()` in `mm/huge_memory.c` for the correct
lock-before-refcount pattern when splitting is needed.

**REPORT as bugs**: Code paths that call `folio_get()` then block on
`folio_lock()` before calling `split_folio()` on large folios, especially
in retry loops.

## Large Folio Swapin and Swap Cache Conflicts

Attempting to swap in a large folio (mTHP) without checking for existing
smaller folios in the swap cache causes unbounded retry loops (softlockup).
`swapcache_prepare()` in `mm/swapfile.c` fails with `-EEXIST` when any swap
slot in the range already has `SWAP_HAS_CACHE` set (checked via
`__swap_duplicate()`), and callers that unconditionally retry on `-EEXIST`
loop forever because the conflicting entry persists.

**Required pre-check for large folio swapin:**
- Before attempting mTHP swapin, callers must verify that no swap slot in
  the target range is already occupied in the swap cache. Use
  `non_swapcache_batch(entry, nr_pages)` in `mm/swap.h`, which checks
  `SWAP_HAS_CACHE` in `si->swap_map[]` for each slot. If the result is less
  than `nr_pages`, fall back to order-0 swapin
- The anon path does this in `can_swapin_thp()` in `mm/memory.c`; the shmem
  path does this in `shmem_swap_alloc_folio()` in `mm/shmem.c`. Any new
  large folio swapin path must include the same check

**How swap cache conflicts arise:**
- Swap readahead (`shmem_swapin_cluster()`, `swap_cluster_readahead()`) may
  bring in individual order-0 folios into the swap cache for slots that are
  part of a larger swap entry in the shmem mapping
- Concurrent swapin from another thread may populate individual swap cache
  entries while the current thread attempts a large swapin

## Page Table Walker Callbacks

A `pmd_entry` callback in `struct mm_walk_ops` (see `include/linux/pagewalk.h`)
that fails to handle transparent huge page PMDs causes silent data skipping,
incorrect page references, or kernel crashes from dereferencing a huge-page
PFN as a page table pointer.

The `walk_page_range()` family in `mm/pagewalk.c` walks page tables and
invokes caller-provided callbacks at each level.

**`pmd_entry` must handle THP:**
- The walker's `walk_pmd_range()` calls `ops->pmd_entry()` for every
  non-empty PMD, including `pmd_trans_huge()` PMDs. The `mm_walk_ops`
  documentation states: "this handler is required to be able to handle
  pmd_trans_huge() pmds"
- When `pmd_entry` is defined but `pte_entry` is not, the walker does NOT
  descend to PTE level at all. The `pmd_entry` callback must perform its
  own PTE-level walking internally (using `pte_offset_map_lock()` and
  iterating PTEs) if it needs to examine individual pages

**Callback return values** control walker flow:
- `0`: continue walking to the next entry
- `> 0`: stop walking immediately and return this value to the caller
- `< 0`: abort with error, return this value to the caller

**`walk_lock`** in `mm_walk_ops` specifies the locking requirement (see
`enum page_walk_lock` in `include/linux/pagewalk.h`):
- `PGWALK_RDLOCK`: caller holds `mmap_lock` for read
- `PGWALK_WRLOCK`: walker will write-lock each VMA during the walk
- `PGWALK_WRLOCK_VERIFY`: VMA is expected to be already write-locked
- `PGWALK_VMA_RDLOCK_VERIFY`: VMA is expected to be already read-locked

**Common patterns in `pmd_entry` callbacks:**
- Read the PMD locklessly first with `pmdp_get_lockless()`, then reread under
  `pmd_lock()` if it is a THP leaf
- `pte_offset_map_lock()` can return NULL and must be checked
- `folio_get()` must be called before releasing the PTL when the callback
  needs to return a folio reference to the caller

## Folio Reference Count Expectations

Operations that require exclusive folio access -- migration, THP collapse,
folio splitting -- fail when a folio has unexpected references. Using folio
flags (e.g., `folio_test_lru()`) as a proxy for "has extra references" is
unreliable because per-CPU batching mechanisms (LRU caches, mlock/munlock
batches in `mm/mlock.c`) hold transient `folio_get()` references that are
independent of page flags.

**`folio_expected_ref_count()`** (in `include/linux/mm.h`) calculates the
expected refcount from pagecache, swapcache, `PG_private`, and page table
mappings. Comparing `folio_ref_count(folio)` against
`folio_expected_ref_count(folio)` plus the caller's own reference detects
unexpected references from any source.

**Where transient batch references come from:**
- LRU pagevecs: `folio_add_lru()` in `mm/swap.c` defers LRU insertion via
  per-CPU `folio_batch` with an extra reference
- mlock batches: `mlock_folio()` in `mm/mlock.c` calls `folio_get()` before
  adding to per-CPU `mlock_fbatch` for deferred processing
- munlock batches: `munlock_folio()` in `mm/mlock.c` similarly defers via
  `folio_get()` and per-CPU batching

**Draining batches:**
- `lru_add_drain()` drains the current CPU's LRU and mlock/munlock batches
- `lru_add_drain_all()` drains all CPUs' batches (expensive, per-CPU workqueue)
- Code that detects unexpected references should drain batches and recheck
  before concluding the folio is not migratable (see
  `collect_longterm_unpinnable_folios()` in `mm/gup.c`)

**REPORT as bugs**: code that uses `folio_test_lru()` or other flag checks as
the sole heuristic for deciding whether to call `lru_add_drain_all()` before
migration or other exclusive-access operations, instead of comparing
`folio_ref_count()` against `folio_expected_ref_count()`.

## Hugetlb Fault Path Locking

Acquiring a pagecache folio lock while holding the `hugetlb_fault_mutex`
risks ABBA deadlock because `hugetlb_wp()` drops the mutex (and vma_lock)
mid-operation while the folio lock may still be held.

**Lock ordering** (see the "Lock ordering in mm" comment block at the top
of `mm/rmap.c`):
- `hugetlb_fault_mutex` -> `vma_lock` -> `mapping->i_mmap_rwsem` -> `folio_lock`

**Why `hugetlb_wp()` drops locks:**
- When `alloc_hugetlb_folio()` fails for a `cow_from_owner` case,
  `hugetlb_wp()` must call `unmap_ref_private()`, which takes the
  `vma_lock` in write mode. Since the caller holds `vma_lock` in read
  mode and the `hugetlb_fault_mutex`, both must be dropped first (see
  the lock drop in `hugetlb_wp()` in `mm/hugetlb.c`)

**Rules for folio locking in the hugetlb fault path:**
- Do NOT call `filemap_lock_folio()` or `filemap_lock_hugetlb_folio()` to
  look up pagecache folios while holding the `hugetlb_fault_mutex` in code
  paths that lead to `hugetlb_wp()`. The pagecache folio lock will be held
  across the mutex drop, inverting the lock ordering
- When folio locking is needed (e.g., for the `folio_mapcount` exclusivity
  check), use `folio_trylock()` and bail out on failure, waiting for the
  folio to become unlocked after releasing all other locks (see
  `need_wait_lock` handling in `hugetlb_fault()` in `mm/hugetlb.c`)
- Prefer testing folio state without locking when possible (e.g.,
  `folio_test_anon()` does not require the folio lock)

## Hugetlb Pool Accounting

Incorrect manipulation of hugetlb pool counters causes kernel crashes
(via `VM_BUG_ON`), reservation leaks, surplus counter corruption, or
over-allocation. Review any code that reads or modifies `hstate` pool
counters.

The `hstate` struct (see `include/linux/hugetlb.h`) tracks per-page-size
pool state through global counters, all protected by `hugetlb_lock`:

| Counter | Per-node variant | Meaning |
|---------|-----------------|---------|
| `nr_huge_pages` | `nr_huge_pages_node[nid]` | Total pages in pool (free + in-use) |
| `free_huge_pages` | `free_huge_pages_node[nid]` | Pages on the free list |
| `surplus_huge_pages` | `surplus_huge_pages_node[nid]` | Pages beyond the persistent pool size |
| `resv_huge_pages` | *(global only)* | Pages reserved for future faults |

**Available (unreserved free) pages** = `free_huge_pages - resv_huge_pages`
(see `available_huge_pages()` in `mm/hugetlb.c`).

**Reservation lifecycle:**
1. `hugetlb_reserve_pages()` establishes reservations by calling
   `hugetlb_acct_memory()`, which increments `resv_huge_pages` under
   `hugetlb_lock`
2. The allocation function dequeues a page and decrements `resv_huge_pages`
3. These two steps are NOT atomic -- there is a lock-drop gap between them

**Correct allocation pattern** (`alloc_hugetlb_folio()` in `mm/hugetlb.c`):
- Uses `gbl_chg` (from `vma_needs_reservation()`) to determine whether the
  allocation is consuming a reservation or requires an unreserved page
- `dequeue_hugetlb_folio_vma()` checks `available_huge_pages(h)` before
  dequeuing when `gbl_chg` is set
- Only decrements `resv_huge_pages` when `!gbl_chg`

**Interdependent counter atomicity:**
Derived values like `persistent_huge_pages()` (`nr_huge_pages -
surplus_huge_pages`) combine multiple counters. When related counters are
updated across different lock-hold windows (e.g., dropping the lock to
allocate, then reacquiring), concurrent readers see transiently inconsistent
state. All related counter updates must occur within the same `hugetlb_lock`
hold (see `alloc_surplus_hugetlb_folio()` in `mm/hugetlb.c`).

**`adjust_surplus` parameter:**
`remove_hugetlb_folio()` and `add_hugetlb_folio()` in `mm/hugetlb.c`
take a `bool adjust_surplus` that controls whether surplus counters are
decremented/incremented. Callers must check
`h->surplus_huge_pages_node[folio_nid(folio)]` and pass the result.
Hardcoding `false` silently skips the adjustment for surplus pages. Error
paths that call `add_hugetlb_folio()` to undo a removal must use the same
`adjust_surplus` value. See `free_huge_folio()` in `mm/hugetlb.c` for the
correct pattern.

**Common mistakes:**
- Assuming `resv_huge_pages > 0` whenever a folio is dequeued -- the dequeue
  can succeed from the unreserved-free pool
- Using `VM_BUG_ON` to assert reservation state in functions reachable from
  userspace
- Decrementing `resv_huge_pages` without verifying it is positive

## Hugetlb PMD Page Table Sharing and Unsharing

PMD-level page table sharing allows multiple mappings of the same hugetlbfs
file to share a single PMD page table page, reducing memory overhead. Unsharing
(triggered by `MADV_DONTNEED`, munmap, fault on shared page tables, or
mremap) must synchronize against concurrent GUP-fast readers and page table
walkers. Getting this wrong causes use-after-free on page table pages, stale
TLB entries, or GUP returning wrong pages.

**GUP-fast synchronization on unshare:**
When a PUD entry is cleared during page table unsharing, GUP-fast may be
concurrently traversing the page table without holding any locks (only
`local_irq_disable`). The page table page freed by unsharing could be
reused before GUP-fast finishes reading it. `tlb_remove_table_sync_one()`
sends an IPI to all CPUs to ensure no concurrent GUP-fast is in the
critical section before freeing the page table page. Any code path that
clears a PUD or PMD entry pointing to a shared page table must call
`tlb_remove_table_sync_one()` (or use `tlb_remove_table()` which batches
the synchronization). See `huge_pmd_unshare()` in `mm/hugetlb.c`.

**mmu_gather batching:**
When `huge_pmd_unshare()` clears a PUD entry, the unshared page table page
must be freed through the mmu_gather TLB batch mechanism (`tlb_remove_table()`),
not directly via `free_page()`. The `struct mmu_gather` tracks whether
unsharing occurred via `unshared_tables` and `fully_unshared_tables` flags
(see `struct mmu_gather` in `include/asm-generic/tlb.h`). If
`fully_unshared_tables` is set, the subsequent page table walk for unmapping
individual PTEs can be skipped because all page tables were shared (and are
now freed). A missing `tlb_remove_table_sync_one()` or direct free causes
use-after-free under GUP-fast.

**i_mmap_rwsem protocol:**
PMD sharing and unsharing require `i_mmap_rwsem` in write mode to prevent
concurrent sharing/unsharing of the same page tables. Fault paths that
call `huge_pmd_share()` must hold `i_mmap_rwsem` for read (to prevent
concurrent unsharing) and retry with write mode if sharing fails.
Functions that walk VMAs via `i_mmap_foreach()` to unshare page tables
must hold `i_mmap_rwsem` for write. See `hugetlb_walk()` and
`huge_pmd_share()` in `mm/hugetlb.c`.

## PFN Range Iteration and Large Folios

Iterating a physical address or PFN range with `PAGE_SIZE` steps and looking
up folios at each PFN silently breaks when large folios are present: either
tail pages are skipped (losing visibility into most of the folio) or the same
folio is processed multiple times per iteration (double-accounting, duplicate
list insertion, redundant actions).

**Two failure modes:**

1. **Tail page rejection** -- a `PageTail(page)` guard after
   `pfn_to_online_page()` causes the code to skip every PFN that is not the
   head page. The folio is only processed if the head PFN falls within the
   range. For monitoring, tail pages appear unaccessed; for actions, the folio
   may be missed entirely. Note: `page_idle_get_folio()` in `mm/page_idle.c`
   intentionally uses this pattern because its callers iterate a per-PFN bitmap
   where each bit position must correspond to exactly one PFN.

2. **Duplicate processing** -- when `PageTail()` is not filtered,
   `page_folio(page)` returns the same folio for every PFN in that folio's
   span. A `PAGE_SIZE`-stepping loop then processes the folio
   `folio_nr_pages()` times. This is harmless for read-only checks but wrong
   for actions like list insertion, reclaim, migration, or accounting.

**Correct patterns:**

- **Per-folio action loops** (reclaim, migration, DAMOS actions): step by
  `folio_size(folio)` when a folio is found, `PAGE_SIZE` when the PFN has
  no online page or no LRU folio (see `damon_pa_pageout()` and
  `damon_pa_migrate()` in `mm/damon/paddr.c`)
- **Per-PFN bitmap loops** (page_idle): keep `PAGE_SIZE` stepping for
  bitmap alignment but skip tail pages with `PageTail()`. Optionally
  advance by `folio_nr_pages(folio) - 1` after processing the head page
  (see `split_huge_pages_all()` in `mm/huge_memory.c`)

**REPORT as bugs**: code that iterates a PFN or physical address range,
calls `page_folio()` to obtain a folio, performs non-idempotent operations
on that folio, and steps by `PAGE_SIZE` unconditionally.

## HWPoison Content Access Guard

Accessing the content of a hardware-poisoned page from kernel context triggers a
Machine Check Exception (MCE) that is not recoverable in-kernel, causing a kernel
panic. Any code path that reads or writes page data must check `PageHWPoison()`
before accessing the content.

**Two granularities of checking** (see `include/linux/page-flags.h`):
- `PageHWPoison(page)`: per-page check; use when iterating individual subpages
  and skipping only the poisoned ones (e.g., `try_to_map_unused_to_zeropage()`
  in `mm/migrate.c` skips the poisoned subpage but continues scanning others)
- `folio_contain_hwpoisoned_page(folio)`: folio-level early-exit; use when any
  poisoned subpage makes the entire operation unsafe or pointless (e.g.,
  `thp_underused()` in `mm/huge_memory.c` bails out entirely because scanning
  subpage content is not safe without per-page guards)

**Content-accessing functions that need guards** include `pages_identical()`,
`memcmp_pages()`, `memchr_inv()` on mapped page data, `copy_page()`,
`copy_mc_to_kernel()`, and any `kmap`/`kmap_local_page` followed by a read.

**REPORT as bugs**: Code that reads page content (especially in THP split,
migration, KSM, or compaction paths) without first checking `PageHWPoison()`
on pages that could have been marked poisoned by a concurrent or prior
`memory_failure()` call.

## Speculative Folio Access in PFN-Scanning Code

Accessing folio flags or state on a folio obtained via speculative `page_folio()`
during PFN iteration -- without first stabilizing the folio with a reference --
causes `VM_BUG_ON` crashes (in `const_folio_flags()` which asserts
`!(page->compound_head & 1)`), garbage reads from `folio_nr_pages()`, or silent
data corruption. These bugs only trigger when compound page setup or teardown
races with the scan, making them hard to reproduce.

Code that iterates PFNs (memory hotplug, page scanning, memory-failure, THP
splitting) converts `struct page *` to `struct folio *` via `page_folio()`.
This is speculative: the underlying compound page structure may be concurrently
changing (allocation via `prep_compound_page()`, split, or free on another CPU).
The `page_folio()` kernel-doc explicitly warns: "If the caller does not hold a
reference, this call may race with a folio split, so it should re-check the
folio still contains this page after gaining a reference on the folio" (see
`page_folio()` in `include/linux/page-flags.h`).

**Required pattern** (see `split_huge_pages_all()` in `mm/huge_memory.c`,
`page_idle_get_folio()` in `mm/page_idle.c`):
```c
folio = page_folio(page);                        // speculative, may race
if (!folio_try_get(folio))                       // stabilize with a reference
    continue;
if (unlikely(page_folio(page) != folio))         // re-validate after stabilizing
    goto put_folio;
// CORRECT: folio flags and state are now safe to access
```

**REPORT as bugs**: Code in PFN-scanning loops that calls folio flag accessors
(`folio_test_large()`, `folio_test_lru()`, `folio_test_hugetlb()`, etc.) or
reads folio size (`folio_nr_pages()`, `folio_pfn()`) on a folio from
`page_folio()` before calling `folio_try_get()` and re-checking
`page_folio(page) == folio`.

## VMA Flags Modification API

Using the wrong `vm_flags` modifier silently preserves stale flags (if `set` is
used where `reset` was intended) or drops flags (if `reset` is used where `set`
was intended). Stale `VM_WRITE` or `VM_MAYWRITE` flags create security holes;
lost `VM_LOCKED` or `VM_IO` flags cause incorrect memory management behavior.
Review any code that modifies VMA flags to verify the correct API is used.

The Operation column describes the bitwise effect on the VMA's flags. "OR"
means only new bits are added, existing bits are never cleared. "Replace" means
the flags are set to exactly the given value (all previous flags are lost).

| Function | Operation | Locking | Use Case |
|----------|-----------|---------|----------|
| `vm_flags_init()` | Replace | None (no VMA write lock) | VMA not yet in the VMA tree (initial setup, `do_mmap()`, `do_brk_flags()`) |
| `vm_flags_reset()` | Replace | Asserts VMA write-locked | VMA in tree, caller holds write lock, full replacement needed |
| `vm_flags_set()` | OR | Takes VMA write lock | Add flags without clearing any (e.g., `VM_IO \| VM_DONTEXPAND` in mmap handlers) |
| `vm_flags_clear()` | AND-complement | Takes VMA write lock | Remove specific flags without affecting others |
| `vm_flags_mod()` | OR set, then AND-complement clear | Takes VMA write lock | Simultaneously add and remove different flags |
| `__vm_flags_mod()` | OR set, then AND-complement clear | None (no locking) | Same as `vm_flags_mod()` but VMA not in tree or no other users |

See `include/linux/mm.h` for all definitions.

**Common mistake:** using `vm_flags_set(vma, new_flags)` to synchronize or
replace VMA flags. Because `vm_flags_set()` ORs, any flags present in the
VMA but absent from `new_flags` silently survive. Use `vm_flags_reset()` (or
`vm_flags_init()` if the VMA is not yet in the tree) when the intent is to
set flags to an exact value.

## Realloc Zeroing Lifecycle (`want_init_on_alloc` / `want_init_on_free`)

Incorrect zeroing in realloc-style functions that support in-place resize
causes information leaks: stale data from a previous larger allocation is
exposed to the caller after a shrink-then-grow sequence. This affects both
`vrealloc_node_align_noprof()` in `mm/vmalloc.c` and `__do_krealloc()` in
`mm/slub.c`.

`want_init_on_alloc(flags)` in `include/linux/mm.h` returns true when
`CONFIG_INIT_ON_ALLOC_DEFAULT_ON` is enabled or `__GFP_ZERO` is set.
`want_init_on_free()` returns true when `CONFIG_INIT_ON_FREE_DEFAULT_ON` is
enabled. These are independent settings -- `init_on_alloc` can be on while
`init_on_free` is off.

**Zeroing rules for in-place realloc:**
- **Shrink path** (new size < old size): the region `[new_size, old_size)` must
  be zeroed when `want_init_on_free()` OR `want_init_on_alloc(flags)` is true.
  Zeroing on `want_init_on_alloc` is required because a subsequent in-place
  grow must not re-expose stale data from the previously-requested region
- **Grow path** (new size > old size, within backing allocation): if the shrink
  path correctly zeros on `want_init_on_alloc`, the grow path does not need to
  re-zero, because the backing memory was either zeroed at initial allocation
  time or during a prior shrink. The initial allocation zeroes the full backing
  size (see `__vmalloc_node_range_noprof()` in `mm/vmalloc.c`)
- **New allocation path** (new size exceeds backing allocation): the new
  allocation is zeroed by the underlying allocator when `want_init_on_alloc` is
  true; no special handling needed in the realloc wrapper

**Common mistake:** checking only `want_init_on_free()` on the shrink path.
This is wrong because `init_on_alloc` and `init_on_free` are independent --
a system may enable `init_on_alloc` for defense-in-depth while leaving
`init_on_free` off for performance. The shrink path must check both conditions
(see `vrealloc_node_align_noprof()` in `mm/vmalloc.c`).

## Per-CPU LRU Cache Batching

Calling `lru_add_drain_all()` when a folio cannot possibly be in a per-CPU LRU
cache wastes significant time: `lru_add_drain_all()` schedules work on every
online CPU and waits for completion (see `__lru_add_drain_all()` in `mm/swap.c`).
Unnecessary calls degrade performance under workloads that pin large folios.

**Invariant:** Large folios are never held in per-CPU LRU caches. When a large
folio is added to a per-CPU folio batch, the batch is immediately drained (see
`__folio_batch_add_and_move()` in `mm/swap.c` and `mlock_folio()` /
`mlock_new_folio()` / `munlock_folio()` in `mm/mlock.c`, which all check
`!folio_may_be_lru_cached(folio)`).

**API:** `folio_may_be_lru_cached()` in `include/linux/swap.h` returns whether
a folio could be sitting in a per-CPU LRU cache. Currently returns
`!folio_test_large(folio)`.

**Review rule:** Any code that calls `lru_add_drain()` or `lru_add_drain_all()`
on a per-folio basis (e.g., to resolve an unexpected refcount before migration)
should guard the drain with `folio_may_be_lru_cached(folio)`. See
`collect_longterm_unpinnable_folios()` in `mm/gup.c` for the correct pattern.

## Folio Eviction and Invalidation Guards

Evicting or invalidating a folio from the page cache without first verifying
that it is neither dirty nor under writeback causes data loss (dirty data
discarded before reaching storage) or corrupts in-flight IO (storage layer
reads freed memory). These races are timing-dependent and rarely reproduce
outside heavy concurrent IO workloads.

**Required state checks before removal:**

Any code path that removes a folio from the page cache (via
`folio_unmap_invalidate()`, `remove_mapping()`, `__filemap_remove_folio()`,
or similar) must verify under the folio lock:
- `!folio_test_dirty(folio)` -- the folio has not been re-dirtied
- `!folio_test_writeback(folio)` -- the folio is not under active IO

Both conditions can change asynchronously: a concurrent write re-dirties
the folio, and a concurrent writeback submission sets the writeback flag.
The folio lock serializes against these state transitions, so the checks
must happen after the lock is acquired, not before.

**Established pattern** (see `mapping_evict_folio()` in `mm/truncate.c`
and `filemap_end_dropbehind()` in `mm/filemap.c`):
```c
// CORRECT: check dirty+writeback under folio lock before invalidating
folio_lock(folio);  // or folio_trylock()
if (folio_test_dirty(folio) || folio_test_writeback(folio))
	goto skip;
folio_unmap_invalidate(mapping, folio, 0);
```

**Note:** `folio_unmap_invalidate()` itself has a late dirty check
(`folio_test_dirty()` under `xa_lock_irq`) that catches some races and
returns `-EBUSY`, but relying solely on this internal check is
insufficient -- it does not guard against writeback state, and the folio
has already been unmapped by that point, which is wasteful and can cause
unnecessary page faults.

## Folio Migration and Sleeping Constraints

Holding a spinlock across folio migration helper calls causes
sleeping-in-atomic that only triggers for large (multi-page) folios. Code
that was safe when folios were single pages silently becomes buggy when
large folio support is enabled for the affected filesystem or block device.

**Why large folios change sleeping behavior:**

`folio_mc_copy()` in `mm/util.c` copies folio data page-by-page and calls
`cond_resched()` between pages. For single-page folios the loop body
executes once and exits before `cond_resched()`, so the function is
effectively non-sleeping. For multi-page folios, `cond_resched()` fires on
every iteration after the first, making the function a sleeping operation.

**Functions that call `folio_mc_copy()`:**
- `__migrate_folio()` in `mm/migrate.c` (called by `filemap_migrate_folio()`
  and `migrate_folio()`)

**Review rule:** Any `migrate_folio` callback implementation (registered in
`struct address_space_operations`) that holds a spinlock must not call
`filemap_migrate_folio()`, `migrate_folio()`, or any other function that
reaches `folio_mc_copy()` while that spinlock is held. If synchronization
is needed across the migration, use a non-blocking mechanism (e.g., a state
flag checked by concurrent lookup paths, as `BH_Migrate` does in
`__buffer_migrate_folio()` in `mm/migrate.c`) instead of extending the
spinlock scope.

**REPORT as bugs**: Code paths in `migrate_folio` callbacks that hold a
spinlock while calling `filemap_migrate_folio()` or `__migrate_folio()`.
These are sleeping-in-atomic bugs for large folios even if they work
correctly for single-page folios.

## Trylock-Only Allocation Paths (ALLOC_TRYLOCK)

Subroutines in the page allocator that take unconditional locks but are
reachable from `get_page_from_freelist()` will deadlock or livelock when
called via the trylock-only allocation path (`alloc_pages_nolock()` /
`try_alloc_pages()`). These callers set `ALLOC_TRYLOCK` in `alloc_flags`
(see `mm/internal.h`) and omit both `__GFP_DIRECT_RECLAIM` and
`__GFP_KSWAPD_RECLAIM` from GFP flags (making `gfpflags_allow_spinning()`
return false). Both signals must be respected throughout the allocation path.

| Enforcement mechanism | How it works | When correct |
|----------------------|-------------|--------------|
| Fine-grained check in helper | Helper checks `ALLOC_TRYLOCK` or `gfpflags_allow_spinning()`, skips locking operation but lets allocation proceed | Always correct; preferred |
| Coarse-grained early bailout | Caller checks a global condition and returns NULL before `get_page_from_freelist()` | Only when condition is **transient** (resolves on its own, e.g., early boot) |

A coarse bailout for a **persistent** condition permanently disables the
trylock allocation path, silently breaking all callers.

**REPORT as bugs**: New helpers called from `get_page_from_freelist()` that
use `spin_lock()` / `spin_lock_irqsave()` without checking `alloc_flags &
ALLOC_TRYLOCK` or `gfpflags_allow_spinning()`, and without a coarse bailout
for a specific transient condition in the caller.

## File Reference Ownership During mmap Callbacks

Swapping the `struct file` in a driver callback (`f_op->mmap_prepare()` or
the legacy `f_op->mmap()`) without adjusting reference counting causes file
object leaks (extra `get_file()` on the replacement) or use-after-free
(missing reference). The mmap path has a split-ownership model where
`ksys_mmap_pgoff()` holds the original file reference and drops it via
`fput()` at the end, while the VMA independently holds its own reference
via `get_file()`.

**Reference ownership model** (see `ksys_mmap_pgoff()` in `mm/mmap.c` and
`__mmap_new_file_vma()` in `mm/vma.c`):

1. `ksys_mmap_pgoff()` calls `fget(fd)` to obtain the original file (one
   reference), calls `fput()` unconditionally at end
2. `__mmap_new_file_vma()` calls `get_file()` to give the VMA its own
   independent reference
3. When the VMA is destroyed, `remove_vma()` calls `fput(vma->vm_file)`

**When a callback replaces the file**, the replacement (e.g., from
`anon_inode_getfile()` or `shmem_kernel_file_setup()`) already carries its
own reference. The original file is still `fput()`-ed by `ksys_mmap_pgoff()`.
If code unconditionally calls `get_file()` on the replaced file, the
replacement gets an extra reference that is never released.

**File replacement paths:**
- `f_op->mmap_prepare()`: replaces `desc->vm_file`; tracked via
  `map->file_doesnt_need_get` in `call_mmap_prepare()` in `mm/vma.c`
- `f_op->mmap()` (legacy): replaces `vma->vm_file` directly;
  `__mmap_new_file_vma()` reads back `vma->vm_file` afterward
- `shmem_zero_setup()` in `mm/shmem.c`: replaces `vma->vm_file` for
  `MAP_ANONYMOUS|MAP_SHARED`, calls `fput()` on the old file itself

**REPORT as bugs**: Code that unconditionally calls `get_file()` on a file
that may have been swapped by a prior callback, without checking whether the
swap occurred.

## Slab Page Overlay Initialization and Cleanup

`struct slab` in `mm/slab.h` is a memory overlay on `struct page` and
`struct folio` (verified by `SLAB_MATCH` static assertions that check matching
offsets). Failing to initialize fields on allocation or clear them on free
causes stale data dereferences or cross-subsystem state leaks that only
reproduce when recycled pages carry non-zero residual data.

**Initialization**: the page allocator (`post_alloc_hook()` in
`mm/page_alloc.c`) does NOT zero `struct page` metadata fields -- it only
zeros page *data* contents when `__GFP_ZERO` / init_on_alloc is active, and
sets `page_private` to 0, but all other fields retain residual values from
prior use. `allocate_slab()` in `mm/slub.c` must explicitly initialize every
`struct slab` field. Conditionally compiled fields (under `CONFIG_*` ifdefs)
are particularly easy to miss because they are invisible in most build
configurations. New fields added to `struct slab` must have corresponding
initialization in `allocate_slab()`.

**Cleanup on free**: `SLAB_MATCH(memcg_data, obj_exts)` means
`slab->obj_exts` and `folio->memcg_data` share storage. When slab pages are
freed via `__free_slab()` in `mm/slub.c`, all slab-specific metadata --
including sentinel values like `OBJEXTS_ALLOC_FAIL` -- must be zeroed before
the page returns to the page allocator via `free_frozen_pages()`. Leftover
bits are visible through the folio/page view and trigger `VM_BUG_ON_FOLIO`
assertions (e.g., `folio_memcg_kmem()` in `include/linux/memcontrol.h`) or
`free_page_is_bad()` failures ("page still charged to cgroup" in
`page_bad_reason()` in `mm/page_alloc.c`). Review any code that adds new
flags, sentinel values, or states to `slab->obj_exts` to verify all values
are cleared on the slab free path. Additionally, `free_slab_obj_exts()` in
`unaccount_slab()` must be called unconditionally -- it must NOT be gated on
`mem_alloc_profiling_enabled()` or `memcg_kmem_online()`, because both can
change at runtime between allocation and deallocation. Extensions allocated
while a feature was active will leak when the feature is later disabled.
`free_slab_obj_exts()` is idempotent (checks for NULL), so unconditional
calls are safe.

## Folio Isolation for Migration

Folio isolation is a multi-step process where not every folio that qualifies
for migration is successfully added to the isolation list. Code that uses list
emptiness as a proxy for "no work needed" silently skips folios that qualified
but failed isolation, leading to incorrect retry-loop termination or
impermissible longterm pinning.

**Longterm pinning pipeline** (see `__gup_longterm_locked()` in `mm/gup.c`):
- `check_and_migrate_movable_pages_or_folios()` calls
  `collect_longterm_unpinnable_folios()` to identify and isolate folios that
  cannot be longterm pinned, then `migrate_longterm_unpinnable_folios()` to
  migrate them
- The caller retries in a `do { ... } while (rc == -EAGAIN)` loop until all
  folios are pinnable or a fatal error occurs
- `folio_is_longterm_pinnable()` in `include/linux/mm.h` returns false for
  CMA/MIGRATE_ISOLATE folios, device-coherent folios, fsdax folios, and
  movable-zone folios

**Gap between classification and list insertion**: in
`collect_longterm_unpinnable_folios()`, several categories of unpinnable
folios are never added to `movable_folio_list`:
- Device-coherent folios skip the list (they use
  `migrate_device_coherent_folio()` separately)
- `folio_isolate_lru()` fails for folios temporarily isolated by a concurrent
  operation or never on LRU (e.g., CMA pages from `vm_ops->fault`)
- The function returns a `collected` count of all unpinnable folios, not just
  those added to the list

**REPORT as bugs**: code that checks `list_empty()` on a migration/isolation
list to determine whether qualifying items exist, when the collection function
has early-continue paths between qualifying an item and adding it to the list.
Use an explicit count or separate boolean instead.

## HugeTLB State TOCTOU Races

Using `folio_hstate()` or deriving `hstate` from a folio without holding
`hugetlb_lock` after a lockless `PageHuge()` / `folio_test_hugetlb()` check
causes NULL pointer dereferences or `VM_BUG_ON` crashes when the HugeTLB page
is freed concurrently between the check and the use.

**Why the race exists:**
`remove_hugetlb_folio()` in `mm/hugetlb.c` (under `hugetlb_lock`) clears
`PG_hugetlb` via `__folio_clear_hugetlb()`. Subsequently,
`__update_and_free_hugetlb_folio()` destroys the compound page structure.
After this, `folio_size()` no longer returns the original huge page size, so
`size_to_hstate(folio_size(folio))` returns NULL. `folio_hstate()` in
`include/linux/hugetlb.h` wraps `size_to_hstate(folio_size(folio))` and
includes a `VM_BUG_ON_FOLIO(!folio_test_hugetlb(folio))` assertion.

**Unsafe pattern:**
```c
if (PageHuge(page)) {
    struct hstate *h = folio_hstate(folio);  // page may be freed here
    if (!hugepage_migration_supported(h))    // NULL deref if h is NULL
```

**Safe pattern:**
```c
if (PageHuge(page)) {
    struct hstate *h = size_to_hstate(folio_size(folio));
    if (h && !hugepage_migration_supported(h))
```

**When `folio_hstate()` IS safe:** callers that hold `hugetlb_lock`, or callers
that hold a reference preventing the folio from being freed (e.g., during
migration where the folio is pinned). Code outside `mm/hugetlb.c` that
encounters HugeTLB pages through lockless PFN iteration or page table walks
(e.g., `has_unmovable_pages()` in `mm/page_isolation.c`) must use the safe
pattern with a NULL check.

## Zone Watermark Initialization Ordering

Code that uses watermark values as decision thresholds during early boot silently
malfunctions because zero is a valid-looking but incorrect watermark. This produces
skipped reclaim, skipped memory acceptance, or incorrect free-page calculations that
can cause premature OOM or boot failures on confidential VM platforms (TDX/SEV).

Zone watermarks (`zone->_watermark[WMARK_MIN/LOW/HIGH/PROMO]` and `watermark_boost`)
are zero-initialized in `struct zone` and only populated when
`init_per_zone_wmark_min()` runs as a `postcore_initcall` (see
`init_per_zone_wmark_min()` in `mm/page_alloc.c`). Until that point, all watermark
helper functions (`min_wmark_pages()`, `low_wmark_pages()`, `high_wmark_pages()`,
`promo_wmark_pages()`) return 0 through `wmark_pages()` in
`include/linux/mmzone.h`. The `zone_watermark_ok()` family is also affected:
with all watermarks at 0, these checks trivially pass as long as any free pages
exist, masking the need for actions like memory acceptance or compaction.

**Review any new code that uses watermark values for gating or threshold decisions:**
- Verify whether the code path is reachable during early boot (before
  `postcore_initcall` level)
- If reachable, the code must handle `wmark == 0` as "not yet initialized" rather
  than "threshold is met" -- typically by providing a fallback threshold or
  unconditionally performing the minimum required work

## Memblock Range Parameter Conventions

Passing an end address where a size is expected (or vice versa) silently
corrupts memblock region metadata during early boot. Because both parameters
are `phys_addr_t`, the compiler gives no type error, and because memblock
operates before most kernel infrastructure is running, the corruption may be
masked by iteration order or later corrections.

The memblock API uses two incompatible conventions for specifying address ranges:

| Convention | Parameters | Examples |
|------------|-----------|----------|
| `(base, size)` | Range is `[base, base + size)` | `memblock_add()`, `memblock_remove()`, `memblock_set_node()`, `memblock_mark_nomap()`, `memblock_mark_hotplug()`, `memblock_phys_free()`, `memblock_free_late()` (see `mm/memblock.c`) |
| `(start, end)` | Range is `[start, end)` | `reserve_bootmem_region()` in `mm/mm_init.c`, `__memblock_find_range_bottom_up()` / `__memblock_find_range_top_down()` in `mm/memblock.c` |

**Common mistake:** when iterating `memblock_region` entries, code typically
computes both `start = region->base` and `end = start + region->size` for use
with `(start, end)` functions. It is easy to then pass `end` instead of
`region->size` to a `(base, size)` function in the same loop body. Verify each
call site uses the correct parameter by checking the function's documented
parameter names (the second parameter is named `size` or `end` in the
function signature and kernel-doc comment).

## Folio Order vs Page Count

Passing a folio `order` (a log2 exponent) where the actual page count
(`1 << order`) is expected produces silently wrong results -- typically incorrect
alignment, size checks, or loop bounds that only fail for non-trivial orders. The
bug is hard to catch because for order 0 and order 1 the two values coincide, and
for order 2 (`order` = 2, count = 4) the difference is small enough to not be
obvious in testing.

**Key rule:** `round_up()`, `round_down()`, and `ALIGN()` (defined in
`include/linux/math.h`) all require the alignment granularity to be the actual
page count, not the order exponent:

```c
// CORRECT
round_up(index, 1 << order)
round_down(pfn, 1UL << order)
ALIGN(addr, PAGE_SIZE << order)

// WRONG -- passes the exponent, not the power of 2
round_up(index, order)
round_down(pfn, order)
```

Correct usage throughout MM confirms the pattern: `do_sync_mmap_readahead()` in
`mm/filemap.c` uses `round_up(..., 1UL << ra->order)`, `shmem_undo_range()` in
`mm/shmem.c` uses `round_down(base, 1 << order)`, and `block_start_pfn()` in
`mm/compaction.c` uses `round_down(pfn, 1UL << (order))`.

**REPORT as bugs**: Any call to `round_up()`, `round_down()`, or `ALIGN()` where
the alignment argument is a raw `order` variable rather than `1 << order` or
`PAGE_SIZE << order`.

## Page Cache XArray Setup (`mapping_set_update`)

Operating on `mapping->i_pages` with an `xa_state` that was not configured
via `mapping_set_update()` causes workingset shadow node tracking to silently
break: xa_nodes allocated without proper `xa_lru` and `xa_update` callbacks
will not be added to their memcg's `list_lru`, leading to leaked nodes that
are never reclaimed and incorrect `list_lru->nr_items` accounting. The failure
only manifests under memory pressure, making it hard to catch in testing.

**Required setup:** Any code path that initializes an `xa_state` (via
`XA_STATE()` or `XA_STATE_ORDER()`) for `mapping->i_pages` and may allocate
xa_nodes (through `xas_store()`, `xas_create_range()`, or other mutating
operations) must call `mapping_set_update(&xas, mapping)` before the first
mutating xarray operation. This macro (defined in `mm/internal.h`) sets:
- `xas_set_update(xas, workingset_update_node)` -- callback invoked when
  xa_node shadow entry counts change, to maintain the `shadow_nodes` list_lru
  (see `workingset_update_node()` in `mm/workingset.c`)
- `xas_set_lru(xas, &shadow_nodes)` -- tells the xarray allocator which
  list_lru to pre-allocate memcg entries for

**When reviewing:** look for `XA_STATE` or `XA_STATE_ORDER` declarations
using `&mapping->i_pages` (or equivalent `&folio->mapping->i_pages`). If
the function performs any xarray store or create operation, verify that
`mapping_set_update()` is called on the `xa_state` before those operations.
The main `filemap.c` paths (`page_cache_delete()`, `page_cache_delete_batch()`,
`__filemap_add_folio()`) all follow this pattern. Code paths outside
`filemap.c` that operate on the page cache xarray (e.g., `collapse_file()` in
`mm/khugepaged.c`, shmem paths in `mm/shmem.c`) are more likely to omit it.

## Lockless Page Cache Folio Access

Accessing folio properties that depend on compound state (order, mapcount,
nr_pages, LRU membership) from a page cache xarray iteration under RCU
without holding a folio reference races with concurrent folio split or
free. The folio can be split between a `folio_test_large()` check and
a subsequent `folio_large_mapcount()` call, triggering `VM_WARN_ON_FOLIO`
or returning corrupted values. Even without an explicit large-folio check,
functions like `folio_mapcount()` and `folio_nr_pages()` internally branch
on compound state.

**The lockless page cache lookup protocol** (documented in
`filemap_get_entry()` in `mm/filemap.c`):

1. Load the folio from `i_pages` via `xas_load()`/`xas_find()`/`xas_for_each()`
2. Skip retries (`xas_retry()`) and value entries (`xa_is_value()`)
3. Increment the refcount speculatively with `folio_try_get(folio)` --
   if it fails (refcount was zero), reset and retry
4. Verify the folio is still at the same xarray slot with `xas_reload()` --
   if the folio changed (was replaced or removed concurrently), `folio_put()`
   and retry

After this sequence, the folio reference is stable: the folio cannot be
freed or split while the caller holds the reference. The caller must
`folio_put()` on every exit path.

**When a reference is NOT needed:** code that only reads xarray metadata
(marks via `xas_get_mark()`, entry order via `xas_get_order()`) or treats
the folio pointer as an opaque value without dereferencing compound-dependent
fields. See `filemap_cachestat()` in `mm/filemap.c` which deliberately
avoids dereferencing the folio and derives all information from the xarray.
Simple page flag tests (`folio_test_dirty()`, `folio_test_writeback()`) are
also safe under RCU alone because they access `folio->flags` directly
without branching on compound state.

**REPORT as bugs**: Code in `xas_for_each()` / `xas_for_each_marked()`
loops under `rcu_read_lock()` that calls `folio_mapcount()`,
`folio_nr_pages()`, `folio_order()` (when used for branching),
`folio_test_lru()`, `folio_expected_ref_count()`, or `is_refcount_suitable()`
on a folio without first executing the `folio_try_get()` +
`xas_reload()` stabilization sequence.

## Quick Checks

Common MM review pitfalls. Missing any of these typically results in data
corruption, use-after-free, or deadlock that only reproduces under memory
pressure or on NUMA systems.

- **TLB flushes after PTE modifications**: Missing a TLB flush after making a
  PTE less permissive lets userspace keep stale write access, causing data
  corruption or security bypass. Required for writable-to-readonly and
  present-to-not-present transitions. Not needed for not-present-to-present or
  more-permissive transitions (callers pair `ptep_set_access_flags()` with
  `update_mmu_cache()`). See `change_pte_range()` in `mm/mprotect.c` and
  `zap_pte_range()` in `mm/memory.c`
- **VM_WRITE gate for writable PTEs**: code that constructs or installs a
  PTE must only set the writable bit when the VMA has `VM_WRITE`. The
  standard helper `maybe_mkwrite()` in `include/linux/mm.h` enforces this
  by gating `pte_mkwrite()` on `vma->vm_flags & VM_WRITE`. Hugetlb uses a
  separate helper `make_huge_pte()` in `mm/hugetlb.c` that checks
  `VM_WRITE` internally. When reviewing code that constructs writable PTEs
  -- especially in fork/COW copy paths, userfaultfd install paths, or any
  path that copies or installs pages -- verify that the writable bit is
  gated on the VMA's `VM_WRITE` flag, not assumed from context (e.g., "this
  is a COW copy so it should be writable"). VMA permissions can change via
  `mprotect()` between the original mapping and the PTE installation
- **VMA flag and PTE/PMD flag consistency**: when a VMA operation clears
  a `vm_flags` bit that has a corresponding per-PTE or per-PMD
  representation (e.g., `VM_UFFD_WP` / `pte_uffd_wp()`, `VM_SOFT_DIRTY`
  / `pte_soft_dirty()`), the PTE/PMD-level bits must also be cleared
  across all their physical forms (present PTE bit, swap PTE bit, PTE
  markers). This is especially error-prone when the VMA flag clearing
  happens in a different code path from the page table walk (e.g.,
  `userfaultfd_reset_ctx()` in `mm/userfaultfd.c` clears `VM_UFFD_WP`
  but `move_ptes()` in `mm/mremap.c` must separately clear the PTE-level
  bits). See `uffd_supports_page_table_move()` in `mm/mremap.c` and
  `clear_uffd_wp_pmd()` in `mm/huge_memory.c` for the uffd-wp pattern
- **`flush_tlb_batched_pending()` after PTL re-acquisition**: when code drops
  the page table lock (PTL) and re-acquires it (e.g., to split a large folio
  or call `cond_resched()`), it must call `flush_tlb_batched_pending(mm)`
  again after re-acquiring the PTL. While the PTL was released, reclaim on
  another CPU could have unmapped pages via `try_to_unmap_one()` and batched
  the TLB flush. All callers in `mm/madvise.c`, `mm/mprotect.c`,
  `mm/mremap.c`, and `mm/memory.c` follow this pattern. See
  `flush_tlb_batched_pending()` in `mm/rmap.c`
- **Page table removal vs GUP-fast**: code that clears a higher-level page
  table entry (PUD, PMD) to detach or free a page table page must call
  `tlb_remove_table_sync_one()` (or route through `mmu_gather` via
  `tlb_remove_table()`) before the page table page can be reused for any
  other purpose. GUP-fast (`gup_fast()` in `mm/gup.c`) walks page tables
  locklessly under `local_irq_save()`, relying on IPIs to synchronize
  against page table teardown. Without this synchronization, a concurrent
  GUP-fast can follow a stale page table entry into a freed and reused
  page table, resolving pages from an unrelated address space. See
  `tlb_remove_table_sync_one()` in `mm/mmu_gather.c` and
  `tlb_flush_unshared_tables()` in `include/asm-generic/tlb.h`
- **mmap_lock ordering**: Taking the wrong lock type deadlocks or corrupts the
  VMA tree. Write lock (`mmap_write_lock()`) for VMA structural changes
  (insert/delete/split/merge, modifying vm_flags/vm_page_prot). Read lock
  (`mmap_read_lock()`) for VMA lookup, page fault handling, read-only traversal.
  See the VMA Split/Merge Critical Section above for the finer-grained locking
  within `__split_vma()` and related paths.
  See the "Lock ordering in mm" comment block at the top of `mm/rmap.c`
- **`vma_start_write()` before page table access under `mmap_write_lock`**:
  holding `mmap_write_lock` does NOT exclude per-VMA lock readers. Operations
  like `madvise_dontneed` can run under per-VMA lock only (via
  `lock_vma_under_rcu()` in `mm/mmap_lock.c`) without holding `mmap_lock`,
  and can modify page table structure (e.g., PT_RECLAIM clearing PMDs via
  `try_to_free_pte()` in `mm/pt_reclaim.c`). Code holding `mmap_write_lock`
  must call `vma_start_write(vma)` (see `include/linux/mmap_lock.h`) before
  checking or modifying page table state that per-VMA lock holders could
  change. `vma_start_write()` sets `vma->vm_lock_seq = mm->mm_lock_seq`,
  which causes subsequent `vma_start_read()` attempts to fail, draining
  existing per-VMA lock holders. Without it, a window exists where both the
  `mmap_write_lock` holder and a per-VMA lock holder operate on the same page
  tables concurrently. See `collapse_huge_page()` in `mm/khugepaged.c` for the
  correct ordering: `vma_start_write(vma)` before `check_pmd_still_valid()`
- **Failable mmap lock reacquisition**: when code drops the mmap lock and
  reacquires it using a killable variant (`mmap_write_lock_killable()` or
  `mmap_read_lock_killable()` in `include/linux/mmap_lock.h`), the return
  value must be checked. These functions fail with `-EINTR` when the task is
  killed. Ignoring the failure means continuing without the lock held,
  causing unprotected VMA tree access or an unbalanced unlock on the exit
  path. This pattern appears in retry loops that unwind races (e.g.,
  `-ERESTARTNOINTR` handling) and in lock upgrade sequences (read-unlock
  then write-lock-killable). See `expand_stack()` in `mm/mmap.c` and
  `__get_user_pages_locked()` in `mm/gup.c` for correct examples
- **Page fault path lock constraints**: code running in a `->fault` or
  `->page_mkwrite` handler executes under `mmap_lock`, which is nested
  below `i_rwsem` and `sb_start_write` (freeze protection) in the lock
  ordering (see `sb_start_write()` in `include/linux/fs/super.h` and the
  lock ordering comment in `mm/filemap.c`). The full nesting in the write
  path is: `sb_start_write -> i_rwsem -> mmap_lock (via
  fault_in_iov_iter_readable) -> fault handler`. Therefore, fault handlers
  must not perform operations that wait on freeze protection or call into
  userspace handlers that may need freeze protection, as this creates an
  ABBA deadlock. The same constraint applies to any subsystem hook (e.g.,
  security, fsnotify) invoked from the fault path. When copying user data
  under locks that rank above `mmap_lock`, use atomic copies
  (`copy_folio_from_iter_atomic()`) and retry outside the lock on failure
  (see `generic_perform_write()` in `mm/filemap.c`)
- **Folio reference before flag tests or mapping**: Testing folio flags or
  mapping a page without holding a reference is unsafe. Without a reference,
  the folio can be freed and its memory reused as a tail page of a new compound
  page. `const_folio_flags()` and `folio_flags()` in
  `include/linux/page-flags.h` assert the folio is not a tail page, so any
  `folio_test_*()` call on an unreferenced folio can crash if the memory was
  reallocated. `folio_try_get()` must precede flag tests in speculative lookups
  (e.g., page cache iteration via xarray). For mapping, `folio_get()` must
  precede `set_pte_at()` and rmap operations; `validate_page_before_insert()`
  in `mm/memory.c` rejects pages with zero refcount
- **Compound page tail pages**: In `struct page` (see `include/linux/mm_types.h`),
  the page-cache fields (`mapping`, `index`/`__folio_index`, `private`) share a
  union with the tail-page `compound_head` member. Accessing these fields on a
  tail page returns garbage from the `compound_head` pointer without any warning.
  Unlike page flags, which have `PF_HEAD` macro redirection through
  `compound_head()`, raw struct page data fields have no such safety net. Code
  using `struct page *` must call `compound_head()` or `page_folio()` first and
  read the field from the head page. The folio API (`folio_pos()`, `folio->index`,
  `folio->mapping`) avoids this entirely. See `page_offset()` and `page_pgoff()`
  in `include/linux/pagemap.h` for correctly handled examples
- **`pte_unmap_unlock` pointer must be within the kmap'd PTE page**: After a
  PTE iteration loop, the iterated pointer may point one-past-the-end of the
  PTE page. On `CONFIG_HIGHPTE` systems, `pte_unmap()` calls
  `kunmap_local()`, which derives the page address via `PAGE_MASK`. If the
  pointer crosses a page boundary, it unmaps the wrong page. Save the start
  pointer from `pte_offset_map_lock()` or pass `ptep - 1` after the loop.
  Only triggers on 32-bit HIGHMEM architectures
- **`pte_unmap()` LIFO ordering**: when `CONFIG_HIGHPTE` is enabled,
  `pte_offset_map*()` calls `kmap_local_page()` internally (via `__pte_map()`
  in `include/linux/pgtable.h`) and `pte_unmap()` calls `kunmap_local()`.
  Multiple PTE mappings must be unmapped in reverse (LIFO) order. This is
  invisible on 64-bit kernels where `pte_unmap()` only does
  `rcu_read_unlock()`, but triggers a WARNING in `kunmap_local_indexed()`
  on 32-bit HIGHPTE systems. See `kmap_local_page()` documentation in
  `include/linux/highmem.h`
- **`pte_unmap()` must receive the mapped pointer, not a local copy**:
  `pte_unmap()` must be called with the exact `pte_t *` returned by
  `pte_offset_map*()`, not a pointer to a stack-local `pte_t` copy. A common
  pattern is saving `orig_pte = *ptep` for later comparison and then
  accidentally calling `pte_unmap(&orig_pte)` instead of `pte_unmap(ptep)`.
  Both have type `pte_t *` so the compiler gives no warning. On 64-bit
  without `CONFIG_HIGHPTE`, `pte_unmap()` only calls `rcu_read_unlock()`
  so the bug is invisible; with `CONFIG_HIGHPTE`, it passes a stack address
  to `kunmap_local()`, corrupting the kmap stack and leaking the real mapping
- **`pmd_present()` after `pmd_trans_huge_lock()`**: `pmd_trans_huge_lock()`
  succeeds for both present THP PMDs and non-present PMD leaf entries
  (migration entries, device-private entries), because `pmd_is_huge()` in
  `include/linux/huge_mm.h` returns true for any non-none non-present PMD.
  Callers must check `pmd_present()` before calling `pmd_folio()`,
  `pmd_page()`, or any function that assumes a present PMD. See the correct
  pattern in `mlock_vma_folio()` in `mm/mlock.c` and
  `damon_mkold_pmd_entry()` in `mm/damon/vaddr.c`
- **Page table state after lock drop and retry**: when a page table walk
  drops the PTE or PMD lock (e.g., for `cond_resched()`, TLB flush
  batching, or `need_resched()`) and then reacquires it via a retry loop,
  concurrent threads can repopulate previously-empty entries. Any decision
  to free page table structures (PTE pages via `try_get_and_clear_pmd()` /
  `free_pte()` in `mm/pt_reclaim.c`, or PMD entries) must be re-validated
  after lock reacquisition. The fast path that skips re-checking is only
  safe if the lock was held continuously for the entire range. See
  `zap_pte_range()` in `mm/memory.c` where `direct_reclaim` tracks whether
  the PTE lock was dropped, and `try_to_free_pte()` in `mm/pt_reclaim.c`
  which re-checks all entries under the lock as the slow-path fallback
- **VMA merge anon_vma propagation**: when a VMA merge expands an unfaulted
  VMA to absorb a faulted VMA (one with a non-NULL `anon_vma`), the target
  must acquire the source's `anon_vma` via `dup_anon_vma()`. Missing this
  causes use-after-free when the original VMA's `anon_vma` is freed while
  folios still reference it. See `vma_expand()` and `dup_anon_vma()` in
  `mm/vma.c`. Additionally, merge-time checks on `anon_vma` properties
  (e.g., `list_is_singular(&vma->anon_vma_chain)` scalability guard in
  `is_mergeable_anon_vma()`) must be applied to the VMA that **has** the
  `anon_vma` being propagated, not unconditionally to the destination.
  There are three asymmetric cases: (1) destination unfaulted, source
  faulted -- check the source; (2) destination faulted, source unfaulted
  -- check the destination; (3) both faulted -- symmetric. Applying the
  check to the wrong VMA (e.g., always the destination) incorrectly
  rejects merges in case 1 because the unfaulted VMA has an empty
  `anon_vma_chain`. See `vma_is_fork_child()` in `mm/vma.c`
- **File reference ownership during mmap callbacks**: the mmap path has
  split file-reference ownership: `ksys_mmap_pgoff()` holds a reference
  via `fget(fd)` and `fput()`s it unconditionally at exit, while the VMA
  gets its own reference via `get_file()` in `__mmap_new_file_vma()`.
  When a callback (`f_op->mmap_prepare()` or legacy `f_op->mmap()`)
  replaces `vma->vm_file` with a new file, the replacement already
  carries its own reference. Unconditionally calling `get_file()` on
  the (now-replaced) file leaks a reference. `call_mmap_prepare()` in
  `mm/vma.c` tracks this via `map->file_doesnt_need_get`; legacy
  `f_op->mmap()` is handled by `__mmap_new_file_vma()` reading back
  `vma->vm_file` after the call. When adding new callback hooks or
  converting drivers between `mmap` and `mmap_prepare`, verify that
  file-swap reference counting is preserved
- **VMA interval tree and `vma_address()` use pgoff, not PFN**: the
  `mapping->i_mmap` interval tree is keyed by `vm_pgoff` (see
  `vma_start_pgoff()` / `vma_last_pgoff()` in `mm/interval_tree.c`), and
  `vma_address()` in `mm/internal.h` computes a virtual address from a
  `pgoff_t`. Passing a raw PFN where a pgoff is expected searches the wrong
  coordinate space and produces wrong virtual addresses. This confusion
  typically arises for PFNMAP regions that lack struct pages (no
  `page->index` to derive pgoff from), making it tempting to substitute
  the PFN directly. **REPORT as bugs**: raw PFN passed to
  `vma_interval_tree_foreach()`, `vma_address()`, or any pgoff-expecting API
- **Bit-based locking barrier pairing**: when a bit flag is used for mutual
  exclusion (trylock pattern), the unlock must use `clear_bit_unlock()` (release
  semantics), not `clear_bit()` (relaxed, no barrier). The lock side must use
  `test_and_set_bit_lock()` (acquire semantics). Plain `clear_bit()` allows
  stores to be reordered past the unlock on weakly-ordered architectures
  (arm64). MM uses this for `PGDAT_RECLAIM_LOCKED` in `mm/vmscan.c`
- **NUMA node ID validation before `NODE_DATA()`**: `NODE_DATA(nid)` is a raw
  array index into `node_data[]` (see `include/linux/numa.h`) with no bounds
  checking. When a node ID comes from user input, syscall parameters, or
  subsystem configuration (e.g., DAMOS migration target, `move_pages()` node
  array), validate it before use: `numa_valid_node(nid)` checks
  `nid >= 0 && nid < MAX_NUMNODES` (see `include/linux/numa.h`), but code that
  needs a node with actual memory must also check `node_state(nid, N_MEMORY)`.
  The canonical three-part validation is
  `nid >= 0 && nid < MAX_NUMNODES && node_state(nid, N_MEMORY)` (see
  `do_pages_move()` in `mm/migrate.c` and `damon_migrate_pages()` in
  `mm/damon/ops-common.c`). Omitting this causes NULL-pointer dereferences
  that only trigger on NUMA systems or with specific user-provided
  configurations
- **`get_node(s, numa_mem_id())`** can return NULL on systems with memory-less
  nodes (see `get_node()` and `get_barn()` in `mm/slub.c`). A missing NULL
  check causes a NULL-pointer dereference that only triggers on NUMA systems
  with memory-less nodes
- **Node mask selection for memory allocation loops**: iterating
  `for_each_online_node()` or `node_states[N_ONLINE]` to allocate memory
  or size per-node memory resources includes memoryless nodes (nodes with
  CPUs but no physical memory). Allocations attempted on memoryless nodes
  silently fail and fall back to unintended nodes, causing incorrect NUMA
  page distribution or undersized per-node reservations. Use
  `for_each_node_state(nid, N_MEMORY)` or `node_states[N_MEMORY]` instead.
  During early boot `N_MEMORY` may not yet be populated (it is set up by
  `free_area_init()` in `mm/mm_init.c`); boot-time code must build its own
  mask from memblock ranges. The node state definitions are in
  `include/linux/nodemask.h`: `N_ONLINE` (node is online), `N_MEMORY`
  (node has any type of memory), `N_NORMAL_MEMORY` (node has regular
  non-highmem memory)
- **NUMA node count vs node ID range**: `num_node_state(N_MEMORY)` and
  `num_online_nodes()` return the **count** of nodes in a given state, not
  an upper bound on node IDs. Node IDs can be sparse (e.g., only node 1
  has memory, node 0 does not). Using the count as an iteration bound
  (`for (nid = 0; nid < num_node_state(...); nid++)`) silently skips
  nodes whose ID exceeds the count. Use `nr_node_ids` as the upper bound
  for raw node ID iteration, or prefer `for_each_node_state(nid, N_MEMORY)`
  which iterates only over nodes in the given state regardless of ID gaps.
  See `setup_nr_node_ids()` in `mm/mm_init.c` and `for_each_node_state()`
  in `include/linux/nodemask.h`
- **`pfn_to_page()` on boundary PFNs**: `pfn_to_page()` is only safe on
  PFNs known to have a valid backing `struct page`. Under `CONFIG_SPARSEMEM`
  without `CONFIG_SPARSEMEM_VMEMMAP`, it performs a section table lookup via
  `__pfn_to_section()` / `__nr_to_section()` (in `include/linux/mmzone.h`)
  that returns NULL for non-existent sections, causing a NULL dereference in
  `__section_mem_map_addr()`. Loops that iterate PFN ranges and call
  `pfn_to_page()` must check the loop termination condition before the
  conversion, not after. This is latent on VMEMMAP and FLATMEM
  configurations where `pfn_to_page()` is simple pointer arithmetic
- **Zone device page metadata reinitialization**: zone device pages
  (ZONE_DEVICE) bypass `prep_new_page()`, so stale compound metadata
  (`compound_head`, `_nr_pages`, flags) persists across reuse at different
  orders. `page_pgmap()` dereferences a stale `compound_head` pointer as
  `pgmap` due to union overlap. Zone device init paths must clear all
  per-page compound metadata before `prep_compound_page()`
- **Swap `address_space` mutability**: `struct address_space` contains mutable
  fields (`wb_err`, `flags`, locks) that generic error-reporting infrastructure
  may write through error paths. Never mark any `address_space` instance as
  `__ro_after_init`; use `__read_mostly` instead
- **XArray multi-order entry atomicity**: querying a multi-order xarray
  entry's order with `xa_get_order()` (which only holds `rcu_read_lock()`,
  no `xa_lock`) and then acting on that order in a separate locked operation
  (e.g., `xa_cmpxchg_irq()`) is a TOCTOU race. Between the two operations,
  swap entry splitting or large folio swap-out can change the entry's order
  while preserving its value, so cmpxchg succeeds with a stale order. Use
  `XA_STATE` with explicit `xas_lock_irq()`/`xas_unlock_irq()` to combine
  `xas_load()`, `xas_get_order()`, and `xas_store()` in one critical
  section. `xas_get_order()` requires a prior `xas_load()` and must not be
  called on a sibling entry. **REPORT as bugs**: `xa_get_order()` result
  used across a lock boundary to determine how many pages to free or unmap
- **`pfn_valid()` vs `pfn_to_online_page()`**: `pfn_valid()` only confirms
  a struct page exists for the PFN; the page may be offline (memory hotplug
  removed). `pfn_to_online_page()` additionally verifies the page is in an
  online memory section. Use `pfn_to_online_page()` in hwpoison, migration,
  and any path that will access page metadata. See `pfn_to_online_page()`
  in `mm/memory_hotplug.c`
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
- **VMA merge/modify error handling**: `vma_modify()` and `vma_merge()` may
  return an error or a different VMA pointer. When called inside a VMA
  iteration loop, the caller must handle failure without continuing to use
  the original VMA pointer, which may have been freed or modified by a
  successful merge. On merge failure, `vma_merge_struct` fields (`vmg->start`,
  `vmg->end`, `vmg->pgoff`) may have been mutated by the merge attempt and
  not restored; callers that read these fields after a failed merge must save
  originals beforehand or check `vmg_nomem(vmg)` and abort on OOM. See
  `madvise_walk_vmas()` in `mm/madvise.c` for the correct retry pattern and
  `vma_merge_existing_range()` in `mm/vma.c` for the abort label that resets
  the VMA iterator but not vmg fields
- **VMA flag ordering vs merging**: any VMA flag not in `VM_IGNORE_MERGE`
  (defined as `VM_STICKY` in `include/linux/mm.h`) must be present in the
  proposed `vm_flags` before `vma_merge_new_range()` is called in
  `mm/vma.c`. `is_mergeable_vma()` compares
  `(vma->vm_flags ^ vmg->vm_flags) & ~VM_IGNORE_MERGE`, so any flag
  difference outside `VM_IGNORE_MERGE` blocks the merge. Setting a flag on
  a VMA after creation (post-merge) via `vm_flags_set()` or a subsystem
  hook causes all future adjacent VMAs to fail the merge check, silently
  breaking VMA merging. Subsystem flags like `VM_MERGEABLE` must be
  computed and included in the proposed `vm_flags` before the merge
  attempt (see `ksm_vma_flags()` in `mm/ksm.c`)
- **VMA merge side effects vs subsequent page table operations**:
  `vma_complete()` in `mm/vma.c` triggers side effects after a merge
  completes, including `uprobe_mmap()` which can install anonymous PTEs
  (uprobe breakpoint pages) into the merged VMA range. Callers that will
  subsequently move, copy, or overwrite page tables in the same range
  (e.g., `move_page_tables()` in `mremap` via `copy_vma()`) must suppress
  these side effects via `skip_vma_uprobe` in `struct vma_merge_struct` /
  `struct vma_prepare` (see `mm/vma.h`). Failing to do so orphans the
  installed PTEs -- they become unreachable anonymous pages that corrupt
  rss counters and leak memory. Review any new caller of VMA merge/expand
  that manipulates page tables afterward, and any new PTE-installing
  callback added to `vma_complete()`
- **Fork-time VMA flag divergence**: source and destination VMA flags can
  diverge during `fork()` before `copy_page_range()` runs. In
  `dup_mmap()` in `mm/mmap.c`, `vm_area_dup()` copies all flags, but
  `dup_userfaultfd()` then clears `__VM_UFFD_FLAGS` (`VM_UFFD_MISSING |
  VM_UFFD_WP | VM_UFFD_MINOR`) on the destination VMA when
  `UFFD_FEATURE_EVENT_FORK` is absent, and `vm_flags_clear(tmp,
  VM_LOCKED_MASK)` clears locking flags. Code that checks VMA flags to
  make fork-time decisions (e.g., `vma_needs_copy()` in `mm/memory.c`
  which checks `VM_COPY_ON_FORK` containing `VM_UFFD_WP`) must use the
  destination VMA, not the source. When combining multiple flag checks
  into a single mask check, verify all constituent flags have the same
  source-vs-destination semantics
- **Page comparison for zeropage remapping must use `pages_identical()`**:
  raw byte-level comparisons (`memchr_inv()`, `memcmp()`) miss architecture-
  specific page metadata. On arm64 with MTE (Memory Tagging Extension), a user
  page may be byte-identical to the shared zeropage but carry a different MTE
  tag; remapping it to `ZERO_PAGE(0)` causes tag mismatch faults in userspace.
  `pages_identical()` in `include/linux/mm.h` calls `memcmp_pages()`, which
  has an arm64 override in `arch/arm64/kernel/mte.c` that rejects MTE-tagged
  pages. **REPORT as bugs**: `memchr_inv()` or `memcmp()` used to decide
  whether to remap a page to the shared zeropage or merge pages
- **Large folio size preconditions on hwpoison paths**: `unmap_poisoned_folio()`
  in `mm/memory-failure.c` cannot handle large non-HugeTLB folios (its comment
  states "The caller must guarantee the folio isn't large folio, except
  hugetlb"). Callers iterating folios (reclaim, migration, hotplug) must check
  `folio_test_large(folio) && !folio_test_hugetlb(folio)` and skip or split
  before calling. See the guards in `do_migrate_range()` in
  `mm/memory_hotplug.c` and `shrink_folio_list()` in `mm/vmscan.c`. The
  `memory_failure()` path in `mm/memory-failure.c` handles this by calling
  `try_to_split_thp_page()` to reduce to order-0 before proceeding
- **NUMA mempolicy-aware vs node-specific allocation**: replacing a
  mempolicy-aware allocator (`alloc_pages()`, `alloc_frozen_pages()`,
  `folio_alloc()`) with a node-specific one (`alloc_pages_node()`,
  `__alloc_pages_node()`, `__alloc_frozen_pages()`) silently drops the
  task's NUMA placement policy (`mbind()`, `set_mempolicy()`). The
  mempolicy-aware functions route through `alloc_pages_mpol()` in
  `mm/mempolicy.c`, which consults `get_task_policy(current)`. The
  node-specific functions resolve `NUMA_NO_NODE` to `numa_mem_id()` and
  call `__alloc_pages()` directly, bypassing all policy. This is invisible
  in functional testing -- pages allocate successfully but land on the wrong
  nodes. Consolidating a non-node function into a `_node` variant with
  `NUMA_NO_NODE` as default is a common refactoring mistake. The correct
  pattern branches: mempolicy-aware when `node == NUMA_NO_NODE`,
  node-specific when a specific node is requested (see
  `___kmalloc_large_node()` in `mm/slub.c`)
- **NOWAIT allocation error codes**: code using `GFP_NOWAIT` or
  `__GFP_NORETRY` must return `-EAGAIN` (not `-ENOMEM`) on allocation
  failure when the caller can retry. `-ENOMEM` signals permanent failure
  and may cause the caller to abort an operation that could succeed on retry
- **Deferred split queue for large folios**: when partially unmapping a
  large folio (unmapping some but not all subpages), the folio should be
  queued for deferred splitting via `deferred_split_folio()`. Missing this
  call wastes memory because the partially-mapped folio cannot be reclaimed
  until fully unmapped. See `deferred_split_folio()` in `mm/huge_memory.c`
- **GFP flag propagation in allocation helpers**: when a function wraps
  an allocation and adds its own GFP flags (e.g., `__GFP_ZERO`,
  `__GFP_NOWARN`), it must preserve the caller's flags via bitwise OR,
  not replace them. Replacing the caller's `GFP_KERNEL` with
  `GFP_KERNEL | __GFP_ZERO` is correct; replacing it with just
  `__GFP_ZERO` drops reclaim and IO flags
- **Hugetlb page cache insertion protocol**: any code path that calls
  `hugetlb_add_to_page_cache()` must first zero the folio with
  `folio_zero_user()`, mark it uptodate with `__folio_mark_uptodate()`, and
  hold `hugetlb_fault_mutex_table[hash]` for the index. These preconditions
  are not enforced by `hugetlb_add_to_page_cache()` itself. Paths that bypass
  the normal fault handler (`hugetlb_no_page()`) commonly miss one or more
  steps, causing kernel memory disclosure (unzeroed folio), page cache
  inconsistency (not uptodate), or races with concurrent faults/truncation
  (missing mutex). See `memfd_alloc_folio()` in `mm/memfd.c` and
  `hugetlbfs_fallocate()` in `fs/hugetlbfs/inode.c` for the correct pattern
- **VM_ACCOUNT preservation during VMA manipulation**: `VM_ACCOUNT` controls
  whether a VMA's pages are charged against `vm_committed_as` (overcommit
  accounting). When a VMA continues to exist after an operation (e.g.,
  `MREMAP_DONTUNMAP` leaves the old VMA as an empty mapping, or partial
  unmaps split a VMA), `VM_ACCOUNT` must be preserved on the surviving VMA.
  Clearing it causes a permanent accounting leak: the pages were charged at
  mmap/mremap time, but `do_vmi_munmap()` only calls `vm_unacct_memory()`
  for VMAs with `VM_ACCOUNT` set (see `vms_gather_munmap_vmas()` in
  `mm/vma.c`). Review any `vm_flags_clear()` that includes `VM_ACCOUNT`
  to verify the VMA is actually being destroyed, not preserved
- **Kernel page table population synchronization**: on architectures where
  kernel PGD/P4D entries are not shared across processes (e.g., x86_64 above
  `TASK_SIZE`), populating a kernel page table entry with `pgd_populate()` or
  `p4d_populate()` directly does NOT synchronize to other page tables. Use
  `pgd_populate_kernel()` / `p4d_populate_kernel()` from
  `include/linux/pgalloc.h`, which call `arch_sync_kernel_mappings()` when
  `ARCH_PAGE_TABLE_SYNC_MASK` requires it. Affected paths include vmemmap,
  percpu, and KASAN shadow setup in `mm/`
- **`ALLOC_TRYLOCK` / trylock-only allocation paths**: subroutines reachable
  from `get_page_from_freelist()` that take unconditional locks (`spin_lock()`)
  will deadlock when called via `alloc_pages_nolock()` / `try_alloc_pages()`,
  which set `ALLOC_TRYLOCK` in `alloc_flags` and make
  `gfpflags_allow_spinning()` return false. New helpers in the allocator must
  check `alloc_flags & ALLOC_TRYLOCK` or `gfpflags_allow_spinning()` and skip
  the locking operation. A coarse early bailout (returning NULL before reaching
  the helper) is only correct for **transient** conditions (e.g., deferred
  pages during early boot); for **persistent** conditions (e.g., unaccepted
  memory on TDX), the check must be pushed into the fine-grained helper so
  the allocation can proceed using already-available pages. See `ALLOC_TRYLOCK`
  in `mm/internal.h` and `gfpflags_allow_spinning()` in `include/linux/gfp.h`
- **SLUB `!allow_spin` retry loops**: in `___slab_alloc()` in `mm/slub.c`,
  retry loops (e.g., `goto new_objects`) must check `!allow_spin` before
  retrying operations that use trylocks. When `gfpflags_allow_spinning()`
  returns false (used by `kmalloc_nolock()`), all lock acquisitions use
  `spin_trylock()`. A trylock can fail deterministically when the caller
  interrupted the lock holder on the same CPU, so retrying without a
  bail-out path creates an infinite loop. Any new code in `___slab_alloc()`
  that adds a `goto` back to a retry label after a trylock-based function
  (like `alloc_single_from_new_slab()` or `alloc_single_from_partial()`)
  must return NULL when `!allow_spin` instead of retrying
- **Slab/page/folio struct overlay cleanup**: `struct slab` overlays
  `struct page` and `struct folio` at the same memory addresses (verified by
  `SLAB_MATCH` assertions in `mm/slab.h`). In particular,
  `slab->obj_exts` and `folio->memcg_data` share storage. When slab pages
  are freed via `__free_slab()` in `mm/slub.c`, all slab-specific metadata
  -- including sentinel values like `OBJEXTS_ALLOC_FAIL` -- must be zeroed
  before the page is returned to the page allocator via
  `free_frozen_pages()`. Leftover bits are visible through the folio/page
  view and trigger `VM_BUG_ON_FOLIO` assertions (e.g., in
  `folio_memcg_kmem()` in `include/linux/memcontrol.h`) or "page still
  charged to cgroup" failures. Review any code that adds new flags or
  sentinel values to slab metadata fields to verify that all values are
  cleared on the slab free path
- **KASAN tag reset in SLUB internals**: any new code path in `mm/slub.c`
  that accesses freed object memory for allocator bookkeeping (freelist
  linking, deferred free lists, metadata) must call `kasan_reset_tag()` on
  the object pointer before the access. `kasan_slab_free()` poisons memory
  with a new tag; accessing it through the old-tagged pointer triggers a
  false use-after-free on ARM64 MTE. Existing helpers like
  `set_freepointer()` and `get_freepointer()` already do this internally,
  but generic helpers like `llist_add()` or direct memory writes do not
- **`__GFP_MOVABLE` mobility contract**: `__GFP_MOVABLE` is both a zone
  modifier (allows ZONE_MOVABLE and CMA) and a mobility hint (pages placed
  in `MIGRATE_MOVABLE` pageblocks via `gfp_migratetype()` in
  `include/linux/gfp.h`). Pages allocated with `__GFP_MOVABLE` MUST be
  either reclaimable or migratable (via registered `movable_operations`).
  A common mistake is registering `movable_operations` conditionally (e.g.,
  `#ifdef CONFIG_COMPACTION`) while passing `__GFP_MOVABLE` unconditionally,
  placing unmovable pages in CMA/ZONE_MOVABLE areas. **REPORT as bugs**:
  `__GFP_MOVABLE` on kernel-internal pages with no migration support
- **`page_folio()` on non-folio compound pages**: `page_folio()` blindly
  casts any compound head page to `struct folio *` with no validation.
  Driver-allocated compound pages (inserted via `vm_insert_page()`) have
  `PG_head` set, so `folio_test_large()` returns true, but they are not
  managed by the MM folio infrastructure -- `folio->mapping` is not set up,
  they are not on the LRU, and folio operations like `split_huge_page()`
  and `mapping_min_folio_order()` will crash or corrupt data. Validation
  gates (e.g., `HWPoisonHandlable()` in `mm/memory-failure.c`, `PageLRU()`
  checks) must not be bypassed by flag-based conditional skips
- **`page_size()` / `compound_order()` on non-compound high-order pages**:
  `compound_order()` checks `PG_head` and returns 0 when it is not set.
  The page allocator can produce high-order pages without `__GFP_COMP`
  (non-compound), so `compound_order()`, `page_size()`, and `compound_nr()`
  all silently return order-0 values for these pages. Functions that receive
  both a `struct page *` and an `order` parameter must use `PAGE_SIZE << order`
  (not `page_size(page)`) when operating on the full allocation. The folio API
  (`folio_order()`, `folio_size()`) has the same `PG_head` check but is safe
  because folios are by definition compound or order-0
- **Folio order vs page count in alignment macros**: `round_up()`,
  `round_down()`, and `ALIGN()` (in `include/linux/math.h`) require the
  alignment granularity to be the actual page count (`1 << order`), not
  the log2 exponent (`order`). Passing `order` directly produces silently
  wrong alignment -- e.g., `round_up(index, order)` with order=4 rounds
  to multiples of 4 instead of 16. The bug is hard to catch because for
  orders 0 and 1 the two values coincide, and for order 2 the difference
  is small. **REPORT as bugs**: any `round_up(x, order)`,
  `round_down(x, order)`, or `ALIGN(x, order)` where `order` is a raw
  folio/page order variable rather than `1 << order` or
  `PAGE_SIZE << order`. See `do_sync_mmap_readahead()` in `mm/filemap.c`
  (`round_up(..., 1UL << ra->order)`) and `shmem_undo_range()` in
  `mm/shmem.c` (`round_down(base, 1 << order)`) for correct usage
- **`_mapcount` +1 bias convention**: the `_mapcount` field in `struct page`
  (and `_entire_mapcount`, `_large_mapcount` in large folios) is initialized
  to -1, representing zero mappings. The logical mapcount is always
  `atomic_read(&page->_mapcount) + 1`. Two functions with similar names have
  different expectations: `page_mapcount_is_type(mapcount)` in
  `include/linux/page-flags.h` expects the biased value (`_mapcount + 1`),
  while `page_type_has_type(page_type)` expects the raw field value. All
  external mapcount accessors (`folio_mapcount()`,
  `folio_precise_page_mapcount()`, `folio_entire_mapcount()`) add 1 before
  returning. When reviewing code that reads `_mapcount` directly, verify
  whether the consuming function expects the raw field value or the biased
  logical mapcount -- a mismatch is an off-by-one bug often masked by range
  checks or safety gaps
- **PFN advancement after page-to-folio conversion**: in PFN-walking loops
  where `page = pfn_to_page(pfn)` may point to any subpage of a large folio,
  `folio_nr_pages(folio)` must not be used directly to advance the PFN.
  `compound_nr(page)` returns 1 for tail pages, so old code using
  `pfn += compound_nr(page) - 1` correctly advanced by 0 on tails. After
  conversion to folios, the equivalent is
  `pfn += folio_nr_pages(folio) - folio_page_idx(folio, page) - 1` which
  advances to the last PFN of the folio regardless of the starting offset
  (see `isolate_migratepages_block()` in `mm/compaction.c` and
  `has_unmovable_pages()` in `mm/page_isolation.c`)
- **Compound page metadata after potential refcount drop**: reading
  `compound_order()`, `compound_nr()`, `folio_nr_pages()`, or `folio_order()`
  after a function call that may have dropped the last reference to the
  page/folio returns unpredictable values -- the page may have been freed and
  its compound metadata overwritten. The comment on `compound_order()` in
  `include/linux/mm.h` explicitly warns callers to "be prepared to handle
  wild return values." The fix is to snapshot the metadata into a local
  variable while the page is still known to be valid (before the
  refcount-dropping operation), and use the snapshot afterward. See
  `isolate_migratepages_block()` in `mm/compaction.c` for the snapshot pattern
- **Lazy MMU mode pairing and hazards**: `arch_enter_lazy_mmu_mode()` /
  `arch_leave_lazy_mmu_mode()` batch PTE writes for performance. Two bug
  patterns: (1) **Read-after-write inside lazy mode**: `pte_fn_t` callbacks
  in `apply_to_page_range()` execute inside lazy MMU mode (set by
  `apply_to_pte_range()` in `mm/memory.c`); reading a PTE after modifying
  it may return stale data. Callbacks must bracket such reads with
  `arch_leave_lazy_mmu_mode()` / `arch_enter_lazy_mmu_mode()`. (2) **Error
  paths skipping leave**: any PTE manipulation loop bracketed by
  enter/leave (e.g., `vmap_pages_pte_range()` in `mm/vmalloc.c`) must
  ensure ALL exit paths call `arch_leave_lazy_mmu_mode()`. Early `return`
  statements inside the loop bypass the post-loop leave call, leaving lazy
  mode permanently active on the thread. Convert to `break` + deferred
  return. The default implementation is a no-op, so these bugs only
  manifest on architectures with non-trivial lazy MMU (x86 Xen PV, sparc,
  powerpc book3s64, arm64)
- **Pageblock migratetype updates for high-order pages**: when updating the
  migratetype of a page at `order >= pageblock_order`, use
  `change_pageblock_range(page, order, migratetype)` in `mm/page_alloc.c`,
  not bare `set_pageblock_migratetype()`. High-order buddy pages span
  `1 << (order - pageblock_order)` pageblocks, each with independent
  migratetype metadata. `set_pageblock_migratetype()` only updates the
  first pageblock; the remaining ones retain their old migratetype.
  `expand()` later subdivides the page and places sub-blocks on freelists
  by their individual pageblock migratetypes, causing mismatches and
  warnings
- **Non-present PTE swap entry type dispatch**: non-present PTEs encode
  several distinct swap entry types (migration, device-private,
  device-exclusive, hwpoison, marker) via `softleaf_type()` in
  `include/linux/leafops.h`. When adding a new entry type or modifying
  dispatch logic, verify each branch accepts only entry types whose
  semantics match that branch. A common mistake is grouping device-exclusive
  with migration (both are non-present PTEs with PFNs) even though their
  refcount behavior and resolution paths are different. `softleaf_has_pfn()`
  shows which types encode a PFN — sharing this property does not make
  types interchangeable in dispatch logic. See `check_pte()` in
  `mm/page_vma_mapped.c` for the canonical three-branch dispatch
- **Per-section metadata iteration across large folios**: under
  `CONFIG_SPARSEMEM`, auxiliary per-page data structures (e.g., `page_ext`)
  are allocated independently per memory section in
  `init_section_page_ext()` in `mm/page_ext.c`. They are NOT contiguous
  across section boundaries. Iterating these structures for a compound page
  or large folio by simple pointer arithmetic (e.g., repeated
  `page_ext_next()`) crashes when the folio spans a section boundary. Use
  section-boundary-aware iterators such as `for_each_page_ext()`, which
  re-derives the pointer via `page_ext_lookup()` at each section crossing
- **`page_folio()` / `compound_head()` require vmemmap-resident pages**:
  `page_fixed_fake_head()` in `include/linux/page-flags.h` accesses
  `page[1].compound_head` under `CONFIG_HUGETLB_PAGE_OPTIMIZE_VMEMMAP`, so
  the page pointer must point into the vmemmap array where adjacent
  `struct page` elements exist. Calling `page_folio()` or `compound_head()`
  on a stack-local `struct page` copy, a single-element heap allocation, or
  any isolated `struct page` causes an out-of-bounds read. When working with
  page snapshots (e.g., for crash-safe dumping), open-code the
  `compound_head` bit-test: read `page->compound_head` directly and check
  `(head & 1)` instead of calling `page_folio()`. See `snapshot_page()` in
  `mm/util.c` for the correct pattern
  (see `page_ext_iter_next()` in `include/linux/page_ext.h`). This is
  distinct from `struct page` arrays, which are virtually contiguous under
  `SPARSEMEM_VMEMMAP`
- **VMA iteration on external mm_struct**: code that iterates VMAs of an
  `mm_struct` not belonging to `current` (e.g., obtained from `mmlist`, rmap
  traversal, or `build_map_info()`) must call `check_stable_address_space(mm)`
  after acquiring the mmap lock and before traversing. `dup_mmap()` in
  `mm/mmap.c` adds the child mm to `mmlist` before all VMAs are copied; on
  failure it stores `XA_ZERO_ENTRY` markers in uncopied slots and sets
  `MMF_UNSTABLE`. Iterating without the check dereferences these markers as
  `struct vm_area_struct *`, causing a NULL pointer crash. The OOM reaper
  (`__oom_reap_task_mm()` in `mm/oom_kill.c`) also sets `MMF_UNSTABLE` when
  it begins tearing down an address space. See `unuse_mm()` in
  `mm/swapfile.c` for correct usage
- **`walk_page_range()` default skips `VM_PFNMAP` VMAs**: when
  `mm_walk_ops` does not define a `.test_walk` callback, the default
  `walk_page_test()` in `mm/pagewalk.c` skips VMAs with `VM_PFNMAP` set
  (it returns 1, and `walk_page_range_mm_unsafe()` converts positive
  returns to 0 before continuing). Callers that need to process all VMAs
  including `VM_PFNMAP` must provide a `.test_walk` that returns 0. Watch
  for callers that interpret a 0 return from `walk_page_range()` as
  "target found and handled" without accounting for the silent skip --
  this can cause failures to appear as successes
- **`ACTION_AGAIN` in page walk callbacks**: `walk->action = ACTION_AGAIN`
  in a `pmd_entry` callback causes `walk_pmd_range()` in `mm/pagewalk.c`
  to retry the same PMD entry with no retry limit (`goto again`).
  `pte_offset_map_lock()` returns NULL non-transiently when the PMD is a
  migration entry (because `___pte_offset_map()` in
  `mm/pgtable-generic.c` returns NULL for `!pmd_present(pmdval)`).
  Setting `ACTION_AGAIN` on `pte_offset_map_lock()` failure in a callback
  creates an infinite loop if migration cannot complete (e.g., migration
  blocked on the walking thread). Callbacks should return 0 without
  `ACTION_AGAIN` to skip the entry gracefully. Note that
  `walk_pte_range()` in `mm/pagewalk.c` already sets `ACTION_AGAIN` when
  `pte_offset_map_lock()` fails internally; callbacks that call
  `pte_offset_map_lock()` directly should not duplicate this retry
- **Page allocator retry-loop termination**: every `goto retry` in
  `__alloc_pages_slowpath()` and `get_page_from_freelist()` in
  `mm/page_alloc.c` must modify state that prevents the same retry path
  from being taken again on the next iteration (e.g., clearing a flag like
  `ALLOC_NOFRAGMENT`, setting a boolean like `drained = true`, or using a
  function with internal retry limits like `should_reclaim_retry()`). A
  retry path without such a guard creates an infinite loop that prevents
  the OOM killer from being reached, hanging the machine under memory
  pressure. When reviewing new or modified retry paths, verify both that
  the guard condition checks the modified state and that the state
  modification itself is correct (e.g., `&= ~FLAG` not `&= FLAG`)
- **Page allocator retry vs restart seqcount consistency**:
  `__alloc_pages_slowpath()` caches allocation context at the `restart`
  label (seqcount cookies from `read_mems_allowed_begin()` and
  `zonelist_iter_begin()`, plus `ac->preferred_zoneref` computed from the
  current `ac->nodemask`). The `retry` label reuses this cached state.
  External state -- cpuset nodemask (modified by `mpol_rebind_nodemask()`)
  and zonelists (modified by memory hotremove) -- can change concurrently.
  If a retry-decision function like `should_reclaim_retry()` reads updated
  external state but `get_page_from_freelist()` iterates using the stale
  `ac->preferred_zoneref`, the allocator loops infinitely. Every `goto
  retry` path must be preceded by (or the `retry` label must begin with)
  `check_retry_cpuset()` / `check_retry_zonelist()` calls that redirect to
  `restart` when external state has changed. Verify this when adding new
  retry paths or restructuring existing ones in the slow path

- **Maple state RCU lifetime**: `struct ma_state` caches pointers to
  internal maple tree nodes that are RCU-protected. Once `rcu_read_unlock()`
  is called, those cached node pointers may refer to freed memory. After
  dropping the RCU read lock, the maple state must be invalidated with
  `mas_set(&mas, index)` or `mas_reset(&mas)` before reuse, forcing the
  next operation to re-walk from the tree root. This is easy to miss when
  `vma_start_read()` drops the RCU lock internally on failure: a retry loop
  that calls `mas_walk()` without resetting the state traverses freed nodes.
  See `lock_vma_under_rcu()` in `mm/mmap_lock.c` for the correct pattern
- **mTHP order-fallback index alignment**: in loops that iterate folio
  orders from highest to lowest (via `highest_order()` / `next_order()`),
  the index or address alignment for each order must be computed into a
  temporary variable, not applied in-place to the original index/address.
  Mutating the original value with `round_down(index, larger_pages)`
  destroys information needed by subsequent iterations at smaller orders,
  producing a wrongly aligned index and data corruption. Correct pattern:
  `aligned_index = round_down(index, pages)` with the original `index`
  preserved (see `shmem_alloc_and_add_folio()` in `mm/shmem.c` and
  `alloc_anon_folio()` in `mm/memory.c`)
- **List iteration with lock drop**: `list_for_each_entry_safe` does not
  protect against concurrent removal when the protecting lock is dropped
  mid-iteration (e.g., to call a sleeping function). `list_del_init()` by a
  concurrent thread makes the removed element self-referential, so
  `list_next_entry()` on it returns the element itself, causing an infinite
  loop. After reacquiring the lock, code must check whether the current
  iterator element is still on the list (via `list_empty()`) before
  computing the next element, and restart from the list head if it was
  removed. See `list_safe_reset_next()` documentation in
  `include/linux/list.h` and `shmem_unuse()` in `mm/shmem.c` for the
  correct pattern
- **`static_branch_*()` on allocation paths**: `static_branch_inc()`,
  `static_branch_dec()`, `static_branch_enable()`, and
  `static_branch_disable()` all acquire `cpus_read_lock()` internally (see
  `static_key_slow_inc()` in `kernel/jump_label.c`). Calling them from
  page allocator paths deadlocks when the allocation occurs during CPU
  bringup, which holds `cpu_hotplug_lock` for write. Either use the
  `_cpuslocked` variants (e.g., `static_branch_inc_cpuslocked()` in
  `include/linux/jump_label.h`) when `cpu_hotplug_lock` is already held,
  or defer the modification via `schedule_work()` to move it out of the
  allocation context
- **Early boot use of MM globals**: `high_memory`, zone boundary PFNs, and
  other globals set by `free_area_init()` (via `set_high_memory()` in
  `mm/mm_init.c`) are not available during `setup_arch()` or other code that
  runs before `free_area_init()`. Using them before initialization silently
  produces wrong values (or triggers `BUG()` with `CONFIG_DEBUG_VIRTUAL`).
  When `__init` code needs the physical memory boundary, use
  `memblock_end_of_DRAM()` instead of `__pa(high_memory - 1) + 1`. Guard
  any remaining `high_memory` accesses with `IS_ENABLED(CONFIG_HIGHMEM)`
  since HIGHMEM architectures (arm, powerpc, x86-32) set `high_memory`
  early in arch-specific code before `free_area_init()`. See
  `__cma_declare_contiguous_nid()` and `cma_alloc_mem()` in `mm/cma.c`
  for the correct pattern
- **Lazy MMU mode implies possible atomic context**: `arch_enter_lazy_mmu_mode()`
  disables preemption on some architectures (sparc in `arch/sparc/mm/tlb.c`,
  powerpc in `arch/powerpc/include/asm/book3s/64/tlbflush-hash.h`) but is a
  no-op on others (x86, arm64). Code that runs inside lazy MMU mode -- including
  `pte_fn_t` callbacks passed to `apply_to_page_range()` /
  `apply_to_existing_page_range()` (called from `apply_to_pte_range()` in
  `mm/memory.c`), and PTE-level loops in `mm/mprotect.c`, `mm/mremap.c`,
  `mm/madvise.c`, `mm/vmscan.c`, and `mm/vmalloc.c` -- must not sleep. In
  particular, memory allocations must use `GFP_ATOMIC` / `GFP_NOWAIT` or be
  performed before entering lazy MMU mode (bulk pre-allocation). This bug
  pattern is architecture-dependent and invisible on x86/arm64 testing
- **NOWAIT error code translation**: when a function downgrades GFP flags
  to nonblocking for NOWAIT callers (e.g., `gfp &= ~GFP_KERNEL; gfp |=
  GFP_NOWAIT` or clearing `__GFP_DIRECT_RECLAIM`), allocation failure
  returns `-ENOMEM` from the page allocator. This must be translated to
  `-EAGAIN` before returning to the caller, because NOWAIT callers (io_uring,
  AIO, `pwritev2(RWF_NOWAIT)`) propagate `-ENOMEM` to userspace as a fatal
  error, while `-EAGAIN` triggers a retry in blocking context. See
  `__filemap_get_folio_mpol()` in `mm/filemap.c` for the canonical example
  of this translation with `FGP_NOWAIT`
- **Bounded iteration under LRU locks**: `isolate_lru_folios()` in
  `mm/vmscan.c` holds `lruvec->lru_lock` (a spinlock acquired by callers
  `shrink_inactive_list()` and `shrink_active_list()`) for the entire scan.
  Any code path that skips or filters LRU entries without advancing the loop's
  termination counter (e.g., zone-ineligible folios not counted toward `scan`)
  creates an unbounded scan under a spinlock, causing hard lockups on systems
  with large LRU lists. Verify that skip paths either advance the termination
  counter or have an independent bound (see `SWAP_CLUSTER_MAX_SKIPPED` in
  `include/linux/swap.h`). The same principle applies to any loop that filters
  elements from a list while holding a spinlock -- the total number of
  filtered-out elements must be bounded
- **`folio_page()` vs PTE-mapped subpage**: `folio_page(folio, 0)` returns the
  head page of the folio (see `include/linux/page-flags.h`), not the subpage
  that a specific PTE maps. When iterating over a PTE batch within a large
  folio, deriving the starting page from `folio_page(folio, 0)` is only correct
  if the batch is known to start at the beginning of the folio. Otherwise, use
  `vm_normal_page()` to get the actual subpage the PTE maps, then
  `page_folio(page)` to get the folio. This matters for any per-page state
  checked across the batch (e.g., `PageAnonExclusive` in
  `commit_anon_folio_batch()` in `mm/mprotect.c`)
- **Migration lock scope across unmap and remap phases**: folio migration has
  two rmap walk phases: `try_to_migrate()` (replaces PTEs with migration
  entries) and `remove_migration_ptes()` (restores PTEs). Both walk the rmap
  tree via `rmap_walk()` / `rmap_walk_locked()` in `mm/rmap.c`, which for
  file-backed folios requires `i_mmap_rwsem`. If `TTU_RMAP_LOCKED` is passed
  to `try_to_migrate()` (indicating the caller pre-acquired `i_mmap_rwsem`),
  the lock must remain held until after `remove_migration_ptes()` with
  `RMP_LOCKED`. Dropping `i_mmap_rwsem` between the phases and letting
  `remove_migration_ptes()` re-acquire it via `rmap_walk()` creates an ABBA
  deadlock: migration holds `folio_lock` -> `i_mmap_rwsem`, but paths like
  `hugetlbfs_punch_hole()` acquire `i_mmap_rwsem` -> `folio_lock`. This
  distinction between anon and file-backed folios matters: anon folios use
  `anon_vma->rwsem`, so lock scope changes correct for anon may violate
  ordering for file-backed folios. See `unmap_and_move_huge_page()` in
  `mm/migrate.c`
- **`try_to_unmap()` on PMD-mapped large folios**: calling `try_to_unmap()`
  on a PMD-mapped large folio without `TTU_SPLIT_HUGE_PMD` hits
  `VM_BUG_ON_FOLIO(!pvmw.pte, folio)` in `try_to_unmap_one()` in
  `mm/rmap.c`. `page_vma_mapped_walk()` returns with `pvmw.pte == NULL`
  for PMD-mapped entries, and only the `TTU_SPLIT_HUGE_PMD` branch handles
  that case. Either pass `TTU_SPLIT_HUGE_PMD` when
  `folio_test_pmd_mappable(folio)` (as `shrink_folio_list()` does for
  normal reclaim in `mm/vmscan.c`), or guard with `folio_test_large()` and
  skip large folios. Wrapper functions like `unmap_poisoned_folio()` in
  `mm/memory-failure.c` do NOT pass `TTU_SPLIT_HUGE_PMD` and require
  callers to guarantee the folio is not a large folio (except hugetlb)
- **`folio_page()` index bounds**: `folio_page(folio, n)` performs unchecked
  pointer arithmetic (see `include/linux/page-flags.h`); passing
  `n >= folio_nr_pages(folio)` accesses memory past the folio's struct page
  array. When `n` is computed from byte-offset arithmetic (e.g.,
  `PAGE_ALIGN_DOWN(offset + length) / PAGE_SIZE` in truncation or split
  paths), verify the boundary case where the sum aligns to `folio_size(folio)`
  does not produce a one-past-the-end index. Either skip the operation or
  clamp the index before calling `folio_page()`
- **kswapd order-dropping and watermark checks**: `kswapd_shrink_node()` in
  `mm/vmscan.c` drops `sc->order` to 0 after reclaiming `compact_gap(order)`
  pages, signaling that enough base pages are freed and contiguity work should
  be handed to kcompactd. Any watermark or balance check in `pgdat_balanced()`
  or `balance_pgdat()` that uses a stricter metric for high-order allocations
  (e.g., `NR_FREE_PAGES_BLOCKS` instead of `NR_FREE_PAGES`) must also check
  `order != 0`, not just a static mode flag. Ignoring the dynamic order
  reduction causes kswapd to keep reclaiming against the strict watermark
  after the handoff point, leading to massive overreclaim
- **Hugetlb subpool reservation rollback**: `hugepage_subpool_get_pages()`
  in `mm/hugetlb.c` transforms its input quantity -- the subpool absorbs
  some pages from its own `rsv_hpages` and returns a smaller `gbl_reserve`
  indicating how many need global hstate accounting. Error paths must return
  only the subpool-consumed portion (`chg - gbl_reserve`) to
  `hugepage_subpool_put_pages()`, not the original request (`chg`). Passing
  the untransformed quantity over-credits `rsv_hpages`, eventually causing
  `resv_huge_pages` to underflow. The return value of
  `hugepage_subpool_put_pages()` must be fed to `hugetlb_acct_memory()` to
  keep both levels in sync. See `hugetlb_vm_op_close()` and
  `hugetlb_unreserve_pages()` in `mm/hugetlb.c` for the correct pattern
- **`mapping_set_update()` before page cache xarray mutations**: any code
  path that initializes an `xa_state` (via `XA_STATE()` or `XA_STATE_ORDER()`)
  for `mapping->i_pages` and performs mutating xarray operations (`xas_store()`,
  `xas_create_range()`) must call `mapping_set_update(&xas, mapping)` (defined
  in `mm/internal.h`) before the first mutation. This macro sets the
  `workingset_update_node()` callback and `shadow_nodes` list_lru on the
  xa_state, which are needed for workingset shadow node tracking. Without it,
  xa_nodes allocated for a non-root memcg are not added to their memcg's
  `list_lru`, silently leaking from reclaim accounting. The main `filemap.c`
  paths (`page_cache_delete()`, `page_cache_delete_batch()`,
  `__filemap_add_folio()`) all call it; code paths outside `filemap.c`
  operating on `mapping->i_pages` (e.g., `collapse_file()` in
  `mm/khugepaged.c`) are more likely to omit it
- **Large folio mapcount field consistency**: a large folio's mapping state
  is spread across multiple independently-updated fields (`_large_mapcount`,
  `_entire_mapcount`, per-page `_mapcount`, `_nr_pages_mapped`, and the
  shared/exclusive tracking in `_mm_ids`). During rmap add/remove operations
  in `__folio_add_rmap()` and `__folio_remove_rmap()` in `mm/rmap.c`, these
  fields are updated non-atomically. Code that reads more than one mapcount
  field to make a decision or assert an invariant must hold
  `folio_lock_large_mapcount()` (a bit spin lock on `_mm_ids`, see
  `include/linux/rmap.h`) to get a consistent snapshot. Without the lock,
  concurrent rmap operations can produce transient states that violate
  invariants (e.g., `folio_entire_mapcount()` still nonzero while
  `_large_mapcount` already reflects an unmap). See
  `__wp_can_reuse_large_anon_folio()` in `mm/memory.c` for the canonical
  stabilization pattern: optimistic unlocked check, then lock, recheck, act
- **Folio order vs mapping entry order**: when code stores multi-order entries
  (large swap entries, large folios) in an xarray mapping, every code path
  that retrieves an entry and pairs it with a folio must verify that the
  folio's order matches the mapping entry's order. Asynchronous paths like
  swap readahead (`swap_cluster_readahead()` in `mm/swap_state.c`) can
  insert order-0 folios into the swap cache for slots that are part of a
  large mapping entry. If the swapin path finds such a folio via
  `swap_cache_get_folio()` and inserts it without first splitting the large
  mapping entry, the store overwrites the multi-order entry, silently losing
  data for the other pages it covered. See `shmem_swapin_folio()` and
  `shmem_split_large_entry()` in `mm/shmem.c` for the correct pattern:
  compare the mapping entry order against `folio_order()` and split the
  large entry when they differ
- **`folio_end_read()` on already-uptodate folios**: `folio_end_read()` uses
  XOR to set `PG_uptodate`, so calling it with `success=true` on a folio that
  is already uptodate toggles the flag off, silently corrupting folio state.
  Code paths that may encounter already-uptodate folios (e.g., after zeroing)
  must use `folio_unlock()` instead. See `folio_end_read()` in `mm/filemap.c`
  and `folio_xor_flags_has_waiters()` in `include/linux/page-flags.h`
- **Refcount as semantic state**: `page_count()` and `folio_ref_count()`
  are lifetime-management counters, not indicators of logical state
  (shared vs exclusive, in-use vs idle). Speculative references from
  GUP (`try_get_folio()` in `mm/gup.c`), memory-failure handling,
  page_idle tracking, and split_huge_pages can transiently inflate the
  refcount. Code that uses a refcount comparison to make a semantic
  decision (e.g., "if `page_count() == 1` then not shared") is fragile:
  any new reference-taker silently changes the outcome. Dedicated
  counters or flags should be used for semantic state (e.g.,
  `pt_share_count` in `struct ptdesc` for HugeTLB PMD sharing,
  `PageAnonExclusive` for exclusive anonymous page ownership). Flag any
  new code that branches on `page_count()` or `folio_ref_count()`
  equaling a specific value to encode non-lifetime semantics
- **`folio_putback_lru()` requires valid memcg**: `folio_putback_lru()`
  calls `folio_add_lru()` then `folio_put()`. Adding a folio to the LRU
  requires valid memcg association because `folio_lruvec()` in
  `include/linux/memcontrol.h` asserts
  `!memcg && !mem_cgroup_disabled()`. After `mem_cgroup_migrate()` in
  `mm/memcontrol.c` transfers the charge to the new folio, the old folio
  has `memcg_data = 0` and must not be added to the LRU. Use plain
  `folio_put()` to free a folio whose memcg association has been cleared.
  See `folio_putback_lru()` in `mm/vmscan.c` and `migrate_folio_move()`
  in `mm/migrate.c` for the correct pattern: `folio_add_lru()` only on
  the destination folio, plain `folio_put()` on the source
- **`pmd_trans_huge()` matches both THP and hugetlb PMDs**: this
  predicate tests the hardware huge/leaf bit, which is set for both
  transparent huge pages and hugetlb mappings. Code that calls
  `pmd_trans_huge()` (or `pmd_is_huge()`, which wraps it) and then
  performs THP-specific operations -- `split_huge_pmd()`,
  `pgtable_trans_huge_withdraw()`, THP folio rmap manipulation -- must
  first check `is_vm_hugetlb_page(vma)` (see
  `include/linux/hugetlb_inline.h`) and handle or reject hugetlb VMAs
  separately. Hugetlb pages use their own page table layout, locking
  (`hugetlb_fault_mutex`), and splitting semantics that are incompatible
  with THP code paths. The same ambiguity applies at the PUD level with
  `pud_trans_huge()` vs PUD-sized hugetlb pages
- **Swap allocator local lock scope**: `folio_alloc_swap()` in
  `mm/swapfile.c` calls `swap_alloc_fast()` and `swap_alloc_slow()` under
  `local_lock(&percpu_swap_cluster.lock)`, which disables preemption. All
  functions reachable from this scope must not sleep: no block device I/O
  with sleeping GFP flags, no `cond_resched()`, no sleeping allocations.
  When a sleeping operation is needed, drop the local lock first and
  reacquire after (see `swap_cluster_alloc_table()` in `mm/swapfile.c`).
  Sleeping under this lock may not trigger warnings in typical testing but
  will fire under `CONFIG_DEBUG_PREEMPT` or with PREEMPT_RT
- **Slab freelist pointer access must use accessors**: with
  `CONFIG_SLAB_FREELIST_HARDENED`, freelist pointers are XOR-encoded via
  `freelist_ptr_encode()` using `s->random` and the pointer address (see
  `mm/slub.c`). Raw pointer writes like `*(void **)ptr = NULL` store
  un-encoded values that decode to garbage. All freelist pointer reads and
  writes must use `get_freepointer()` / `set_freepointer()` in `mm/slub.c`
- **Writeback dirty limit dual-parameter ordering**: the writeback
  dirty-throttle system has mutually-exclusive parameter pairs
  (`vm_dirty_bytes` vs `vm_dirty_ratio`, `dirty_background_bytes` vs
  `dirty_background_ratio`). `domain_dirty_limits()` in
  `mm/page-writeback.c` prioritizes the bytes variant when non-zero. When
  a sysctl handler switches from bytes to ratio mode, it must zero the
  bytes variable **before** calling `writeback_set_ratelimit()` (which
  reads these globals), not after. Otherwise the stale bytes value takes
  priority. See `dirty_ratio_handler()` in `mm/page-writeback.c`
- **Hugetlb HPG flag propagation during demotion**: when a hugetlb folio
  is demoted (split into smaller hugetlb folios), `init_new_hugetlb_folio()`
  in `mm/hugetlb.c` does NOT propagate HPG flags from `folio->private`.
  Allocation-origin flags like `HPG_cma` (see `enum hugetlb_page_flags` in
  `include/linux/hugetlb.h`) control the deallocation path -- CMA-allocated
  folios must free via `hugetlb_cma_free_folio()`. Code that creates new
  hugetlb folios from an existing one must explicitly copy these flags.
  See `demote_free_hugetlb_folios()` in `mm/hugetlb.c` for the pattern
- **Page allocator fallback cost in batched paths**: `rmqueue_bulk()` in
  `mm/page_alloc.c` calls `__rmqueue()` in a loop while holding
  `zone->lock` with IRQs disabled for the entire batch. Changes that make
  `__rmqueue()`'s fallback path more conservative multiply that cost across
  every page in the batch, causing latency spikes. The `enum rmqueue_mode`
  cached across iterations exists to skip already-failed fallback levels.
  Any patch modifying fallback in `__rmqueue_claim()` or `__rmqueue_steal()`
  should be evaluated for per-iteration cost in `rmqueue_bulk()`
- **Large folio boundary spanning in PFN iteration**: when code iterates
  PFNs within bounded sub-ranges (DAMON regions, memory sections, zones)
  and applies an action to the containing folio, a large folio crossing a
  sub-range boundary is encountered in multiple sub-ranges. Without
  deduplication, the action is applied multiple times (double pageout, double
  migration, inflated statistics). Track the last-processed folio pointer
  and skip if seen again, or advance by `folio_size()` instead of
  `PAGE_SIZE`. See `last_applied` in `struct damos` in
  `include/linux/damon.h`
- **Hugetlb folio rejection in generic folio paths**: functions that
  process folios through generic interfaces (rmap walker callbacks,
  migration helpers, page cache batch operations) but only implement
  regular PTE-level handling must reject hugetlb folios early via
  `folio_test_hugetlb()`. Hugetlb folios require distinct page table
  operations (`set_huge_pte_at()` vs `set_pte_at()`), rmap functions
  (`hugetlb_remove_rmap()` vs `folio_remove_rmap_pte()`), RSS accounting
  (`hugetlb_count_sub()` vs `dec_mm_counter()`), and additional locking
  (`hugetlb_vma_trylock_write()`). Compare `try_to_unmap_one()` and
  `try_to_migrate_one()` in `mm/rmap.c` which have full hugetlb branches
  against any new rmap walker callback that lacks them
- **`arch_sync_kernel_mappings()` on error paths**: functions that walk
  page table levels, accumulate a `pgtbl_mod_mask`, and call
  `arch_sync_kernel_mappings()` after the loop must use `break` (not
  `return`) on errors inside the loop. An early `return` skips the sync
  call, leaving other processes' kernel page tables stale on architectures
  where `ARCH_PAGE_TABLE_SYNC_MASK` is non-zero (x86, arm). See
  `__apply_to_page_range()` in `mm/memory.c` and `vmap_range_noflush()`
  in `mm/vmalloc.c`
- **Page-count accounting in folio conversions**: when a function is
  converted from single-page to large-folio operation, every `++`, `--`,
  `+= 1`, and hardcoded page-count of `1` that represents "number of pages
  processed" must be audited. The correct value is typically
  `folio_nr_pages(folio)`. A common mistake is updating most accounting
  sites but missing one, leaving a `counter++` that undercounts for large
  folios. Check all counters, statistics, and threshold comparisons in the
  converted function (see `folio_nr_pages()` in `include/linux/mm.h`)
- **User page zeroing on cache-aliasing architectures**: `__GFP_ZERO` and
  `init_on_alloc` zero pages using `clear_page()` (via `kernel_init_pages()`
  in `mm/page_alloc.c`), which does NOT perform the dcache flush that
  `clear_user_page()` / `clear_user_highpage()` does. On architectures
  where `cpu_dcache_is_aliasing()` or `cpu_icache_is_aliasing()` is true,
  user-mapped pages must be zeroed with `clear_user_highpage()` or
  `folio_zero_user()`. Use `user_alloc_needs_zeroing()` in
  `include/linux/mm.h` to determine whether explicit zeroing is required.
  Any optimization replacing `clear_user_highpage()` with `__GFP_ZERO`
  must be checked against cache-aliasing architectures
- **Memfd file creation API layering**: creating a memfd-backed file by
  calling `shmem_file_setup()` or `hugetlb_file_setup()` directly produces
  a file missing `O_LARGEFILE`, `FMODE_LSEEK | FMODE_PREAD | FMODE_PWRITE`,
  and `security_inode_init_security_anon()`. Use `memfd_alloc_file()` in
  `mm/memfd.c`, which wraps the setup functions and adds the required
  initialization. **REPORT as bugs**: code that creates a memfd file by
  calling `shmem_file_setup()` or `hugetlb_file_setup()` directly instead
  of `memfd_alloc_file()`. Legitimate callers of `shmem_file_setup()` exist
  (DRM gem objects, SGX enclaves, SysV shared memory) but are not memfd files
- **`kmap_local_page()` maps only a single page**: on CONFIG_HIGHMEM systems,
  `kmap_local_page()` creates a temporary mapping for exactly one `PAGE_SIZE`
  page. Accessing beyond `PAGE_SIZE` from the returned address faults because
  adjacent pages in a high-order allocation are not mapped. This is silent
  on 64-bit kernels where `kmap_local_page()` returns a direct-map pointer
  with contiguous adjacent pages. For high-order allocations, iterate with
  `kmap_local_page(page + i)` per page (see `poison_page()` in
  `mm/page_poison.c` and `check_element()` in `mm/mempool.c`).
  `kmap_local_folio()` also maps only the single page at the specified offset
- **Direct map restore before page free**: when a page has been removed from
  the kernel direct map (via `set_direct_map_invalid_noflush()` in
  `include/linux/set_memory.h`), the direct map entry must be restored with
  `set_direct_map_default_noflush()` before the page is freed back to the
  allocator. Freeing first creates a window where another task allocates the
  page and faults via the still-invalid direct map. See `secretmem_fault()`
  and `secretmem_free_folio()` in `mm/secretmem.c`
- **`folio->mapping` NULL for non-anonymous folios**: `folio->mapping` can
  be NULL even for non-anonymous folios in two cases: (1) shmem folios in
  the swap cache, and (2) folios that have been truncated (mapping cleared
  in `filemap_remove_folio()` in `mm/filemap.c`). Code that branches on
  `folio_test_anon()` and then unconditionally dereferences `folio->mapping`
  in the non-anonymous path will NULL-dereference on these folios. The NULL
  check must precede any access to `folio->mapping` members. See
  `folio_check_splittable()` in `mm/huge_memory.c` for the canonical guard
- **Memory hotplug lock for kernel page table walks**: walking kernel page
  tables (`init_mm`) with only the `mmap_lock` is insufficient when memory
  hot-remove is possible. Hot-remove frees intermediate page table levels
  (PUDs, PMDs) for direct-map and vmemmap ranges via `remove_pagetable()`
  and `vmemmap_free()`, causing use-after-free in concurrent walkers.
  Callers of `walk_kernel_page_table_range()` or `walk_page_range_debug()`
  on `init_mm` must hold the memory hotplug lock via `get_online_mems()` /
  `put_online_mems()` (a `percpu_rw_semaphore` in `mm/memory_hotplug.c`).
  The lock must be acquired before `mmap_lock` to maintain lock ordering.
  See the comment in `walk_kernel_page_table_range()` in `mm/pagewalk.c`
  and the locking in `ptdump_walk_pgd()` in `mm/ptdump.c`
- **Mapcount symmetry for non-present PTE entries**: non-present swap PTE
  entries that hold a folio reference (device-private, device-exclusive,
  migration) must keep mapcount consistent so RMAP walks discover all
  mappings. When converting a present PTE to a non-present swap entry, either
  keep the mapcount (entry counts as a mapping for RMAP) or remove it (entry
  is invisible to RMAP). The choice must be symmetric: if mapcount is
  maintained during creation, the teardown path (`zap_nonpresent_ptes()` in
  `mm/memory.c`) must remove it, and the restore path must not re-add it.
  The current convention is to keep mapcount: device-private and
  device-exclusive entries maintain mapcount, and `zap_nonpresent_ptes()`
  calls `folio_remove_rmap_pte()` for both. Migration entries are handled
  differently because `try_to_migrate_one()` in `mm/rmap.c` manages rmap
  removal as part of the migration process itself
- **VMA operation results assigned to struct members**: VMA merge, split, and
  copy operations (`vma_merge_extend()`, `vma_merge_new_range()`, `copy_vma()`
  in `mm/vma.c`) return NULL on failure. When the result is assigned directly
  to a struct member (e.g., `vrm->vma = vma_merge_extend(...)`) before the
  NULL check, the original valid VMA pointer is clobbered. Error-handling
  paths that dereference the struct member (e.g., to check `vm_flags` or
  uncharge memory) then hit a NULL pointer dereference. Assign failable VMA
  operation results to a local variable first, NULL-check, then update the
  struct member only on success
- **Large folio split failure in truncation**: when truncation splits a large
  (PMD-mapped) folio, the split itself unmaps the folio as a side effect,
  causing refaults as PTEs that enforce SIGBUS for accesses beyond `i_size`.
  If the split fails and the PMD mapping is preserved, accesses within the PMD
  range but beyond `i_size` will NOT generate SIGBUS. Code that splits large
  folios during truncation must explicitly unmap the folio on split failure to
  preserve SIGBUS semantics (see `try_folio_split_or_unmap()` in
  `mm/truncate.c`). Shmem/tmpfs is an exception: it intentionally allows PMD
  mappings across `i_size`, so `shmem_mapping()` is checked to skip the unmap
- **Counter-gated tracking list removal**: several MM structures use lists
  whose membership is gated by a resource counter (e.g., `shmem_swaplist`
  membership requires `info->swapped > 0`, maintained by
  `shmem_recalc_inode()` in `mm/shmem.c`; `shmem_unuse()` prunes entries
  with `!info->swapped`). When refactoring moves resource allocation
  relative to list insertion, error paths must check the counter before
  calling `list_del_init()` -- the object may already have been on the list
  from a prior successful operation. Unconditional removal causes iterators
  like `try_to_unuse()` in `mm/swapfile.c` to loop forever because they
  can never find and clean up the object's remaining resources
- **Zone skip criteria consistency in vmscan**: when a function in
  `mm/vmscan.c` skips zones during iteration (e.g., zones with no reclaimable
  pages), verify that all other vmscan functions that feed the same decision
  use compatible criteria. `balance_pgdat()` uses `pgdat_balanced()` to decide
  whether to increment `kswapd_failures`; `allow_direct_reclaim()` and
  `skip_throttle_noprogress()` use `kswapd_failures` as an escape hatch. If
  one function counts a zone that another skips, the escape hatch may never
  fire, causing infinite loops in `throttle_direct_reclaim()`
- **Page table teardown vs GUP-fast**: any code path that clears a PUD or PMD
  entry (page table unsharing, memory hotplug, THP splitting) must ensure
  GUP-fast cannot concurrently traverse the freed page table page. Use
  `tlb_remove_table()` (batched) or `tlb_remove_table_sync_one()` (immediate
  IPI) before freeing. Direct `free_page()` of a page table page that was
  reachable via a PUD/PMD entry causes use-after-free under GUP-fast
- **Batched allocation fallback cost under zone->lock**: `rmqueue_bulk()` in
  `mm/page_alloc.c` holds `zone->lock` for the entire batch of `__rmqueue()`
  calls. If `__rmqueue()` falls back to expensive paths (e.g., searching
  all migrate types, compaction), the lock hold time scales with batch size.
  Verify that fallback paths invoked under `rmqueue_bulk()` are bounded and
  do not trigger reclaim or compaction while holding `zone->lock`
- **Slab post-alloc/free hook symmetry**: `slab_post_alloc_hook()` in
  `mm/slub.c` runs KASAN, kmemleak, KMSAN, allocation tagging, and memcg
  hooks per object. When a late hook (e.g., memcg charging) fails, the
  error-handling free path must undo all hooks that already ran. Compare
  any new or specialized free path (including error-abort functions like
  `memcg_alloc_abort_single()`) against `slab_free()` in `mm/slub.c` for
  the required cleanup hook sequence: `memcg_slab_free_hook`,
  `alloc_tagging_slab_free_hook`, `slab_free_hook`
- **Memory failure accounting consistency**: `action_result()` in
  `mm/memory-failure.c` updates both `num_poisoned_pages` (global, exposed
  as `HardwareCorrupted` in `/proc/meminfo`) and per-node
  `memory_failure_stats` (sysfs) together. Code that calls
  `num_poisoned_pages_inc()` directly without a corresponding
  `update_per_node_mf_stats()` causes user-visible inconsistency between
  `/proc/meminfo` and per-node sysfs counters
- **Folio order vs mapping entry order on swapin**: when swap readahead
  (`swap_cluster_readahead()` in `mm/swap_state.c`) inserts order-0 folios
  into the swap cache for slots that are part of a large mapping entry, the
  swapin path must verify that the folio's order matches the mapping entry's
  order. Inserting a mismatched-order folio without first splitting the large
  mapping entry overwrites the multi-order entry, silently losing data. See
  `shmem_swapin_folio()` and `shmem_split_large_entry()` in `mm/shmem.c`
- **VMA lock vs mmap_lock assertions**: `mmap_assert_locked(mm)` fires when
  only a VMA lock is held. Code paths reachable under per-VMA locks (page
  faults via `lock_vma_under_rcu()`, madvise under `MADVISE_VMA_READ_LOCK`)
  must use `vma_assert_locked(vma)` instead, which accepts either a VMA read
  lock or the mmap_lock. Legacy `mmap_assert_locked()` calls in page table
  walk or zap paths that predate per-VMA locks are likely incorrect. See the
  assert definitions in `include/linux/mmap_lock.h`
- **VMA interval tree coordinate spaces**: the `mapping->i_mmap` interval tree
  is keyed by `vm_pgoff` (see `vma_start_pgoff()` in `mm/interval_tree.c`).
  `vma_address()` in `mm/internal.h` also takes `pgoff_t pgoff`, not a PFN.
  Passing a raw PFN where a pgoff is expected causes incorrect VMA lookups and
  wrong virtual address calculations. For `PFNMAP` regions with no struct
  pages, translate the PFN to a pgoff through the driver/mapping layer; do not
  use the PFN directly as a pgoff substitute
- **GFP_KERNEL under locks in reclaim-reachable paths**: any allocation with
  `__GFP_DIRECT_RECLAIM` (including `GFP_KERNEL`) can trigger direct reclaim,
  which may re-enter MM through swap-out (zswap/zram), writeback, or slab
  shrinking. If the allocation holds a lock that the reclaim path also
  acquires, the result is deadlock. Move allocations outside the critical
  section. See `zswap_cpu_comp_prepare()` in `mm/zswap.c` and the
  preallocate-before-lock_page pattern in `__do_fault()` in `mm/memory.c`
- **Page table walker iterator advancement**: in `do { } while` page table
  walking loops, the page table pointer (pte/pmd/pud/p4d/pgd) must be
  advanced unconditionally in the `while` clause, not inside a conditional
  body. The canonical idiom is `} while (pte++, addr += PAGE_SIZE, addr !=
  end)` for PTEs and `} while (pmd++, addr = next, addr != end)` for
  higher levels. When entries should be skipped (e.g., `pte_none()` in a
  non-create path), use `continue` so that the `while` clause still
  executes. Placing `ptr++` inside an `if` body causes the walker to stall
  when the condition is false. See `apply_to_pte_range()` and
  `apply_to_pmd_range()` in `mm/memory.c` for the correct pattern
- **VMA addresses used as boolean flags**: `vm_start` can legitimately be
  zero (userspace mappings beginning at address 0), so storing an address in
  a variable and later testing `if (addr_var)` to mean "was this set" silently
  fails for zero-address VMAs. Use an explicit `bool` flag for the condition
  and a separate variable for the address value, or use direct comparisons
  (e.g., `vm_start < addr`) instead of truthiness checks. The same applies
  to any `unsigned long` representing a page offset or physical address that
  can be zero
- **KASAN granule alignment in vmalloc poison/unpoison**: `kasan_poison()`
  and `kasan_unpoison()` in `mm/kasan/shadow.c` require the start address
  to be aligned to `KASAN_GRANULE_SIZE` (enforced by `WARN_ON`). In
  realloc/resize paths, the region address is computed from
  `vm->requested_size` (an arbitrary byte count), which is typically not
  granule-aligned. Passing `p + old_size` directly to KASAN helpers triggers
  splats or corrupts shadow memory. Use `kasan_vrealloc()` (in
  `mm/kasan/common.c`) which handles partial granule boundaries at both old
  and new sizes via `round_up()`/`round_down()` and
  `kasan_poison_last_granule()`. Any code outside `mm/kasan/` that passes a
  non-granule-aligned address to `kasan_poison_vmalloc()` or
  `kasan_unpoison_vmalloc()` is a bug
- **`mm_struct` flexible array sizing**: `mm_struct` has a trailing flexible
  array packing cpumask and mm_cid regions accessed via pointer arithmetic
  (`mm_cpumask()`, `mm_cidmask()`). Static definitions (`init_mm` in
  `mm/init-mm.c`, `efi_mm` in `drivers/firmware/efi/efi.c`) must use
  `MM_STRUCT_FLEXIBLE_ARRAY_INIT` which accounts for all regions. Adding a
  new region requires updating `mm_cache_init()` in `kernel/fork.c` (dynamic
  size), `MM_STRUCT_FLEXIBLE_ARRAY_INIT` (static size), and all static
  `mm_struct` definitions
- **PCP locking wrapper requirement**: the per-cpu page allocator (PCP) uses
  `pcp->lock` with custom wrappers (`pcp_spin_trylock()`,
  `pcp_spin_lock_maybe_irqsave()`) defined in `mm/page_alloc.c`. On
  `CONFIG_SMP=n`, the UP spinlock implementation makes `spin_trylock()` a
  no-op that always succeeds (see `arch_spin_trylock()` in
  `include/linux/spinlock_up.h`). The PCP wrappers handle UP via
  `pcp_trylock_prepare()`/`pcp_trylock_finish()` which expand to
  `local_irq_save()`/`local_irq_restore()` on UP, preventing IRQ handler
  reentrancy. Using bare `spin_lock(&pcp->lock)` bypasses this protection:
  an IRQ handler calling `pcp_spin_trylock()` will always "succeed" even
  while the lock is held, corrupting PCP free lists
- **VMA merge functions invalidate input on success**: `vma_merge_new_range()`,
  `vma_merge_existing_range()`, and `vma_modify()` in `mm/vma.c` return the
  merged VMA on success. On a successful merge the original VMA may be freed
  (via `commit_merge()` removing it from the VMA tree and later freeing it).
  Code that calls these functions must use the returned VMA for all subsequent
  operations. Discarding the return value and continuing to use the original
  VMA is a use-after-free. Verify every call site captures the return value
  and replaces the local VMA pointer when non-NULL is returned
- **`vma_modify*()` error returns in VMA iteration loops**: the
  `vma_modify_flags()`, `vma_modify_flags_uffd()`, `vma_modify_name()`,
  and `vma_modify_policy()` functions in `mm/vma.c` return
  `ERR_PTR(-ENOMEM)` when a merge or split fails. Callers that assign
  the return value back to a VMA loop variable (e.g.,
  `vma = vma_modify_flags(...)`) and continue iterating without checking
  `IS_ERR()` will dereference the error pointer. In cleanup or release
  paths where the caller modifies entire VMAs (no split needed), the
  merge failure is benign -- the VMA is unchanged -- but the error
  return still corrupts the iteration. Check that every call site in a
  VMA iteration loop either checks `IS_ERR()` before continuing or uses
  `give_up_on_oom` (for `vma_modify_flags_uffd()`) to suppress the
  error when the merge is best-effort. See `userfaultfd_release_all()`
  in `mm/userfaultfd.c` and the `__must_check` annotations in `mm/vma.h`
- **Page/folio access after failed refcount drop**: when
  `put_page_testzero()` or `folio_put_testzero()` returns false, the caller
  no longer holds a reference. Another CPU may drop the last reference and
  free the page at any moment, so any access to the page or folio after the
  failed testzero is a use-after-free. If the false-return path needs page
  metadata (flags, tags, mapping, order, etc.), the code must save it
  **before** the refcount-dropping call while the caller's own reference
  still protects the page. See `___free_pages()` in `mm/page_alloc.c` for
  the correct pattern: it captures `PageHead(page)` and the alloc tag before
  calling `put_page_testzero()`
- **PTE batch loop bounds**: loops that batch consecutive PTEs (e.g.,
  `folio_pte_batch_flags()` in `mm/internal.h`) must not rely solely on
  `pte_same()` against a synthetically constructed expected PTE to detect
  the end of a folio or mapping region. On paravirtualized platforms (XEN
  PV), `pte_advance_pfn()` can produce `pte_none()` when the target PFN
  has no valid machine frame, causing false matches against actual empty
  PTE slots and overrunning the folio. The loop iteration count must be
  independently bounded using folio metadata (e.g., `folio_pfn()` +
  `folio_nr_pages()` - `pte_pfn()`) so the boundary is enforced regardless
  of PTE value degeneracy
- **SLUB bulk free staging buffer flush**: `free_to_pcs_bulk()` in
  `mm/slub.c` destructively separates objects into local (freed to percpu
  sheaves) and remote/pfmemalloc (staged in a stack-local buffer for
  fallback to `__kmem_cache_free_bulk()`). Because objects are removed
  from the caller's array via `p[i] = p[--size]` when moved to the
  staging buffer, the staging buffer is the only remaining reference.
  Every exit path -- including the normal return after freeing all local
  objects -- must flush the staging buffer if `remote_nr > 0`. Missing a
  flush path is a permanent memory leak, not a deferred free. The same
  principle applies to any bulk free function that destructively
  partitions objects into multiple destination buffers during
  classification
- **VMA lock refcount balance on error paths**: `__vma_enter_locked()` in
  `mm/mmap_lock.c` adds `VMA_LOCK_OFFSET` (0x40000000, defined in
  `include/linux/mm_types.h`) to `vm_refcnt` as a writer-present flag, then
  waits for readers to drain. When the wait uses `TASK_KILLABLE` or
  `TASK_INTERRUPTIBLE`, the `-EINTR` error path must subtract
  `VMA_LOCK_OFFSET` back. A leaked offset permanently blocks VMA detach
  and free (refcount stuck above zero). This hazard is introduced whenever
  code converts a wait from `TASK_UNINTERRUPTIBLE` to a killable variant
- **`pte_offset_map`/`pte_unmap` pairing**: `pte_unmap()` must receive the
  exact `pte_t *` pointer returned by `pte_offset_map()` or its variants
  (`pte_offset_map_lock()`, `pte_offset_map_rw_nolock()`, etc.), never a
  pointer to a local `pte_t` value copy. Both have C type `pte_t *` so the
  compiler does not warn on the mismatch. When `CONFIG_HIGHPTE` is enabled,
  `pte_unmap()` calls `kunmap_local()` which expects the kmap'd address
  (see `include/linux/pgtable.h`); passing a stack address unmaps the wrong
  mapping and leaks the real one. A common mistake is copying a PTE value
  for comparison (`pte_t orig = ptep_get(pte)`) and later passing `&orig`
  to `pte_unmap()` instead of the original mapped pointer

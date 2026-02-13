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

Lazyfree folios (`!folio_test_swapbacked()`) may be discarded without writeback
if clean. The reclaim path must check dirty status before refcount, and only
call `folio_set_swapbacked()` when the folio is genuinely dirty:

1. **Dirty** (not `VM_DROPPABLE`): `folio_set_swapbacked()` and remap
2. **Extra references** (`ref_count != 1 + map_count`): remap and abort,
   but do NOT `folio_set_swapbacked()` -- elevated refcount (e.g., speculative
   `folio_try_get()`) does not mean dirty
3. **Clean, no extra refs**: discard

Both PTE (`try_to_unmap_one()` in `mm/rmap.c`) and PMD
(`__discard_anon_folio_pmd_locked()` in `mm/huge_memory.c`) paths must follow
this order. Barrier protocol matches `__remove_mapping()`: `smp_mb()` between
PTE clear and refcount read; `smp_rmb()` between refcount and dirty flag read.

**REPORT as bugs**: `folio_set_swapbacked()` in lazyfree reclaim without first
confirming dirty, or unconditionally on any abort including elevated refcount.

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

`__filemap_add_folio()` in `mm/filemap.c` adds `folio_nr_pages(folio)` extra
references. A page-cache folio's refcount = 1 (base) + `folio_nr_pages()`
(page cache) + other holders. Removal must drop all page-cache refs via
`folio_put_refs(folio, folio_nr_pages(folio))` (see `filemap_free_folio()`
in `mm/filemap.c`). Using `folio_put()` (single-ref drop) after
`__filemap_remove_folio()` leaks `folio_nr_pages() - 1` refs -- a silent
memory leak only visible with large folios.

## Folio Tail Page Overlay Layout

`struct folio` overlays metadata onto tail page `struct page` slots. Tail
pages have `->mapping = TAIL_MAPPING`; metadata-carrying tail pages overwrite
it. Three consumers must stay in sync when fields are rearranged across tail
page boundaries:

- `free_tail_page_prepare()` in `mm/page_alloc.c` -- skips `TAIL_MAPPING`
  check per metadata-carrying tail page
- `NR_RESET_STRUCT_PAGE` in `mm/hugetlb_vmemmap.c` -- HVO vmemmap restore
  count
- `__dump_folio()` in `mm/debug.c` -- debug printing

Common failure: updating one consumer but missing the others (no compile-time
coupling between them).

## Large Folio PTE Installation

When `pte_range_none()` returns false during large folio installation (some
PTEs already populated), the handler must ensure forward progress:

- **Page cache folios** (`finish_fault()`): fall back to single-PTE install
- **Freshly allocated anon folios** (`do_anonymous_page()`): release folio,
  retry at smaller size via `alloc_anon_folio()`
- **PMD-level** (`do_set_pmd()`): return `VM_FAULT_FALLBACK`

**REPORT as bugs**: returning `VM_FAULT_NOPAGE` (retry) when
`pte_range_none()` fails for a page cache folio without falling back to
single-PTE -- this creates a livelock (hung process, no warning).

## Folio Mapcount vs Refcount Relationship

**Invariant**: `folio_ref_count(folio) >= folio_mapcount(folio)`. Extra
refcount comes from swapcache, page cache, GUP pins, LRU isolation, etc.
(see `folio_expected_ref_count()` in `include/linux/mm.h`).

- Exclusivity check: `mapcount == refcount` means no external users
- Sanity assertion: `mapcount > refcount` is the corrupted/impossible state
  to warn on, NOT `mapcount < refcount` (which is normal)

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

`security_vm_enough_memory_mm()` is not just a check -- on success it
increments `vm_committed_as` via `vm_acct_memory()` in `mm/util.c`. Every
error path after a successful call must invoke `vm_unacct_memory()` (or the
corresponding wrapper like `shmem_unacct_size()`). A leaked charge permanently
inflates `vm_committed_as`, causing `-ENOMEM` under strict overcommit
(`vm.overcommit_memory=2`). Prefer ordering side-effect-free validations
before accounting calls to minimize cleanup paths.

## Mempool Allocation Guarantees

`mempool_alloc()` retries forever when `__GFP_DIRECT_RECLAIM` is set (GFP_KERNEL,
GFP_NOIO, GFP_NOFS) -- NULL checks are dead code. Without it (GFP_ATOMIC,
GFP_NOWAIT) it can fail -- missing NULL checks cause crashes. Match error
handling to the GFP flag (see `mempool_alloc_noprof()` in `mm/mempool.c`).

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

Code receiving a `dirty_throttle_control *dtc` must use `dtc_dom(dtc)` for the
domain, not `global_wb_domain` directly. `balance_dirty_pages()` in
`mm/page-writeback.c` selects between global (`gdtc`) and memcg (`mdtc`)
domains based on `pos_ratio`; hardcoding global values produces wrong
throttling when the memcg domain is selected.

**REPORT as bugs**: `global_wb_domain` field access in functions/traces that
receive a `dtc` parameter, except code explicitly operating on the global
domain (e.g., `global_dirty_limits()`).

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
causing duplicate folio processing. `xas_find()` / `xas_find_marked()` skip
siblings internally. When using `xas_next()`, call
`xas_advance(&xas, folio_next_index(folio) - 1)` after processing to skip
remaining slots. See `filemap_get_read_batch()` in `mm/filemap.c`. The bug
is invisible for order-0 folios.

## Page Cache Information Disclosure

Any interface revealing per-file page cache state (resident, dirty, writeback,
evicted) must gate access behind a write-permission check to prevent side-channel
attacks. Required: `f->f_mode & FMODE_WRITE`, or `inode_owner_or_capable()`, or
`file_permission(f, MAY_WRITE)` (see `can_do_mincore()` in `mm/mincore.c`,
`can_do_cachestat()` in `mm/filemap.c`). This applies to new syscalls, ioctls,
and procfs/sysfs interfaces even when using file descriptors rather than
virtual address ranges.

## kmemleak Tracking Symmetry

Allocation/free APIs must pair symmetrically for kmemleak: `kmalloc()` with
`kfree()`/`kfree_rcu()`, `kmalloc_nolock()` with `kfree_nolock()`. Mixing
them causes "Trying to color unknown object" warnings or false leak reports.

SLUB skips kmemleak registration when `!gfpflags_allow_spinning(flags)` (no
`__GFP_RECLAIM` bits). `kmemleak_not_leak()`, `kmemleak_ignore()`, and
`kmemleak_no_scan()` all warn on unregistered objects. When an allocation
path conditionally skips registration, all subsequent kmemleak state-change
calls must be guarded by the same condition.

## Swap Cache Residency

A folio enters the swap cache via `add_to_swap()` during reclaim and remains
until explicitly removed. `folio_free_swap()` in `mm/swap_state.c` removes it
only when `folio_swapcount(folio) == 0` AND refcount equals `1 + nr_pages`.

**Large folio swapin conflicts:** mTHP swapin fails with `-EEXIST` when any
subpage's swap slot is already occupied by a smaller folio from a racing
swapin. The path must fall back to smaller order or retry (see
`shmem_swapin_folio()` in `mm/swap_state.c`).

**Swap entry reuse (ABA problem):** swap entries are recycled -- the same
`swp_entry_t` can be reassigned to a different folio. `pte_same()` on swap
PTEs only confirms the entry value, not folio identity. After locking a folio
from `filemap_get_folio()` on a swap address space, verify
`folio_test_swapcache(folio)` and `folio->swap.val` still match. After
acquiring the PTE lock when an earlier lookup returned NULL, check
`SWAP_HAS_CACHE` in `si->swap_map[swp_offset(entry)]`. See `move_swap_pte()`
in `mm/userfaultfd.c`.

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

**`memory_failure()` return values** (`mm/memory-failure.c`): `0` = recovered
(no signal needed), `-EHWPOISON` = already poisoned, `-EOPNOTSUPP` = filtered
by `hwpoison_filter()`, other negative = recovery failed (process killed).
Architecture MCE handlers (`kill_me_maybe()` in `arch/x86/kernel/cpu/mce/core.c`)
branch on these. Internal helpers whose returns propagate through
`memory_failure()` must return `0` for successful recovery, not `-EFAULT`.

**Large folio hwpoison:** `PG_hwpoison` is per-page (`PF_ANY`);
`PG_has_hwpoisoned` is per-folio (`PF_SECOND`) as a fast indicator. Both must
stay synchronized. When splitting a poisoned folio, `PG_has_hwpoisoned` must
propagate to the correct sub-folio. Re-check `folio_test_large()` after
acquiring folio lock (concurrent split possible).

**HWPoison content access guard:** accessing poisoned page content triggers
an unrecoverable MCE/panic. Check `PageHWPoison(page)` per-subpage (to skip
individual pages) or `folio_contain_hwpoisoned_page(folio)` for early-exit
before any content access (`pages_identical()`, `copy_page()`,
`kmap_local_page()` + read, etc.). **REPORT as bugs**: content reads in THP
split, migration, KSM, or compaction without hwpoison checks.

## Non-Folio Compound Pages

`page_folio()` blindly casts the compound head to `struct folio *` with no
runtime validity check. Driver-allocated compound pages (via `vm_insert_page()`
with `alloc_pages(GFP_*, order > 0)`) have `PG_head` set so
`folio_test_large()` returns true, but `folio->mapping` and LRU state are
uninitialized. Calling folio operations (`folio_lock()`, `split_huge_page()`,
`mapping_min_folio_order()`) on these produces crashes or corruption.

Validation gates (`HWPoisonHandlable()`, `PageLRU()`, null-mapping checks)
reject non-folio pages. When a code path calls `page_folio()` on pages from
driver mappings, verify a gate has filtered non-folio compound pages.
`folio_test_large()` alone is insufficient -- it checks `PageHead`, set for
any compound page.

## Memcg Charge Lifecycle

Every `mem_cgroup_charge()` must have a corresponding `mem_cgroup_uncharge()`
on the free path. On migration, charge transfers via `mem_cgroup_migrate()` --
the old folio is NOT uncharged separately. `folio_unqueue_deferred_split()`
must precede uncharging to avoid accessing freed memcg data.

**Memcg lookup safety:**
- `folio_memcg()` returns NULL for uncharged folios; may return an offline
  memcg (folios retain `memcg_data` until reparented)
- Operations that charge/record/uncharge must use the resolved online ancestor
  from `mem_cgroup_id_get_online()` consistently. Refactorings replacing an
  explicit memcg parameter with `folio_memcg()` introduce a mismatch (counter
  targets online ancestor, recorded ID is the offline memcg), causing permanent
  counter leaks when cgroups are deleted under pressure
- `mem_cgroup_from_id()` returns an RCU-protected pointer valid only under
  `rcu_read_lock()`. Use `mem_cgroup_tryget()` before `rcu_read_unlock()` to
  extend lifetime. `get_mem_cgroup_from_*()` functions acquire a reference
  internally

**Per-CPU stock drain:** charges are batched in per-CPU stocks. Destroying a
memcg requires `drain_all_stock()` (`mm/memcontrol.c`) -- missing this
prevents cgroup deletion.

## Dual Reclaim Paths: Classic LRU vs MGLRU

`mm/vmscan.c` has two parallel reclaim implementations that must maintain
identical vmstat, memcg event, and tracepoint coverage. MGLRU is runtime-
selectable, so bugs only manifest when the other path is active.

- Classic: `shrink_inactive_list()` / `shrink_active_list()`
- MGLRU: `evict_folios()` / `scan_folios()`

Both call `shrink_folio_list()` but each has its own post-reclaim stat
updates. When modifying vmstat counters, memcg events, or tracepoints in
one function, verify the corresponding change in the other. The pairing
is `shrink_inactive_list()` ↔ `evict_folios()` and `shrink_active_list()`
↔ `scan_folios()`.

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

`zone[i].lowmem_reserve[j]` protects zone `i` (not zone `j`) from
over-consumption by allocations targeting zone `j`. The effective watermark
is `watermark[wmark] + lowmem_reserve[j]` (see `__zone_watermark_ok()` in
`mm/page_alloc.c`). A zone's own entry is always 0. **REPORT as bugs**:
indexing `lowmem_reserve` with the zone's own index, or assuming
`lowmem_reserve[j]` protects zone `j`.

**Per-CPU vmstat counter drift:** `zone_page_state()` omits per-CPU deltas;
on many-CPU systems the error can exceed watermark gaps. When
`zone->percpu_drift_mark` is set and the cached value is below it, code must
use `zone_page_state_snapshot()`. Refactorings replacing higher-level
watermark APIs with direct `zone_page_state()` + `__zone_watermark_ok()`
silently drop this safety check. See `should_reclaim_retry()` and
`pgdat_balanced()` in `mm/vmscan.c`.

## Layered vmstat Accounting (Node vs Memcg)

`lruvec_stat_mod_folio()` / `mod_lruvec_page_state()` update both node and
memcg counters only when `folio_memcg(folio)` is non-NULL; otherwise they
update only the node counter. `mod_node_page_state()` is always node-only;
`mod_lruvec_state()` is always both.

**Stat reconciliation on deferred charging:** when a folio is allocated
without a memcg and stats are recorded, only the node counter increments.
If later charged (e.g., `kmem_cache_charge()` in `mm/slub.c`), the post-
charge path must subtract from the node counter and re-add via the lruvec
interface to populate the memcg counter, or the free path will underflow it.

Review any code path that changes a folio's memcg association after allocation
for stat counters recorded before the association existed.

## Frozen vs Refcounted Page Allocation

`get_page_from_freelist()` returns pages with refcount 0 ("frozen").
`__alloc_pages_noprof()` wraps this and calls `set_page_refcounted()` to
return refcount 1. The `_frozen_` variants (`__alloc_frozen_pages_noprof()`,
`alloc_frozen_pages_nolock_noprof()`) return frozen pages for callers that
manage refcount themselves (compaction, bulk allocation). **REPORT as bugs**:
passing a frozen page to code expecting refcount 1 without calling
`set_page_refcounted()`, or calling `set_page_refcounted()` on a page
intended to stay frozen.

## MGLRU Generation and Tier Bit Consistency

When a folio moves to a new generation, its tier bits (`LRU_REFS_FLAGS`:
`LRU_REFS_MASK`, `PG_referenced`, `PG_workingset`) must be cleared so tier
tracking starts fresh. Stale tier bits inflate access counts and distort
eviction. All paths that set `LRU_GEN_MASK` must also clear `LRU_REFS_FLAGS`
via `old_flags & ~(LRU_GEN_MASK | LRU_REFS_FLAGS)`. This is done in
`folio_update_gen()`, `folio_inc_gen()` in `mm/vmscan.c`, and
`lru_gen_add_folio()` in `include/linux/mm_inline.h` (exception:
`PG_workingset` preserved on workingset refault activation for PSI).

**Review any code modifying `LRU_GEN_MASK` in `folio->flags`** to verify it
also handles `LRU_REFS_FLAGS`.

## Folio Lock Strategy After GUP

After GUP pins a specific folio, use `folio_lock()` or
`folio_lock_killable()`, not `folio_trylock()`. Transient lock contention
from concurrent migration/compaction is expected, not a permanent error.
`folio_trylock()` is correct only in scan/iteration paths that can skip
locked folios (e.g., `shrink_folio_list()`, `folio_referenced()`).

When page table re-validation fails after GUP (e.g., `folio_walk_start()`
returns a different folio), retry GUP from scratch rather than returning an
error -- the page table change is a transient race.

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

Large folio (mTHP) swapin without checking for existing smaller swap cache
entries causes unbounded retry loops. `swapcache_prepare()` fails with
`-EEXIST` when any slot in the range has `SWAP_HAS_CACHE` set, and callers
retrying on `-EEXIST` loop forever because readahead or concurrent swapin
can populate individual order-0 entries persistently.

Before mTHP swapin, use `non_swapcache_batch(entry, nr_pages)` in `mm/swap.h`
to verify no slot is occupied; fall back to order-0 if result < `nr_pages`.
See `can_swapin_thp()` in `mm/memory.c` and `shmem_swap_alloc_folio()` in
`mm/shmem.c`. Any new large folio swapin path must include this check.

## Page Table Walker Callbacks

`pmd_entry` in `struct mm_walk_ops` (see `include/linux/pagewalk.h`) receives
every non-empty PMD including `pmd_trans_huge()`. Failing to handle THP PMDs
causes silent data skipping or crashes from treating a huge-page PFN as a
page table pointer. When `pmd_entry` is defined without `pte_entry`, the
walker does NOT descend to PTEs -- the callback must walk PTEs internally.

Return values: `0` = continue, `> 0` = stop (returned to caller), `< 0` =
error. `walk_lock` specifies locking: `PGWALK_RDLOCK` (mmap_lock read),
`PGWALK_WRLOCK` (walker write-locks VMAs), `PGWALK_WRLOCK_VERIFY` /
`PGWALK_VMA_RDLOCK_VERIFY` (assert already locked).

In `pmd_entry` callbacks: read PMD locklessly with `pmdp_get_lockless()`,
reread under `pmd_lock()` for THP; check `pte_offset_map_lock()` return for
NULL; call `folio_get()` before releasing PTL if returning a folio reference.

## Folio Reference Count Expectations

`folio_expected_ref_count()` in `include/linux/mm.h` calculates expected
refcount from pagecache, swapcache, `PG_private`, and mappings. Compare
against `folio_ref_count()` to detect unexpected references from any source.
Per-CPU batching (LRU pagevecs in `mm/swap.c`, mlock/munlock batches in
`mm/mlock.c`) holds transient `folio_get()` references invisible to flag
checks. `lru_add_drain_all()` drains all CPUs' batches; code detecting
unexpected references should drain and recheck before concluding the folio
is not migratable (see `collect_longterm_unpinnable_folios()` in `mm/gup.c`).

**REPORT as bugs**: using `folio_test_lru()` as proxy for "has extra refs"
instead of comparing `folio_ref_count()` against `folio_expected_ref_count()`.

## Hugetlb Fault Path Locking

Lock ordering: `hugetlb_fault_mutex` -> `vma_lock` -> `i_mmap_rwsem` ->
`folio_lock` (see `mm/rmap.c` comment block). `hugetlb_wp()` drops the mutex
and vma_lock mid-operation (to call `unmap_ref_private()` which needs
vma_lock in write mode). Acquiring `folio_lock` before this drop inverts
the ordering.

Do NOT use `filemap_lock_folio()` while holding `hugetlb_fault_mutex` in
paths reaching `hugetlb_wp()`. Use `folio_trylock()` and bail on failure,
waiting after releasing all locks (see `need_wait_lock` in `hugetlb_fault()`
in `mm/hugetlb.c`). Prefer testing folio state without locking when possible
(e.g., `folio_test_anon()` does not need the folio lock).

## Hugetlb Pool Accounting

The `hstate` struct (`include/linux/hugetlb.h`) has four counters (all
protected by `hugetlb_lock`): `nr_huge_pages` (total), `free_huge_pages`,
`surplus_huge_pages` (beyond persistent pool), `resv_huge_pages` (reserved).
Available = `free_huge_pages - resv_huge_pages` (see `available_huge_pages()`).
Each has per-node variants except `resv_huge_pages`.

**Key rules:**
- `alloc_hugetlb_folio()` uses `gbl_chg` from `vma_needs_reservation()` to
  distinguish reserved vs unreserved allocation; only decrements
  `resv_huge_pages` when `!gbl_chg`
- Derived values (`persistent_huge_pages()` = `nr_huge_pages -
  surplus_huge_pages`) combine counters that must be updated in the same
  `hugetlb_lock` hold to avoid transient inconsistency
- `remove_hugetlb_folio()` / `add_hugetlb_folio()` take `bool adjust_surplus`;
  callers must check `surplus_huge_pages_node[nid]` and pass the result --
  hardcoding `false` silently skips surplus adjustment. Error paths must use
  the same value as the forward path

## Hugetlb PMD Page Table Sharing and Unsharing

When unsharing hugetlb PMD page tables, the freed page table page must go
through `tlb_remove_table()` (not direct `free_page()`) to synchronize
against GUP-fast, which traverses page tables locklessly under
`local_irq_disable`. `tlb_remove_table_sync_one()` sends an IPI to ensure
no concurrent GUP-fast before reuse. `struct mmu_gather` tracks unsharing
via `unshared_tables` / `fully_unshared_tables` flags.

**Locking:** PMD sharing/unsharing requires `i_mmap_rwsem` in write mode.
Fault paths calling `huge_pmd_share()` hold it for read and retry with
write on failure. See `huge_pmd_unshare()` and `huge_pmd_share()` in
`mm/hugetlb.c`.

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

## Speculative Folio Access in PFN-Scanning Code

`page_folio()` in PFN-scanning loops is speculative -- compound page structure
may change concurrently. Accessing folio flags or size before stabilizing
causes `VM_BUG_ON` in `const_folio_flags()` or garbage reads.

**Required pattern** (see `split_huge_pages_all()` in `mm/huge_memory.c`):
```c
folio = page_folio(page);                        // speculative
if (!folio_try_get(folio))                       // stabilize
    continue;
if (unlikely(page_folio(page) != folio))         // re-validate
    goto put_folio;
// NOW safe to access folio flags and state
```

**REPORT as bugs**: folio flag accessors or size reads on an unreferenced
folio from `page_folio()` in PFN-scanning loops.

## VMA Flags Modification API

Key distinction: `vm_flags_set()` ORs (adds bits, never clears),
`vm_flags_reset()` replaces (sets to exact value), `vm_flags_init()` replaces
without locking (VMA not yet in tree). `vm_flags_clear()` removes specific
bits. `vm_flags_mod()` adds and removes in one operation. See
`include/linux/mm.h`.

**Common mistake:** `vm_flags_set(vma, new_flags)` to replace flags -- because
it ORs, stale flags silently survive. Use `vm_flags_reset()` for exact
replacement. Stale `VM_WRITE`/`VM_MAYWRITE` creates security holes.

## Realloc Zeroing Lifecycle (`want_init_on_alloc` / `want_init_on_free`)

In-place realloc shrink path must zero `[new_size, old_size)` when
`want_init_on_free()` OR `want_init_on_alloc(flags)` is true. These are
independent settings (`include/linux/mm.h`). Zeroing on `want_init_on_alloc`
during shrink is required because a subsequent in-place grow must not
re-expose stale data.

**Common mistake:** checking only `want_init_on_free()` on shrink -- misses
the `init_on_alloc` case. See `vrealloc_node_align_noprof()` in
`mm/vmalloc.c` and `__do_krealloc()` in `mm/slub.c`.

## Per-CPU LRU Cache Batching

Large folios are never in per-CPU LRU caches (immediately drained on add; see
`__folio_batch_add_and_move()` in `mm/swap.c`). Guard per-folio
`lru_add_drain()` / `lru_add_drain_all()` calls with
`folio_may_be_lru_cached(folio)` (returns `!folio_test_large()`, defined in
`include/linux/swap.h`). See `collect_longterm_unpinnable_folios()` in
`mm/gup.c`.

## Folio Eviction and Invalidation Guards

Removing a folio from page cache without checking dirty/writeback under the
folio lock causes data loss or in-flight IO corruption. Both flags change
asynchronously; checks must be after `folio_lock()`, not before.

**Required pattern** (see `mapping_evict_folio()` in `mm/truncate.c`):
```c
folio_lock(folio);
if (folio_test_dirty(folio) || folio_test_writeback(folio))
	goto skip;
folio_unmap_invalidate(mapping, folio, 0);
```

`folio_unmap_invalidate()` has a late dirty check but does not guard against
writeback, and the folio is already unmapped by that point.

## Folio Migration and Sleeping Constraints

`folio_mc_copy()` in `mm/util.c` calls `cond_resched()` between pages -- safe
for order-0 (loop exits before resched) but sleeps for large folios. This
makes `filemap_migrate_folio()` / `migrate_folio()` / `__migrate_folio()`
sleeping operations for large folios.

**REPORT as bugs**: `migrate_folio` callbacks (in `address_space_operations`)
that hold a spinlock while calling these functions. Use non-blocking state
flags instead (e.g., `BH_Migrate` in `__buffer_migrate_folio()` in
`mm/migrate.c`).

## Trylock-Only Allocation Paths (ALLOC_TRYLOCK)

`alloc_pages_nolock()` / `try_alloc_pages()` set `ALLOC_TRYLOCK` and clear
reclaim GFP flags (`gfpflags_allow_spinning()` returns false). Helpers in
`get_page_from_freelist()` must check `ALLOC_TRYLOCK` or
`gfpflags_allow_spinning()` and skip unconditional locks, or use a coarse
bailout only for **transient** conditions (persistent bailouts permanently
break the path).

**REPORT as bugs**: helpers reachable from `get_page_from_freelist()` using
`spin_lock()` without `ALLOC_TRYLOCK` / `gfpflags_allow_spinning()` checks.

## File Reference Ownership During mmap Callbacks

mmap uses split ownership: `ksys_mmap_pgoff()` holds one file reference
(fput at end), VMA gets its own via `get_file()` in `__mmap_new_file_vma()`.
When a callback replaces the file (`f_op->mmap_prepare()` replacing
`desc->vm_file`, or legacy `f_op->mmap()` replacing `vma->vm_file`), the
replacement already carries its own reference.

**REPORT as bugs**: unconditional `get_file()` on a file that may have been
swapped by a callback -- the replacement gets a leaked extra reference. See
`map->file_doesnt_need_get` in `call_mmap_prepare()` in `mm/vma.c` and
`shmem_zero_setup()` in `mm/shmem.c`.

## Slab Page Overlay Initialization and Cleanup

`struct slab` overlays `struct page`/`struct folio` (verified by `SLAB_MATCH`
assertions in `mm/slab.h`). The page allocator does NOT zero metadata fields,
so `allocate_slab()` in `mm/slub.c` must initialize every field -- especially
conditionally-compiled ones (`CONFIG_*` ifdefs) invisible in most builds.

On free, `slab->obj_exts` shares storage with `folio->memcg_data`. Leftover
sentinel values (e.g., `OBJEXTS_ALLOC_FAIL`) trigger `VM_BUG_ON_FOLIO` or
`free_page_is_bad()`. `free_slab_obj_exts()` in `unaccount_slab()` must be
called unconditionally (not gated on `mem_alloc_profiling_enabled()` or
`memcg_kmem_online()`) because both can change at runtime between alloc and
free. It is idempotent (checks for NULL).

## Folio Isolation for Migration

Not every folio that qualifies for migration is added to the isolation list:
device-coherent folios skip it, `folio_isolate_lru()` can fail, etc.
`collect_longterm_unpinnable_folios()` in `mm/gup.c` returns a count of all
unpinnable folios, not just those listed.

**REPORT as bugs**: using `list_empty()` on a migration list as proxy for
"no qualifying items" when the collection has early-continue paths. Use an
explicit count instead.

## Zone Watermark Initialization Ordering

Zone watermarks are zero until `init_per_zone_wmark_min()` runs as a
`postcore_initcall` (`mm/page_alloc.c`). Before that, `zone_watermark_ok()`
trivially passes, masking the need for reclaim/acceptance. Code reachable
during early boot must handle `wmark == 0` as "not yet initialized" (use a
fallback threshold or unconditionally perform the required work).

## Memblock Range Parameter Conventions

Memblock uses two conventions: `(base, size)` for `memblock_add()`,
`memblock_remove()`, etc., and `(start, end)` for `reserve_bootmem_region()`,
`__memblock_find_range_*()`. Both parameters are `phys_addr_t` -- no compiler
type safety. Common mistake: passing `end` where `size` is expected (or vice
versa) in loops computing both `start = region->base` and
`end = start + region->size`. Check the function's parameter name (`size` vs
`end`) at each call site.

## Folio Order vs Page Count

`round_up()`, `round_down()`, `ALIGN()` require the actual page count
(`1 << order`), not the order exponent. Hard to catch: order 0 and 1 coincide.

```c
// CORRECT                     // WRONG
round_up(index, 1 << order)    round_up(index, order)
ALIGN(addr, PAGE_SIZE << order)
```

**REPORT as bugs**: alignment argument is a raw `order` variable instead of
`1 << order` or `PAGE_SIZE << order`.

## Page Cache XArray Setup (`mapping_set_update`)

Any `XA_STATE` on `mapping->i_pages` that performs mutating xarray operations
must call `mapping_set_update(&xas, mapping)` first (defined in
`mm/internal.h`). This sets callbacks for workingset shadow node tracking
(`workingset_update_node()` in `mm/workingset.c`). Without it, xa_nodes are
not added to their memcg's `list_lru`, leaking nodes under memory pressure.

Main `filemap.c` paths do this correctly. Code outside `filemap.c` operating
on page cache xarray (`collapse_file()` in `mm/khugepaged.c`, shmem paths)
is more likely to omit it.

## Lockless Page Cache Folio Access

Compound-state-dependent folio properties (`folio_mapcount()`,
`folio_nr_pages()`, `folio_order()`, `folio_test_lru()`) under RCU without a
reference race with concurrent split/free. The stabilization protocol (see
`filemap_get_entry()` in `mm/filemap.c`): `folio_try_get(folio)` then
`xas_reload()` to verify the folio is still at the same slot; retry on failure.

No reference needed for: xarray metadata only (`xas_get_mark()`,
`xas_get_order()`), opaque pointer use, or simple flag tests
(`folio_test_dirty()`, `folio_test_writeback()`) that access `folio->flags`
directly without compound branching.

**REPORT as bugs**: `folio_mapcount()`, `folio_nr_pages()`, etc. in
`xas_for_each()` loops under `rcu_read_lock()` without prior
`folio_try_get()` + `xas_reload()`.

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
- **VM_WRITE gate for writable PTEs**: writable PTEs require `VM_WRITE` in
  `vma->vm_flags`. Use `maybe_mkwrite()` (`include/linux/mm.h`). Verify in
  fork/COW, userfaultfd install, and any PTE construction path — VMA
  permissions can change via `mprotect()` between mapping and installation
- **VMA flag and PTE/PMD flag consistency**: clearing a `vm_flags` bit
  (e.g., `VM_UFFD_WP`, `VM_SOFT_DIRTY`) requires clearing the corresponding
  PTE/PMD bits across all forms (present, swap, PTE markers). Error-prone
  when VMA flag clearing and page table walk are in different code paths.
  See `clear_uffd_wp_pmd()` in `mm/huge_memory.c`
- **`flush_tlb_batched_pending()` after PTL re-acquisition**: after dropping
  and re-acquiring PTL, call `flush_tlb_batched_pending(mm)` — reclaim on
  another CPU may have batched TLB flushes while the lock was released.
  See `flush_tlb_batched_pending()` in `mm/rmap.c`
- **Page table removal vs GUP-fast**: clearing a PUD/PMD to free a page
  table page requires `tlb_remove_table_sync_one()` or `tlb_remove_table()`
  before reuse. GUP-fast walks locklessly under `local_irq_save()` and
  can follow stale entries into freed page tables without synchronization.
  See `mm/mmu_gather.c`
- **mmap_lock ordering**: Taking the wrong lock type deadlocks or corrupts the
  VMA tree. Write lock (`mmap_write_lock()`) for VMA structural changes
  (insert/delete/split/merge, modifying vm_flags/vm_page_prot). Read lock
  (`mmap_read_lock()`) for VMA lookup, page fault handling, read-only traversal.
  See the VMA Split/Merge Critical Section above for the finer-grained locking
  within `__split_vma()` and related paths.
  See the "Lock ordering in mm" comment block at the top of `mm/rmap.c`
- **`vma_start_write()` before page table access under `mmap_write_lock`**:
  `mmap_write_lock` does NOT exclude per-VMA lock readers (e.g., madvise
  under `lock_vma_under_rcu()`). Call `vma_start_write(vma)` before
  checking/modifying page tables to drain per-VMA lock holders. See
  `collapse_huge_page()` in `mm/khugepaged.c`
- **Failable mmap lock reacquisition**: `mmap_write_lock_killable()` /
  `mmap_read_lock_killable()` return `-EINTR` on kill. Ignoring the return
  means continuing without the lock. Check in retry loops and lock upgrade
  sequences. See `__get_user_pages_locked()` in `mm/gup.c`
- **Page fault path lock constraints**: `->fault`/`->page_mkwrite` run
  under `mmap_lock`, nested below `i_rwsem` and `sb_start_write`. Fault
  handlers must not wait on freeze protection (ABBA deadlock). Copy user
  data with `copy_folio_from_iter_atomic()` and retry outside the lock.
  See `generic_perform_write()` in `mm/filemap.c`
- **Folio reference before flag tests or mapping**: `folio_test_*()` on
  unreferenced folios crashes if memory was reused as a tail page
  (`const_folio_flags()` asserts not-tail). `folio_try_get()` must precede
  flag tests in speculative lookups; `folio_get()` must precede `set_pte_at()`
- **Compound page tail pages**: page-cache fields (`mapping`, `index`,
  `private`) share a union with `compound_head` in tail pages — accessing
  them on a tail page returns garbage silently. Call `compound_head()` or
  `page_folio()` first. The folio API avoids this entirely
- **`pte_unmap_unlock` pointer must be within the kmap'd PTE page**: After a
  PTE iteration loop, the iterated pointer may point one-past-the-end of the
  PTE page. On `CONFIG_HIGHPTE` systems, `pte_unmap()` calls
  `kunmap_local()`, which derives the page address via `PAGE_MASK`. If the
  pointer crosses a page boundary, it unmaps the wrong page. Save the start
  pointer from `pte_offset_map_lock()` or pass `ptep - 1` after the loop.
  Only triggers on 32-bit HIGHMEM architectures
- **`pte_unmap()` LIFO ordering**: multiple PTE mappings must be unmapped
  in reverse order. Invisible on 64-bit; triggers WARNING on 32-bit HIGHPTE
  where `pte_unmap()` calls `kunmap_local()`
- **`pte_unmap()` must receive the mapped pointer, not a local copy**:
  passing `&orig_pte` (stack copy) instead of `ptep` (mapped pointer) is
  invisible on 64-bit but corrupts the kmap stack on CONFIG_HIGHPTE
- **`pmd_present()` after `pmd_trans_huge_lock()`**: succeeds for both
  present THP PMDs and non-present PMD leaf entries (migration, device-private).
  Must check `pmd_present()` before `pmd_folio()`/`pmd_page()` or any
  function assuming a present PMD
- **Page table state after lock drop and retry**: after dropping and
  reacquiring PTL, concurrent threads may have repopulated empty entries.
  Decisions to free page table structures must be re-validated. See
  `zap_pte_range()` `direct_reclaim` flag in `mm/memory.c` and
  `try_to_free_pte()` in `mm/pt_reclaim.c`
- **VMA merge anon_vma propagation**: merging an unfaulted VMA with a
  faulted one requires `dup_anon_vma()` (see `vma_expand()` in `mm/vma.c`).
  Merge-time `anon_vma` property checks (e.g., `list_is_singular()` in
  `is_mergeable_anon_vma()`) must apply to the VMA that **has** the
  `anon_vma`, not unconditionally to the destination -- the three cases
  (dst unfaulted/src faulted, dst faulted/src unfaulted, both faulted) are
  asymmetric. See `vma_is_fork_child()` in `mm/vma.c`
- **VMA interval tree uses pgoff, not PFN**: `mapping->i_mmap` is keyed by
  `vm_pgoff`; `vma_address()` expects `pgoff_t`. Passing a raw PFN searches
  the wrong coordinate space. **REPORT as bugs**: raw PFN to
  `vma_interval_tree_foreach()` or `vma_address()`
- **Bit-based locking barrier pairing**: when a bit flag is used for mutual
  exclusion (trylock pattern), the unlock must use `clear_bit_unlock()` (release
  semantics), not `clear_bit()` (relaxed, no barrier). The lock side must use
  `test_and_set_bit_lock()` (acquire semantics). Plain `clear_bit()` allows
  stores to be reordered past the unlock on weakly-ordered architectures
  (arm64). MM uses this for `PGDAT_RECLAIM_LOCKED` in `mm/vmscan.c`
- **NUMA node ID validation before `NODE_DATA()`**: `NODE_DATA(nid)` has no
  bounds check. User-provided node IDs need: `nid >= 0 && nid < MAX_NUMNODES
  && node_state(nid, N_MEMORY)`. See `do_pages_move()` in `mm/migrate.c`
- **`get_node(s, numa_mem_id())`** can return NULL on systems with memory-less
  nodes (see `get_node()` and `get_barn()` in `mm/slub.c`). A missing NULL
  check causes a NULL-pointer dereference that only triggers on NUMA systems
  with memory-less nodes
- **Node mask selection for allocation loops**: `for_each_online_node()`
  includes memoryless nodes. Use `for_each_node_state(nid, N_MEMORY)` for
  memory allocation. During early boot, `N_MEMORY` may not be populated yet
  (`free_area_init()` in `mm/mm_init.c` sets it); use memblock ranges instead
- **NUMA node count vs node ID range**: `num_node_state()` returns a count,
  not an upper bound on IDs (IDs can be sparse). Use `nr_node_ids` as the
  upper bound for raw iteration, or `for_each_node_state(nid, N_MEMORY)`
- **`pfn_to_page()` on boundary PFNs**: only safe on PFNs with valid
  `struct page`. Under `CONFIG_SPARSEMEM` without `VMEMMAP`, returns NULL
  for non-existent sections → NULL deref. PFN-range loops must check
  termination before `pfn_to_page()`, not after. Latent on VMEMMAP/FLATMEM
  where it's simple pointer arithmetic
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
- **XArray multi-order entry atomicity**: `xa_get_order()` under
  `rcu_read_lock()` then acting on the order under `xa_lock` is a TOCTOU
  race (entry order can change between operations). Combine `xas_load()`,
  `xas_get_order()`, and `xas_store()` in one `xas_lock_irq()` section.
  **REPORT as bugs**: `xa_get_order()` result used across a lock boundary
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
- **VMA merge/modify error handling**: `vma_modify()`/`vma_merge()` may
  return error or a different VMA. Original VMA may be freed on success.
  On failure, `vmg->start/end/pgoff` may be mutated and not restored —
  save originals or check `vmg_nomem()`. See `madvise_walk_vmas()` in
  `mm/madvise.c`
- **VMA flag ordering vs merging**: flags not in `VM_IGNORE_MERGE` must be
  set in proposed `vm_flags` *before* `vma_merge_new_range()`. Setting
  flags post-merge via `vm_flags_set()` silently breaks future merges
  (`is_mergeable_vma()` XORs flags). See `ksm_vma_flags()` in `mm/ksm.c`
- **VMA merge side effects vs page table operations**: `vma_complete()`
  triggers `uprobe_mmap()` which installs PTEs. Callers that subsequently
  move/overwrite page tables must set `skip_vma_uprobe` in
  `struct vma_merge_struct` (see `mm/vma.h`), or orphaned PTEs leak memory
- **Fork-time VMA flag divergence**: `dup_mmap()` clears `__VM_UFFD_FLAGS`
  and `VM_LOCKED_MASK` on the child VMA. Fork-time flag checks (e.g.,
  `vma_needs_copy()` checking `VM_UFFD_WP`) must use the destination VMA,
  not the source. Combined mask checks must verify all flags have the same
  source-vs-destination semantics
- **Page comparison for zeropage remapping must use `pages_identical()`**:
  raw `memchr_inv()`/`memcmp()` miss architecture metadata. On arm64 MTE,
  byte-identical pages with different tags cause mismatch faults after
  remapping to `ZERO_PAGE(0)`. `pages_identical()` has an arm64 override
  rejecting MTE-tagged pages. **REPORT as bugs**: `memchr_inv()`/`memcmp()`
  for zeropage/merge decisions
- **Large folio size preconditions on hwpoison paths**: `unmap_poisoned_folio()`
  cannot handle large non-hugetlb folios. Callers must check
  `folio_test_large() && !folio_test_hugetlb()` and split before calling.
  `memory_failure()` handles this via `try_to_split_thp_page()` first
- **NUMA mempolicy-aware vs node-specific allocation**: `alloc_pages_node()`
  / `__alloc_pages_node()` bypass task NUMA policy (`mbind()`,
  `set_mempolicy()`). Replacing `alloc_pages()` / `folio_alloc()` with
  `_node` variants silently drops mempolicy — invisible in testing, pages
  land on wrong nodes. Branch: mempolicy-aware for `NUMA_NO_NODE`,
  node-specific for explicit node. See `___kmalloc_large_node()` in
  `mm/slub.c`
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
- **Hugetlb page cache insertion protocol**: before
  `hugetlb_add_to_page_cache()`: zero with `folio_zero_user()`, mark
  uptodate with `__folio_mark_uptodate()`, hold
  `hugetlb_fault_mutex_table[hash]`. Not enforced by the function itself.
  See `hugetlbfs_fallocate()` in `fs/hugetlbfs/inode.c`
- **VM_ACCOUNT preservation during VMA manipulation**: clearing `VM_ACCOUNT`
  on a surviving VMA (e.g., `MREMAP_DONTUNMAP`, partial unmap) leaks
  committed memory permanently — `do_vmi_munmap()` only uncharges VMAs
  with `VM_ACCOUNT`. Review `vm_flags_clear()` calls including `VM_ACCOUNT`
- **Kernel page table population synchronization**: `pgd_populate()` /
  `p4d_populate()` do NOT sync to other processes' kernel page tables. Use
  `pgd_populate_kernel()` / `p4d_populate_kernel()` which call
  `arch_sync_kernel_mappings()`. Affects vmemmap, percpu, KASAN shadow
- **SLUB `!allow_spin` retry loops**: in `___slab_alloc()` (`mm/slub.c`),
  `goto` back to retry after a trylock failure must check `!allow_spin`
  and return NULL. Trylock can fail deterministically (caller interrupted
  holder on same CPU), creating an infinite loop without a bail-out
- **KASAN tag reset in SLUB internals**: new `mm/slub.c` code accessing freed
  object memory (freelist linking, metadata) must call `kasan_reset_tag()`
  first. `kasan_slab_free()` poisons with a new tag; the old-tagged pointer
  triggers false use-after-free on ARM64 MTE. `set_freepointer()`/
  `get_freepointer()` handle this; generic helpers like `llist_add()` do not
- **`__GFP_MOVABLE` mobility contract**: pages allocated with
  `__GFP_MOVABLE` MUST be reclaimable or migratable. Common mistake:
  `movable_operations` registered conditionally (`#ifdef CONFIG_COMPACTION`)
  while `__GFP_MOVABLE` passed unconditionally. **REPORT as bugs**:
  `__GFP_MOVABLE` on pages with no migration support
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
- **PFN advancement after page-to-folio conversion**: `folio_nr_pages()`
  is wrong for advancing PFN when starting from a tail page. Use
  `pfn += folio_nr_pages(folio) - folio_page_idx(folio, page) - 1`. See
  `isolate_migratepages_block()` in `mm/compaction.c`
- **Compound page metadata after potential refcount drop**: reading
  `compound_order()`/`folio_nr_pages()` after a call that may drop the last
  reference returns garbage (page may be freed). Snapshot metadata before
  the refcount-dropping call. See `isolate_migratepages_block()` in
  `mm/compaction.c`
- **Lazy MMU mode pairing and hazards**: (1) PTE reads after writes inside
  lazy mode may return stale data — bracket with leave/enter. (2) Error
  paths must not skip `arch_leave_lazy_mmu_mode()` — use `break` not
  `return`. No-op on most configs; bugs only manifest on Xen PV, sparc,
  powerpc book3s64, arm64
- **Pageblock migratetype updates for high-order pages**: use
  `change_pageblock_range()` not bare `set_pageblock_migratetype()` for
  `order >= pageblock_order`. The bare function only updates the first
  pageblock; remaining ones keep stale migratetypes, causing freelist
  mismatches
- **Non-present PTE swap entry type dispatch**: see the full section in
  PTE State Consistency above. Verify each dispatch branch accepts only
  semantically matching entry types — do not group device-exclusive with
  migration despite both having PFNs
- **Per-section metadata iteration across large folios**: under
  `CONFIG_SPARSEMEM`, `page_ext` arrays are per-section, not contiguous.
  Pointer arithmetic across section boundaries crashes. Use
  `for_each_page_ext()` / `page_ext_iter_next()` which re-derive via
  `page_ext_lookup()` at crossings
- **`page_folio()` / `compound_head()` require vmemmap-resident pages**:
  `page_fixed_fake_head()` accesses `page[1].compound_head` under
  `CONFIG_HUGETLB_PAGE_OPTIMIZE_VMEMMAP`. Calling on a stack-local or
  single-element copy is an OOB read. For page snapshots, open-code the
  `compound_head` bit-test instead. See `snapshot_page()` in `mm/util.c`
- **VMA iteration on external mm_struct**: call
  `check_stable_address_space(mm)` after mmap lock, before traversal.
  `dup_mmap()` adds mm to `mmlist` before copying VMAs; on failure, slots
  contain `XA_ZERO_ENTRY` markers (`MMF_UNSTABLE`). OOM reaper also sets
  `MMF_UNSTABLE`. See `unuse_mm()` in `mm/swapfile.c`
- **`walk_page_range()` default skips `VM_PFNMAP` VMAs**: without
  `.test_walk`, default `walk_page_test()` skips `VM_PFNMAP` silently.
  Callers needing all VMAs must provide `.test_walk` returning 0. A 0
  return from `walk_page_range()` may mean "skipped", not "handled"
- **`ACTION_AGAIN` in page walk callbacks**: `ACTION_AGAIN` retries with
  no limit. `pte_offset_map_lock()` returns NULL non-transiently for
  migration entries — setting `ACTION_AGAIN` on this failure creates an
  infinite loop. Return 0 to skip gracefully. `walk_pte_range()` already
  handles retry internally; callbacks should not duplicate it
- **Page allocator retry-loop termination**: every `goto retry` in
  `__alloc_pages_slowpath()` must modify state preventing the same path
  next iteration (clear flag, set bool, use bounded function). Without a
  guard, infinite loop prevents OOM killer. Verify `&= ~FLAG` not `&= FLAG`
- **Page allocator retry vs restart seqcount consistency**: `retry` reuses
  cached `ac->preferred_zoneref`; external state (cpuset nodemask,
  zonelists) can change. Every `goto retry` must call
  `check_retry_cpuset()` / `check_retry_zonelist()` to redirect to
  `restart` when stale. Otherwise allocator loops on stale zone iteration

- **Maple state RCU lifetime**: `ma_state` caches RCU-protected node
  pointers. After `rcu_read_unlock()`, invalidate with `mas_set()` or
  `mas_reset()` before reuse. Easy to miss when `vma_start_read()` drops
  RCU internally on failure. See `lock_vma_under_rcu()` in `mm/mmap_lock.c`
- **mTHP order-fallback index alignment**: compute alignment into a
  temporary, not in-place on the original index. `round_down(index,
  larger_pages)` destroys info for subsequent smaller-order iterations.
  See `shmem_alloc_and_add_folio()` in `mm/shmem.c`
- **List iteration with lock drop**: `list_for_each_entry_safe` is not safe
  when the lock is dropped mid-iteration. Concurrent `list_del_init()` makes
  the element self-referential → infinite loop. After reacquiring, check
  `list_empty()` and restart from head. See `shmem_unuse()` in `mm/shmem.c`
- **`static_branch_*()` on allocation paths**: these acquire
  `cpus_read_lock()` internally. Calling from page allocator during CPU
  bringup deadlocks (bringup holds `cpu_hotplug_lock` for write). Use
  `_cpuslocked` variants or defer via `schedule_work()`
- **Early boot use of MM globals**: `high_memory` and zone PFNs are zero
  until `free_area_init()`. Use `memblock_end_of_DRAM()` instead of
  `__pa(high_memory)` in `__init` code. Guard `high_memory` with
  `IS_ENABLED(CONFIG_HIGHMEM)`. See `mm/cma.c`
- **Lazy MMU mode implies possible atomic context**: disables preemption
  on some architectures (sparc, powerpc). `pte_fn_t` callbacks and PTE
  loops inside lazy MMU mode must not sleep. Allocations need
  `GFP_ATOMIC`/`GFP_NOWAIT` or pre-allocation. Invisible on x86/arm64
- **NOWAIT error code translation**: NOWAIT callers expect `-EAGAIN` (retry
  in blocking context), not `-ENOMEM` (fatal). When downgrading GFP to
  NOWAIT, translate allocation failure to `-EAGAIN`. See
  `__filemap_get_folio_mpol()` `FGP_NOWAIT` in `mm/filemap.c`
- **Bounded iteration under LRU locks**: skipping LRU entries without
  advancing the termination counter creates unbounded spinlock-held scans.
  Skip paths must either advance the counter or have an independent bound
  (e.g., `SWAP_CLUSTER_MAX_SKIPPED`). Applies to any spinlock-held list
  filtering loop
- **`folio_page()` vs PTE-mapped subpage**: `folio_page(folio, 0)` returns the
  head page, not the subpage a specific PTE maps. In PTE batch loops within a
  large folio, use `vm_normal_page()` for the actual subpage unless the batch
  starts at folio offset 0. Per-page state checks (e.g., `PageAnonExclusive`)
  on the wrong subpage yield wrong results
- **Migration lock scope across unmap and remap phases**: if
  `TTU_RMAP_LOCKED` is passed to `try_to_migrate()`, `i_mmap_rwsem` must
  stay held until `remove_migration_ptes()` with `RMP_LOCKED`. Dropping
  between phases creates ABBA deadlock (`folio_lock` → `i_mmap_rwsem` vs
  reverse). Anon vs file-backed use different locks — fixes for one may
  break the other. See `unmap_and_move_huge_page()` in `mm/migrate.c`
- **`try_to_unmap()` on PMD-mapped large folios**: requires
  `TTU_SPLIT_HUGE_PMD` flag, otherwise `VM_BUG_ON(!pvmw.pte)` fires in
  `try_to_unmap_one()`. Wrappers like `unmap_poisoned_folio()` do NOT set
  this flag — callers must guarantee not a large folio (except hugetlb)
- **`folio_page()` index bounds**: `folio_page(folio, n)` does unchecked
  arithmetic; `n >= folio_nr_pages(folio)` accesses past the struct page array.
  When `n` is computed from byte-offset arithmetic in truncation/split paths,
  verify boundary cases don't produce a one-past-the-end index
- **kswapd order-dropping and watermark checks**: `kswapd_shrink_node()`
  drops `sc->order` to 0 after reclaiming `compact_gap(order)` pages. Watermark
  checks in `pgdat_balanced()`/`balance_pgdat()` that use stricter high-order
  metrics must check `order != 0`, not a static mode flag. Ignoring the
  dynamic order drop causes massive overreclaim
- **Hugetlb subpool reservation rollback**: `hugepage_subpool_get_pages()`
  absorbs some pages from `rsv_hpages` and returns smaller `gbl_reserve`.
  Error paths must return `chg - gbl_reserve` (not `chg`) to
  `hugepage_subpool_put_pages()`, and feed its return to
  `hugetlb_acct_memory()`. Over-crediting causes `resv_huge_pages` underflow
- **Large folio mapcount field consistency**: `_large_mapcount`,
  `_entire_mapcount`, per-page `_mapcount`, `_nr_pages_mapped` are updated
  non-atomically in rmap operations. Reading multiple fields requires
  `folio_lock_large_mapcount()` for a consistent snapshot. See
  `__wp_can_reuse_large_anon_folio()` in `mm/memory.c`: optimistic check,
  lock, recheck, act
- **Folio order vs mapping entry order**: swapin paths must verify
  `folio_order()` matches the mapping entry order. Readahead can insert
  order-0 folios for slots covered by a large mapping entry; inserting
  without splitting the large entry silently loses data. See
  `shmem_split_large_entry()` in `mm/shmem.c`
- **`folio_end_read()` on already-uptodate folios**: uses XOR for
  `PG_uptodate`, so calling with `success=true` on an already-uptodate folio
  toggles the flag off. Paths that may encounter uptodate folios must use
  `folio_unlock()` instead
- **Refcount as semantic state**: `page_count()`/`folio_ref_count()` are
  lifetime counters, not semantic indicators. Speculative references (GUP,
  memory-failure, page_idle) transiently inflate them. Use dedicated
  counters/flags for semantic state (`PageAnonExclusive`, `pt_share_count`).
  Flag code branching on refcount == specific value for non-lifetime logic
- **`folio_putback_lru()` requires valid memcg**: after
  `mem_cgroup_migrate()` clears the source folio's `memcg_data`,
  `folio_putback_lru()` triggers a memcg assert. Use plain `folio_put()`
  for the source folio. See `migrate_folio_move()` in `mm/migrate.c`
- **`pmd_trans_huge()` matches both THP and hugetlb PMDs**: check
  `is_vm_hugetlb_page(vma)` first before THP-specific operations
  (`split_huge_pmd()`, `pgtable_trans_huge_withdraw()`). Hugetlb uses
  different page table layout, locking, and splitting semantics. Same
  ambiguity at PUD level
- **Swap allocator local lock scope**: `folio_alloc_swap()` runs under
  `local_lock()` (preemption disabled). No sleeping operations reachable
  from this scope. Drop the lock for sleeping ops. Silent in typical testing;
  fires under `CONFIG_DEBUG_PREEMPT` or PREEMPT_RT
- **Slab freelist pointer access must use accessors**: with
  `CONFIG_SLAB_FREELIST_HARDENED`, freelist pointers are XOR-encoded. Raw
  writes (`*(void **)ptr = NULL`) store un-encoded values that decode to
  garbage. Use `get_freepointer()` / `set_freepointer()` for all access
- **Writeback dirty limit dual-parameter ordering**: `vm_dirty_bytes` vs
  `vm_dirty_ratio` are mutually exclusive; bytes takes priority when
  non-zero. Switching to ratio mode must zero bytes *before*
  `writeback_set_ratelimit()`. See `dirty_ratio_handler()` in
  `mm/page-writeback.c`
- **Hugetlb HPG flag propagation during demotion**: `init_new_hugetlb_folio()`
  does NOT propagate HPG flags from `folio->private`. Allocation-origin flags
  like `HPG_cma` control the deallocation path (CMA vs buddy). Code creating
  new hugetlb folios from an existing one must explicitly copy these flags.
  See `demote_free_hugetlb_folios()` in `mm/hugetlb.c`
- **Page allocator fallback cost in batched paths**: `rmqueue_bulk()` calls
  `__rmqueue()` in a loop under `zone->lock` with IRQs off. Fallback changes
  multiply across every page in the batch, causing latency spikes.
  `enum rmqueue_mode` caches failed levels across iterations. Evaluate any
  `__rmqueue_claim()`/`__rmqueue_steal()` change for per-iteration cost
- **Large folio boundary spanning in PFN iteration**: large folios crossing
  sub-range boundaries are seen in multiple sub-ranges. Without dedup,
  actions apply multiple times (double pageout, inflated stats). Track
  last-processed folio or advance by `folio_size()`. See `last_applied` in
  `struct damos`
- **Hugetlb folio rejection in generic folio paths**: generic rmap/migration
  callbacks that only handle PTE-level folios must reject hugetlb early via
  `folio_test_hugetlb()`. Hugetlb requires distinct PTE ops, rmap functions,
  RSS accounting, and locking. Compare `try_to_unmap_one()`/
  `try_to_migrate_one()` in `mm/rmap.c` (full hugetlb branches) against new
  callbacks
- **`arch_sync_kernel_mappings()` on error paths**: loops that accumulate
  `pgtbl_mod_mask` and call `arch_sync_kernel_mappings()` after must use
  `break` (not `return`) on errors. Early `return` skips the sync, leaving
  other processes' kernel page tables stale. See `__apply_to_page_range()`
  and `vmap_range_noflush()`
- **Page-count accounting in folio conversions**: when converting
  single-page code to large-folio, every `counter++` and hardcoded `1` for
  "pages processed" must become `folio_nr_pages(folio)`. Common mistake:
  updating most sites but missing one, causing undercounting for large folios
- **User page zeroing on cache-aliasing architectures**: `__GFP_ZERO` uses
  `clear_page()` which skips the dcache flush that `clear_user_highpage()`/
  `folio_zero_user()` provides. On cache-aliasing architectures, user-mapped
  pages need the flush. Use `user_alloc_needs_zeroing()` to check. Any
  optimization replacing `clear_user_highpage()` with `__GFP_ZERO` is wrong
  on these architectures
- **Memfd file creation API layering**: calling `shmem_file_setup()` or
  `hugetlb_file_setup()` directly for memfd produces files missing
  `O_LARGEFILE`, fmode flags, and security init. Use `memfd_alloc_file()`.
  **REPORT as bugs**: memfd creation via direct `shmem_file_setup()` /
  `hugetlb_file_setup()` (non-memfd callers like DRM/SGX/SysV are fine)
- **`kmap_local_page()` maps only a single page**: on CONFIG_HIGHMEM,
  accessing beyond `PAGE_SIZE` from the returned address faults — adjacent
  pages in a high-order allocation are not mapped. Silent on 64-bit (direct
  map is contiguous). For multi-page access, iterate with
  `kmap_local_page(page + i)`. `kmap_local_folio()` also maps one page only
- **Direct map restore before page free**: when a page has been removed from
  the kernel direct map (via `set_direct_map_invalid_noflush()` in
  `include/linux/set_memory.h`), the direct map entry must be restored with
  `set_direct_map_default_noflush()` before the page is freed back to the
  allocator. Freeing first creates a window where another task allocates the
  page and faults via the still-invalid direct map. See `secretmem_fault()`
  and `secretmem_free_folio()` in `mm/secretmem.c`
- **`folio->mapping` NULL for non-anonymous folios**: `folio->mapping` is
  NULL for shmem folios in swap cache and for truncated folios. Code that
  branches on `!folio_test_anon()` then dereferences `folio->mapping` will
  NULL-deref on these. NULL-check before accessing mapping members
- **Memory hotplug lock for kernel page table walks**: walking `init_mm`
  page tables needs `get_online_mems()` / `put_online_mems()`, not just
  `mmap_lock`. Hot-remove frees intermediate PUDs/PMDs for direct-map and
  vmemmap ranges, causing use-after-free in concurrent walkers. Acquire
  hotplug lock before `mmap_lock` for ordering
- **Mapcount symmetry for non-present PTE entries**: non-present swap PTEs
  holding a folio reference (device-private, device-exclusive, migration) must
  keep mapcount symmetric: if mapcount is maintained during creation, teardown
  (`zap_nonpresent_ptes()`) must remove it. Device-private/exclusive maintain
  mapcount; migration entries are managed by `try_to_migrate_one()` itself
- **VMA operation results assigned to struct members**: `vma_merge_extend()`,
  `vma_merge_new_range()`, `copy_vma()` return NULL on failure. Assigning
  directly to a struct member (e.g., `vrm->vma = vma_merge_extend(...)`)
  clobbers the original VMA pointer before the NULL check. Assign to a local
  first, NULL-check, then update the struct member on success
- **Large folio split failure in truncation**: successful split unmaps the
  PMD mapping, causing refaults as PTEs that enforce SIGBUS beyond `i_size`.
  If split fails and PMD is preserved, beyond-`i_size` accesses won't SIGBUS.
  Must explicitly unmap on split failure (see `try_folio_split_or_unmap()`).
  Exception: shmem allows PMD mappings across `i_size`
- **Counter-gated tracking list removal**: list membership gated by a
  resource counter (e.g., `shmem_swaplist` requires `info->swapped > 0`).
  Error paths must check the counter before `list_del_init()` — the object
  may already be on the list from a prior operation. Unconditional removal
  causes iterators to loop forever unable to find remaining resources
- **Zone skip criteria consistency in vmscan**: zone-skip logic must be
  consistent across `balance_pgdat()`, `pgdat_balanced()`,
  `allow_direct_reclaim()`, and `skip_throttle_noprogress()`. If one counts a
  zone another skips, `kswapd_failures` escape hatch may never fire, causing
  infinite loops in `throttle_direct_reclaim()`
- **Slab post-alloc/free hook symmetry**: `slab_post_alloc_hook()` runs
  KASAN, kmemleak, KMSAN, alloc tagging, and memcg hooks. When a late hook
  fails, the error-free path must undo all that already ran. Compare any
  specialized free/abort path against `slab_free()` for the required hook
  sequence
- **Memory failure accounting consistency**: `action_result()` updates
  `num_poisoned_pages` (global) and `memory_failure_stats` (per-node)
  together. Calling `num_poisoned_pages_inc()` without
  `update_per_node_mf_stats()` causes `/proc/meminfo` vs sysfs inconsistency
- **VMA lock vs mmap_lock assertions**: `mmap_assert_locked(mm)` fires when
  only a VMA lock is held. Paths reachable under per-VMA locks must use
  `vma_assert_locked(vma)` (accepts either VMA lock or mmap_lock). Legacy
  `mmap_assert_locked()` in page table walk/zap paths is likely incorrect
- **GFP_KERNEL under locks in reclaim-reachable paths**: `GFP_KERNEL` can
  trigger direct reclaim, re-entering MM through swap-out, writeback, or slab
  shrinking. Deadlock if the allocation holds a lock reclaim also acquires.
  Move allocations outside the critical section or use `GFP_NOWAIT`/`GFP_ATOMIC`
- **Page table walker iterator advancement**: in `do { } while` page table
  loops, advance the pointer unconditionally in the `while` clause (e.g.,
  `} while (pte++, addr += PAGE_SIZE, addr != end)`), not inside a
  conditional body. Use `continue` to skip entries so `while` still advances.
  Placing `ptr++` inside an `if` stalls the walker when false
- **VMA addresses used as boolean flags**: `vm_start` can legitimately be
  zero, so `if (addr_var)` to mean "was this set" silently fails for
  zero-address VMAs. Use an explicit `bool` flag or direct comparisons.
  Same for any `unsigned long` address/offset that can be zero
- **KASAN granule alignment in vmalloc poison/unpoison**: `kasan_poison()`/
  `kasan_unpoison()` require `KASAN_GRANULE_SIZE`-aligned addresses. In
  realloc paths, `vm->requested_size` is arbitrary — passing `p + old_size`
  directly triggers splats. Use `kasan_vrealloc()` which handles partial
  granule boundaries. Code outside `mm/kasan/` passing non-aligned addresses
  to `kasan_poison_vmalloc()` / `kasan_unpoison_vmalloc()` is a bug
- **`mm_struct` flexible array sizing**: trailing flexible array packs
  cpumask and mm_cid regions. Static definitions (`init_mm`, `efi_mm`) must
  use `MM_STRUCT_FLEXIBLE_ARRAY_INIT`. Adding a new region requires updating
  `mm_cache_init()` (dynamic), `MM_STRUCT_FLEXIBLE_ARRAY_INIT` (static), and
  all static `mm_struct` definitions
- **PCP locking wrapper requirement**: `pcp->lock` must use PCP-specific
  wrappers (`pcp_spin_trylock()`, `pcp_spin_lock_maybe_irqsave()`), not bare
  `spin_lock()`. On `CONFIG_SMP=n`, `spin_trylock()` is a no-op; the PCP
  wrappers add `local_irq_save()`/`local_irq_restore()` to prevent IRQ
  reentrancy. Bare `spin_lock()` allows IRQ handler corruption of PCP lists
- **VMA merge functions invalidate input on success**: `vma_merge_new_range()`,
  `vma_merge_existing_range()`, `vma_modify()` may free the original VMA on
  success. Callers must use the returned VMA, not the original. Discarding the
  return value and using the original is use-after-free
- **`vma_modify*()` error returns in VMA iteration loops**: `vma_modify_flags()`
  etc. return `ERR_PTR(-ENOMEM)` on merge/split failure. Assigning back to a
  VMA loop variable without `IS_ERR()` check dereferences the error pointer.
  Even when the merge is best-effort (VMA unchanged on failure), the error
  return corrupts iteration. Check `IS_ERR()` or use `give_up_on_oom`
- **Page/folio access after failed refcount drop**: when
  `put_page_testzero()`/`folio_put_testzero()` returns false, the caller has
  no reference — another CPU may free the page immediately. Any access after
  the failed testzero is use-after-free. Save needed metadata (flags, order,
  tags) **before** the refcount drop. See `___free_pages()` for the pattern
- **PTE batch loop bounds**: loops batching consecutive PTEs must not rely
  solely on `pte_same()` against a synthetic expected PTE. On XEN PV,
  `pte_advance_pfn()` can produce `pte_none()` for PFNs without valid
  machine frames, causing false matches and overrunning the folio. Bound
  iteration independently using folio metadata (`folio_nr_pages()` etc.)
- **SLUB bulk free staging buffer flush**: `free_to_pcs_bulk()` destructively
  moves objects from the caller's array to a staging buffer (`p[i] = p[--size]`).
  The staging buffer becomes the only reference. Every exit path must flush it
  if `remote_nr > 0` — missing a flush is a permanent leak. Same principle for
  any bulk free that destructively partitions objects
- **VMA lock refcount balance on error paths**: `__vma_enter_locked()` adds
  `VMA_LOCK_OFFSET` to `vm_refcnt` then waits for readers. When using
  `TASK_KILLABLE`/`TASK_INTERRUPTIBLE`, the `-EINTR` path must subtract the
  offset back. Leaked offset permanently blocks VMA detach/free. Hazard
  introduced when converting waits to killable variants
- **`pte_offset_map`/`pte_unmap` pairing**: `pte_unmap()` must receive the
  exact pointer from `pte_offset_map()`, never a pointer to a local `pte_t`
  copy. Both are `pte_t *` so the compiler won't warn. On `CONFIG_HIGHPTE`,
  passing a stack address to `pte_unmap()` unmaps the wrong mapping. Common
  mistake: `pte_t orig = ptep_get(pte)` then `pte_unmap(&orig)`

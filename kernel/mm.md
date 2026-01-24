# Memory Management Subsystem Delta

## Memory Management Patterns [MM]

#### MM-001: PTE state consistency

**Risk**: Invalid states

**Details**: Clean+Writable, Non-accessed+Writable are invalid

#### MM-002: Cross-page state handling

**Risk**: Wrong page attrs

**Details**: A/D bits must match target page, not source

#### MM-003: Migration state expectations

**Risk**: System crash

**Details**: Migration/NUMA/swap expect valid PTE combinations

#### MM-004: Large folio per-page handling

**Risk**: Data corruption

**Details**: PageAnonExclusive/dirty/accessed per page

#### MM-005: Writeback tag preservation

**Risk**: Sync violations

**Details**: folio_start_writeback() clears TOWRITE tag

## Page/Folio States
- PTE dirty bit implies accessed bit (dirty→accessed)
- Young/accessed pages shouldn't be clean and writable simultaneously
- Large folios require per-page state tracking for:
  - PageAnonExclusive
  - Dirty/accessed bits
  - Reference counts

## GFP Flags Context

**GFP_ATOMIC**
: **Sleeps**: No
: **Reclaim**: No
: **Use Case**: IRQ/spinlock context

**GFP_KERNEL**
: **Sleeps**: Yes
: **Reclaim**: Yes
: **Use Case**: Normal allocation

**GFP_NOWAIT**
: **Sleeps**: No
: **Reclaim**: No
: **Use Case**: Non-sleeping, may fail

**GFP_NOFS**
: **Sleeps**: Yes
: **Reclaim**: Limited
: **Use Case**: Avoid FS recursion

## __GFP_ACCOUNT

- slabs created with SLAB_ACCOUNT implicitly have __GFP_ACCOUNT on every allocation

**Mandatory memcg accounting validation:**
- step 1: when using __GFP_ACCOUNT, ensure the correct memcg is charged
  - old = set_active_memcg(memcg) ; work ; set_active_memcg(old)
- step 2: most usage does not need set_active_memcg(), but:
  - kthreads switching context between many memcgs may need it
  - helpers operating on objects (e.g., BPF maps) with stored memcg may need it
- step 3: ensure new __GFP_ACCOUNT usage is consistent with surrounding code

## Migration Invariants
- Migration entries must maintain PTE state consistency
- NUMA balancing expects valid PTE combinations
- Swap code has strict PTE state requirements

## Writeback Tags
- PAGECACHE_TAG_TOWRITE cleared by folio_start_writeback()
- Use __folio_start_writeback(folio, true) to preserve
- Tags affect sync_file_range() behavior

## Mempool Allocation Guarantees

`mempool_alloc()` cannot fail when `__GFP_DIRECT_RECLAIM` is set - it sleeps
and retries forever until success (`mm/mempool.c:mempool_alloc_noprof()`).

**GFP flags with `__GFP_DIRECT_RECLAIM`**: GFP_KERNEL, GFP_NOIO, GFP_NOFS
(all include `__GFP_RECLAIM` = `__GFP_DIRECT_RECLAIM | __GFP_KSWAPD_RECLAIM`)

**Can fail**: GFP_ATOMIC, GFP_NOWAIT (no `__GFP_DIRECT_RECLAIM`)

## Quick Checks
- TLB flushes required after PTE modifications
- mmap_lock ordering (read vs write)
- Page reference before mapping operations
- Compound page tail page handling
- get_node(XXX, numa_mem_id()) can return NULL on memory-less nodes

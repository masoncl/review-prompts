# Memory Management Subsystem Delta

## Memory Management Patterns [MM]

| Pattern ID | Check | Risk | Details |
|------------|-------|------|---------|
| MM-001 | PTE state consistency | Invalid states | Clean+Writable, Non-accessed+Writable are invalid |
| MM-002 | Cross-page state handling | Wrong page attrs | A/D bits must match target page, not source |
| MM-003 | Migration state expectations | System crash | Migration/NUMA/swap expect valid PTE combinations |
| MM-004 | Large folio per-page handling | Data corruption | PageAnonExclusive/dirty/accessed per page |
| MM-005 | Writeback tag preservation | Sync violations | folio_start_writeback() clears TOWRITE tag |

## Page/Folio States
- PTE dirty bit implies accessed bit (dirty→accessed)
- Young/accessed pages shouldn't be clean and writable simultaneously
- Large folios require per-page state tracking for:
  - PageAnonExclusive
  - Dirty/accessed bits
  - Reference counts

## GFP Flags Context
| Flag | Sleeps | Reclaim | Use Case |
|------|--------|---------|----------|
| GFP_ATOMIC | No | No | IRQ/spinlock context |
| GFP_KERNEL | Yes | Yes | Normal allocation |
| GFP_NOWAIT | No | No | Non-sleeping, may fail |
| GFP_NOFS | Yes | Limited | Avoid FS recursion |

## Migration Invariants
- Migration entries must maintain PTE state consistency
- NUMA balancing expects valid PTE combinations
- Swap code has strict PTE state requirements

## Writeback Tags
- PAGECACHE_TAG_TOWRITE cleared by folio_start_writeback()
- Use __folio_start_writeback(folio, true) to preserve
- Tags affect sync_file_range() behavior

## Quick Checks
- TLB flushes required after PTE modifications
- mmap_lock ordering (read vs write)
- Page reference before mapping operations
- Compound page tail page handling

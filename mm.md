# Memory Management Patterns

| Pattern | Check | Risk | Details |
|---------|-------|------|---------|
| **Resource Lifecycle** | Map all alloc→cleanup paths | Memory leak | Verify no early returns bypass cleanup |
| **PTE State Consistency** | No mixing A/D bits between pages | Invalid states | Clean+Writable, Non-accessed+Writable are invalid |
| **Cross-Page State** | Verify pte_advance_pfn() preserves correct state | Wrong page attrs | A/D bits must match target page, not source |
| **Migration Impact** | Check downstream subsystems handle new PTE states | System crash | Migration/NUMA/swap expect valid PTE combinations |
| **Large Folio Batching** | Per-page state handled individually | Data corruption | PageAnonExclusive/dirty/accessed per page |
| **Writeback Side Effects** | folio_start_writeback() clears TOWRITE tag | Sync violations | Use __folio_start_writeback(folio, true) to preserve |
| **Reference Counting** | Balance get/put operations | Use-after-free | Check all error paths for proper cleanup |

## Critical Invariants
- PTE state combinations must be logically possible
- Write permission requires dirty+accessed bits
- Batch operations can't mix state between different pages
- Page cache tags affect sync operation ordering
- Migration code has strict PTE state expectations

## Validation
1. Trace 2+ concrete examples through batching logic
2. Verify all downstream MM subsystems handle new states
3. Check reference counting in error paths
4. Validate PTE state transitions are possible
5. Ensure per-page metadata not shared incorrectly

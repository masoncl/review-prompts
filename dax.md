# DAX Patterns

| Pattern | Check | Risk |
|---------|-------|------|
| **Memory Mapping** | Verify pfn valid and within device range | Invalid access |
| **Cache Coherency** | Flush CPU caches at appropriate points | Data corruption |
| **Locking Order** | Follow VFS→DAX→device locking hierarchy | Deadlock |

## Quick Checks
- PFN validation before mapping
- Cache flush on persistence points
- Lock ordering compliance
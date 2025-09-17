# Tracing Patterns

| Pattern | Check | Risk |
|---------|-------|------|
| **Tracepoint Safety** | No sleeping/blocking in tracepoint handlers | Deadlock |
| **Data Access** | Validate pointers before dereferencing in trace | Crash |
| **String Safety** | Use strncpy_from_user() for user strings | Overflow |

## Quick Checks
- Atomic context restrictions
- NULL pointer validation
- String length limits
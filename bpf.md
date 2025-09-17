# BPF Patterns

| Pattern | Check | Risk |
|---------|-------|------|
| **Verifier State** | Check bounds, alignment, NULL checks | Runtime crash |
| **Helper Functions** | Validate context types match helper requirements | Type confusion |
| **Map Operations** | Verify key/value sizes and lookup error handling | Buffer overflow |
| **Program Types** | Context access must match program type restrictions | Invalid access |
| **Reference Tracking** | Balance acquire/release of references | Leak/UAF |

## Quick Checks
- Pointer arithmetic stays within valid bounds
- Helper ARG_PTR_TO_CTX matches actual context
- Map lookups check for NULL return
- Program type allows requested context fields
- References released in all paths
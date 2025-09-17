# Fscrypt Patterns

| Pattern | Check | Risk |
|---------|-------|------|
| **Key Lifecycle** | Verify key available before crypto ops | Crash/corruption |
| **Context Inheritance** | Child inherits parent encryption context | Data exposure |
| **Policy Validation** | Check policy compatibility before application | Invalid state |
| **Filename Encryption** | Handle encrypted name length limits | Buffer overflow |

## Quick Checks
- Key loaded before file access
- Directory encryption context propagated
- Policy version compatibility
- Encrypted filename fits in NAME_MAX
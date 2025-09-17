# VFS Patterns

| Pattern | Check | Risk |
|---------|-------|------|
| **Inode Locking** | Directory ops need inode_lock_nested(dir, I_MUTEX_PARENT) | Deadlock |
| **Dentry Lifecycle** | d_instantiate() only on negative dentries | Corruption |
| **Permission Checks** | may_open() before file access | Security bypass |
| **Path Walking** | Hold appropriate locks during traversal | Race conditions |
| **File Operations** | Check file->f_op != NULL before use | NULL deref |

## Quick Checks
- Parent directory locking for create/delete ops
- Dentry state before instantiation
- Permission validation timing
- RCU vs ref-walk mode handling

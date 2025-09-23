# VFS Subsystem Delta

## VFS Patterns [VFS]

| Pattern ID | Check | Risk | Details |
|------------|-------|------|---------|
| VFS-001 | Directory locking hierarchy | Deadlock | Use inode_lock_nested(dir, I_MUTEX_PARENT) |
| VFS-002 | Dentry instantiation | Corruption | d_instantiate() only on negative dentries |
| VFS-003 | Permission check timing | Security bypass | may_open() before file access |
| VFS-004 | File ops NULL check | NULL deref | Check file->f_op != NULL before use |

## Inode Locking Hierarchy
- Parent → Child ordering for directory operations
- I_MUTEX_PARENT for parent directory locks
- Rename requires locks on both parents

## Dentry States
- Negative dentry: d_inode == NULL
- Positive dentry: d_inode != NULL
- Only instantiate negative dentries

## Path Walking Modes
- RCU-walk: Lockless, can fail and retry
- REF-walk: Takes references, always succeeds
- Transitions from RCU to REF on conflict

## File Operations
- file->f_op can be NULL for special files
- file_operations reassignment needs synchronization
- Private_data lifetime tied to file lifetime

## Quick Checks
- inode->i_rwsem for file size/data modifications
- sb->s_umount for superblock operations
- Proper dget/dput for dentry references
- Permission checks before operations (may_open, inode_permission)

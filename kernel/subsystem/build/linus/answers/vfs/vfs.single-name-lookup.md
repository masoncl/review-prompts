- `lookup_one()` and `lookup_noperm()`: the caller holds
  `base->d_inode->i_rwsem`; both open with
  `WARN_ON_ONCE(!inode_is_locked(base->d_inode))`.
- `inode_is_locked()`: is `rwsem_is_locked()`, so a shared hold satisfies it,
  and so does a hold by any other task.
- Shared hold: enough for `lookup_one()` and `lookup_noperm()`; they fall back
  to `__lookup_slow()`, the same function `lookup_slow()` runs under
  `inode_lock_shared()`.
- `lookup_one_positive_killable()`: checks permission, is called unlocked,
  on a dcache miss takes the lock shared with a killable wait, returns
  `ERR_PTR(-EINTR)` if killed and `ERR_PTR(-ENOENT)` for a negative dentry.
- `try_lookup_noperm()`: after `lookup_noperm_common()` it calls `d_lookup()`
  only; it does not revalidate and never calls `->lookup`. The other forms
  revalidate through `lookup_dcache()`.
- `lookup_one_qstr_excl()`: `static` in `fs/namei.c`; no name validation, no
  hashing, no permission check, no lock assertion; the caller holds the lock
  exclusive and passes a hashed name.
- `start_dirop()`: the lock-and-lookup wrapper around
  `lookup_one_qstr_excl()`; declared in `fs/internal.h` and not exported.
  Other code uses the helpers in "Create and remove start helpers".
- lookup_one_len() and its variants: not defined in this tree; every form
  takes a `struct qstr *`.

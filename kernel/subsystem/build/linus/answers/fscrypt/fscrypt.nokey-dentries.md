- `fscrypt_d_revalidate()` on a no-key dentry with `LOOKUP_RCU`: returns
  `-ECHILD` before it looks at the key, whether or not the key was added.
- `fscrypt_d_revalidate()` on a no-key dentry in ref-walk: calls
  `fscrypt_get_encryption_info(dir, true)` before it tests the key, so it sets
  up the directory's key itself; a negative result is returned as is.
- `fscrypt_d_revalidate()` uses its `dir` argument; it does not take the parent
  from the dentry.
- `__fscrypt_prepare_lookup()`: calls `fscrypt_prepare_dentry()` with
  `fname->is_nokey_name` when `fscrypt_setup_filename()` returns 0 or `-ENOENT`;
  on any other error it returns without calling `fscrypt_prepare_dentry()`.
- `fscrypt_prepare_dentry()`: changes only `d_flags`; it never installs dentry
  operations.
- There is no generic_set_encrypted_ci_d_ops() here; `generic_set_sb_d_ops()`
  in `fs/libfs.c` calls `set_default_d_op()`, which sets `__s_d_op` and
  `s_d_flags` in `struct super_block`.
- `generic_set_sb_d_ops()`: tests `sb->s_encoding` and then `sb->s_cop` at the
  time of the call, and installs nothing if both are unset.
- Order at mount in ext4, f2fs and ubifs: `sb->s_cop` is set first (directly or
  with `fscrypt_set_ops()`), then `generic_set_sb_d_ops()`, then the root dentry
  is allocated; `__d_alloc()` copies `__s_d_op` and `s_d_flags` into each new
  dentry.
- `DCACHE_NOKEY_NAME` is also set outside `fscrypt_prepare_dentry()`:
  `ceph_fill_trace()` and `ceph_readdir_prepopulate()` in `fs/ceph/inode.c` set
  it directly, under `d_lock`, on dentries they allocate.

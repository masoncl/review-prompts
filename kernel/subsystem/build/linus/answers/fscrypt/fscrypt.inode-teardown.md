- `fscrypt_put_encryption_info()`: frees the whole
  `struct fscrypt_inode_info` through `put_crypt_info()` and sets the pointer
  to NULL.
- `fscrypt_free_inode()`: frees only `inode->i_link`, and only when
  `IS_ENCRYPTED(inode) && S_ISLNK(inode->i_mode)` holds at the time of the
  call.
- Which inodes: every inode the filesystem evicts; ext4, f2fs, ubifs and ceph
  call it with no test of the inode.
- `s_cop`: `fscrypt_put_encryption_info()` dereferences it with no NULL test,
  so `s_cop` must be set on every superblock whose inodes reach the call.
  Without `CONFIG_FS_ENCRYPTION` both functions are empty stubs.
- The reset to NULL is relied on: ext4 sets `i_crypt_info` to NULL only in
  the slab constructor `init_once()`, so a reused object is clean only
  because eviction cleared it.
- `make_bad_inode()` sets `i_mode` to `S_IFREG`; a later
  `fscrypt_free_inode()` then skips the `kfree()` of `i_link`.
- **Potentially unsafe usage**: calling `fscrypt_free_inode()` outside
  `->free_inode()`.
  - Unsafe: once the inode has been reachable by path walk; `fs/namei.c`
    reads `inode->i_link` in RCU mode, so the free needs the grace period that
    `->free_inode()` provides.
  - Safe: on a new symlink that was never hashed or instantiated, as the error
    path of `ubifs_symlink()` does; the function sets `i_link` to NULL, so
    the later call from `->free_inode()` does nothing.

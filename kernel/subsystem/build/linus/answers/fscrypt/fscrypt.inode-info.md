- `fscrypt_inode_info_addr()` in `include/linux/fscrypt.h`: the one helper
  that turns an inode into the address of the pointer;
  `fscrypt_get_inode_info()`, `fscrypt_get_inode_info_raw()`,
  `fscrypt_setup_encryption_info()` and `fscrypt_put_encryption_info()` go
  through it.
- `inode_info_offs` of 0: means "not set". In ext4, f2fs, ubifs and ceph the
  `i_crypt_info` field follows the embedded inode, so the offset is positive.
- `VFS_WARN_ON_ONCE()` on a zero offset: compiled out without
  `CONFIG_DEBUG_VFS`; the address is then the start of the `struct inode`.
- `s_cop`: `fscrypt_inode_info_addr()` dereferences `inode->i_sb->s_cop` with
  no NULL test, so no accessor may be used on a superblock that did not set
  `s_cop`.
- Initialising the field to NULL is the filesystem's job: ext4 does it in the
  slab constructor `init_once()`; f2fs has no slab constructor and calls its
  `init_once()` from `f2fs_alloc_inode()` at every allocation; ubifs does it
  by `memset()` in `ubifs_alloc_inode()`, ceph in `ceph_alloc_inode()`.

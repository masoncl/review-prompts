- `fscrypt_get_inode_info()` and `fscrypt_get_inode_info_raw()`: this tree has
  both, in `include/linux/fscrypt.h`.
- `fscrypt_get_inode_info_raw()` warning on NULL: `VFS_WARN_ON_ONCE()`,
  compiled out without `CONFIG_DEBUG_VFS`; the NULL is then returned
  silently, and callers that make no test of their own dereference it.
- Without `CONFIG_FS_ENCRYPTION`: `fscrypt_get_inode_info()` has a stub that
  returns NULL; `fscrypt_get_inode_info_raw()` and
  `fscrypt_inode_info_addr()` have no stub.
- Callers of `fscrypt_get_inode_info_raw()`: all are in `fs/crypto/`.
  Filesystems test for a key with `fscrypt_has_encryption_key()`.
- Exported helpers that use the raw accessor pass its requirement to the
  filesystem, for example `fscrypt_fname_encrypt()`,
  `fscrypt_fname_encrypted_size()`, `fscrypt_fname_siphash()` and
  `fscrypt_encrypt_block_inplace()`.
- Pointer lifetime: once non-NULL it stays set until
  `fscrypt_put_encryption_info()` at eviction, the only place in `fs/crypto/`
  that clears it.
- **Potentially unsafe usage**: calling `fscrypt_get_inode_info_raw()`.
  - Unsafe: when nothing earlier on the calling path has seen the pointer
    non-NULL, or to test whether a key exists; callers such as
    `fscrypt_fname_encrypt()` dereference the result at once.
  - Safe: after the same task got success from `fscrypt_require_key()` on an
    `IS_ENCRYPTED()` inode, or true from `fscrypt_has_encryption_key()`, both
    of which do the acquire load; `fscrypt_policy_to_inherit()` and
    `fscrypt_setup_filename()` do this, the latter on a directory.
  - Safe: on a new inode after `fscrypt_prepare_new_inode()` returned 0 with
    `*encrypt_ret` true in the same task, as `fscrypt_set_context()` does
    when `__ext4_new_inode()` calls it.
  - Safe: in file contents I/O on an encrypted regular file, where
    `fscrypt_file_open()` required the key, as
    `fscrypt_encrypt_pagecache_blocks()` and `fscrypt_set_bio_crypt_ctx()`
    do.

- Returns 1 without comparing, besides an unencrypted parent and a child that
  is not a regular file, directory or symlink: when parent and child are both
  encrypted and `fscrypt_get_policy()` returns `-EINVAL` for both
  (unrecognized context version or size); this lets such files be deleted.
- Any error from `fscrypt_get_encryption_info()`, any other error from
  `fscrypt_get_policy()`, or `-EINVAL` for only one of the two: returns 0.
- Recognized version with unsupported modes or flags: not the `-EINVAL` case;
  the two policies are compared with `fscrypt_policies_equal()`.
- Without `CONFIG_FS_ENCRYPTION`: the stub in `include/linux/fscrypt.h`
  returns 0 for every pair.
- Link: `__fscrypt_prepare_link()` returns `-EXDEV`, not `-EPERM`.
- Link and rename: the filesystem calls `fscrypt_prepare_link()` and
  `fscrypt_prepare_rename()`, never `fscrypt_has_permitted_context()`
  directly.
- Rename within one directory: not checked; `__fscrypt_prepare_rename()`
  compares only when `old_dir != new_dir`.
- Lookup: `__fscrypt_prepare_lookup()` in `fs/crypto/hooks.c` does not call
  it; the filesystem's lookup method does, as in `ext4_lookup()`,
  `f2fs_lookup()` and `ubifs_lookup()`.
- Lookup check in `ext4_lookup()`, `f2fs_lookup()` and `ubifs_lookup()`: made
  only when `IS_ENCRYPTED(dir)` and the child is a directory or symlink;
  failure gives `-EPERM`.
- Regular files: not checked by those lookup methods; `fscrypt_file_open()`,
  which the filesystem calls from its open method or, in ubifs, installs as
  `->open`, checks them against the parent of the dentry used to open.

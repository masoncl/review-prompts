- `fscrypt_setup_filename()` with `lookup` 0: returns `-ENOKEY` only while the
  directory has no key; once the key was added after the lookup it succeeds and
  encrypts the no-key string as if it were a plaintext name.
- `ext4_add_entry()`: tests `fscrypt_is_nokey_name()` and returns `-ENOKEY`
  before it calls `__ext4_add_entry()`.
- ubifs: the test is in `ubifs_prepare_create()` in `fs/ubifs/dir.c`, which its
  create methods call, for example `ubifs_create()`.
- The two tests can differ: flag set and key present, when the key was added
  after the lookup.
- `fscrypt_has_encryption_key()`: tests only that the inode's
  `struct fscrypt_inode_info` pointer is non-NULL; fs/crypto clears that
  pointer only in `fscrypt_put_encryption_info()`.
- `__fscrypt_prepare_link()` and `__fscrypt_prepare_rename()`: after the flag
  test they make no key test of the directory.
- **Potentially unsafe usage**: a method that adds a name for a dentry that
  came from lookup, and calls `fscrypt_setup_filename()` with `lookup` 0 or
  tests `fscrypt_has_encryption_key()` on the directory.
  - Unsafe: when the directory can be encrypted and nothing earlier on the path
    tested `fscrypt_is_nokey_name()` on that dentry; if the key was added after
    the lookup, `fscrypt_setup_filename()` encrypts the no-key string as a
    plaintext name.
  - Safe: test `fscrypt_is_nokey_name()` first and return `-ENOKEY`, as
    `ext4_add_entry()`, `f2fs_add_link()` and `ubifs_prepare_create()` do; the
    flag is the one `fscrypt_prepare_dentry()` set at lookup.
  - Safe: after `fscrypt_prepare_link()` or `fscrypt_prepare_rename()` returned
    0 for an encrypted directory, as in `ubifs_link()` and `ubifs_rename()`;
    `__fscrypt_prepare_link()` and `__fscrypt_prepare_rename()` test the flag.
  - Safe: on a filesystem that never sets `S_ENCRYPTED`, as
    `btrfs_new_inode_prepare()` in `fs/btrfs/inode.c`;
    `fscrypt_setup_filename()` returns at its `IS_ENCRYPTED()` test.

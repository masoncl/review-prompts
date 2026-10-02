- `is_block_based`: bit field in `struct fscrypt_operations`
  (`include/linux/fscrypt.h`) that selects the data path; set by
  `ext4_cryptops` and `f2fs_cryptops`, not by ubifs or ceph.
- `needs_bounce_pages`: set only by `ceph_fscrypt_ops` in `fs/ceph/crypto.c`;
  `ext4_cryptops` and `f2fs_cryptops` do not set it.
- Attaching: ubifs and ceph call `fscrypt_set_ops()`; ext4 and f2fs assign
  `sb->s_cop` directly under `#ifdef CONFIG_FS_ENCRYPTION`, because the field
  exists only then.
- There is no fscrypt_set_test_dummy_encryption() here; see
  `fscrypt_parse_test_dummy_encryption()`.

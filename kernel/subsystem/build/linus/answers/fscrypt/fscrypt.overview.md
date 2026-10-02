- Filesystems that set a `struct fscrypt_operations`: ext4, f2fs, ubifs and
  ceph only; search for `inode_info_offs` to list them.
- Contents encryption path is fixed per filesystem by flags in
  `struct fscrypt_operations`, not chosen per mount or per inode:

  | Filesystem flag | Regular-file key | Contents I/O |
  |---|---|---|
  | `is_block_based` (ext4, f2fs) | `blk_key` | blk-crypto, via `fscrypt_set_bio_crypt_ctx()` in `fs/crypto/block.c` |
  | `needs_bounce_pages` (ceph) | `tfm` | `fscrypt_encrypt_pagecache_blocks()` and the in-place helpers |
  | neither (ubifs) | `tfm` | `fscrypt_encrypt_block_inplace()`, `fscrypt_decrypt_block_inplace()` |

- Bounce page pool: one global pool; `fscrypt_initialize()` creates it only
  when `needs_bounce_pages` is set; `fscrypt_alloc_bounce_page()` warns and
  returns NULL while no pool exists.
- Directories and symlinks: always use `tfm`, on every filesystem.
- `struct fscrypt_inode_info` pointer: not a member of `struct inode`; it lives
  in the filesystem's own inode (`i_crypt_info` in `struct ext4_inode_info`,
  for example) and fscrypt finds it with `inode_info_offs` through
  `fscrypt_inode_info_addr()` in `include/linux/fscrypt.h`.
- `ci_master_key`: NULL when a v1 key came from the process-subscribed
  keyrings; such an inode holds no active ref, is not on
  `mk_decrypted_inodes`, and `fscrypt_drop_inode()` returns 0 for it.
- v2 inode info: `ci_master_key` is set by the time the
  `fscrypt_setup_encryption_info()` call that published it returns, since
  `setup_file_encryption_key()` returns `-ENOKEY` for v2 when the key is not
  in `s_master_keys`.
- v1 master keys: also live in `s_master_keys` when added with
  `FS_IOC_ADD_ENCRYPTION_KEY` and a descriptor (`CAP_SYS_ADMIN`);
  `setup_file_encryption_key()` searches there first and falls back to
  `fscrypt_setup_v1_file_key_via_subscribed_keyrings()`.
- `struct fscrypt_prepared_key`: `tfm` is a `struct crypto_sync_skcipher *`;
  `fscrypt_prepare_key()` sets exactly one of `tfm` and `blk_key`, never both.
- `ci_enc_key`: an embedded `struct fscrypt_prepared_key`; for a shared key it
  is a by-value copy of the owner's struct; `ci_owns_key` says whether the
  inode info frees it. Owners:

  | Policy | Owner of the key | Freed by |
  |---|---|---|
  | per-file key (v1 or v2, no key-sharing flag) | the inode info | `put_crypt_info()` |
  | v2 with `FSCRYPT_POLICY_FLAG_DIRECT_KEY`, `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64` or `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32` | a `struct fscrypt_mode_key` on `mk_mode_keys` | `fscrypt_put_master_key_activeref()`, on the last active ref |
  | v1 with `FSCRYPT_POLICY_FLAG_DIRECT_KEY` | a `struct fscrypt_direct_key` (`ci_direct_key`) | `fscrypt_put_direct_key()` |

- Shared mode keys: kept alive by the inode's active ref on the master key, not
  by a refcount of their own.
- `struct fscrypt_direct_key`: wraps a `struct fscrypt_prepared_key`
  (`dk_key`), so it may hold a `blk_key`; it sits in the global table
  `fscrypt_direct_keys` in `fs/crypto/keysetup_v1.c`, has its own
  `dk_refcount`, and is matched per superblock (`dk_sb`).
- `struct fscrypt_mode`: one entry per mode number in `fscrypt_modes[]`, not a
  contents/filenames pair; `select_encryption_mode()` in
  `fs/crypto/keysetup.c` picks the contents mode for regular files and the
  filenames mode for directories and symlinks.
- `struct fscrypt_dummy_policy`: inherited only by new regular files,
  directories and symlinks created under an unencrypted directory
  (`fscrypt_policy_to_inherit()`, `fscrypt_prepare_new_inode()`); existing
  inodes are untouched.

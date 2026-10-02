- `fscrypt_using_inline_encryption()` in `fs/crypto/fscrypt_private.h`: the
  whole test is `S_ISREG(inode->i_mode) && inode->i_sb->s_cop->is_block_based`.
- There is no fscrypt_select_encryption_impl(), no ci_inlinecrypt field and no
  fs/crypto/inline_crypt.c here; the blk-crypto code is `fs/crypto/block.c`.
- Regular files on a block-based filesystem: always blk-crypto, with or without
  the inlinecrypt mount option; fs/crypto has no crypto API contents path for
  them.
- Regular file on ext4 or f2fs: always gets a `blk_key` and `tfm` stays NULL,
  whatever the mount options.
- `SB_INLINECRYPT` is not part of the test; `fscrypt_prepare_inline_crypt_key()`
  turns it into `BLK_CRYPTO_CFG_ALLOW_HW` for `blk_crypto_init_key()`.
- Without `BLK_CRYPTO_CFG_ALLOW_HW`: `blk_crypto_config_supported_natively()`
  returns false, so blk-crypto-fallback does every bio in software.
- Device capability never selects between blk-crypto and the crypto API in
  fs/crypto; with `BLK_CRYPTO_CFG_ALLOW_HW` and a raw key it only selects
  hardware or blk-crypto-fallback. There is no blk_crypto_config_supported()
  here.
- `blk_crypto_start_using_key()` failure: fails key setup; there is no fall
  back to `fscrypt_allocate_skcipher()`.
- `blk_crypto_mode` unset in a `struct fscrypt_mode`: not tested by fs/crypto;
  for a raw key `blk_crypto_init_key()` returns `-EINVAL` for the key size.
- `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64` and `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32`:
  no hardware requirement; see `supported_iv_ino_lblk_policy()` in
  `fs/crypto/policy.c`.
- Hardware-wrapped keys, regular file: `setup_per_mode_enc_key()` calls
  `fscrypt_prepare_inline_crypt_key()` directly, not `fscrypt_prepare_key()`;
  `-EINVAL` without `SB_INLINECRYPT`.
- `get_devices` unset: `fscrypt_get_devices()` uses `sb->s_bdev`; it is not a
  condition.
- There is no fscrypt_inode_uses_inline_crypto() or
  fscrypt_inode_uses_fs_layer_crypto() here; filesystem code does not test the
  path.
- `CONFIG_FS_ENCRYPTION_INLINE_CRYPT`: no prompt, `default y if FS_ENCRYPTION &&
  BLOCK`; `CONFIG_FS_ENCRYPTION` selects `BLK_INLINE_ENCRYPTION` and
  `BLK_INLINE_ENCRYPTION_FALLBACK` if `BLOCK` (`fs/crypto/Kconfig`).

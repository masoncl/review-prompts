- Shared keys: kept as `struct fscrypt_mode_key` nodes on the list
  `mk_mode_keys` in `struct fscrypt_master_key`
  (`fs/crypto/fscrypt_private.h`), one list for all three flags.
- There are no per-flag arrays here: mk_direct_keys, mk_iv_ino_lblk_64_keys,
  mk_iv_ino_lblk_32_keys and FSCRYPT_MODE_MAX are not defined in this tree.
- Node identity: `fscrypt_find_mode_key()` matches `hkdf_context`,
  `mode_num`, `data_unit_bits` and the prepared form (`blk_key` or `tfm`,
  via `fscrypt_is_key_prepared()`).
- One master key under one flag can therefore own several nodes with the
  same raw key bytes; for example `FSCRYPT_POLICY_FLAG_DIRECT_KEY` on ext4
  gets one `blk_key` node for regular files and one `tfm` node for
  directories and symlinks.
- `setup_per_mode_enc_key()` in `fs/crypto/keysetup.c`: derives and appends
  the node under `fscrypt_mode_key_setup_mutex`; there is no
  fscrypt_setup_per_mode_enc_key(), fscrypt_get_derived_key(),
  setup_mode_prepared_key() or mk_prepared_keys_lock.
- `fscrypt_find_mode_key()`: returns a pointer into the node with no
  reference taken; safe only because the caller holds `mk_sem` for read with
  `mk_present` true, as `setup_file_encryption_key()` does, which keeps the
  list append-only.
- Hardware-wrapped master key, regular file: `setup_per_mode_enc_key()`
  skips HKDF and passes `mk_secret.bytes` to
  `fscrypt_prepare_inline_crypt_key()` with `is_hw_wrapped` true.
- Hardware-wrapped master key, directory or symlink: the per-mode key is
  still HKDF-derived, with HKDF keyed by the software secret from
  `fscrypt_derive_sw_secret()`.
- `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32`: the HKDF info includes `sb->s_uuid`,
  the same as `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64`; only
  `FSCRYPT_POLICY_FLAG_DIRECT_KEY` passes `include_fs_uuid` false.
- `FSCRYPT_POLICY_FLAG_DIRECT_KEY`: `supported_direct_key_modes()` requires
  equal contents and filenames modes, and the only such pair that
  `fscrypt_valid_enc_modes_v1()` or `fscrypt_valid_enc_modes_v2()` accepts
  is `FSCRYPT_MODE_ADIANTUM`; `FSCRYPT_MODE_AES_256_HCTR2` never qualifies.
- `fscrypt_put_master_key()`: drops only a structural reference and frees
  the struct through `call_rcu()`; it destroys no mode key.

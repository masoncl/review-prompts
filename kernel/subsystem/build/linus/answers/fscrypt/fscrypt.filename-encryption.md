- `fname->is_nokey_name`: set to true for every no-key lookup, before the name
  is decoded, so it is also true when `fscrypt_setup_filename()` returns
  `-ENOENT`; `__fscrypt_prepare_lookup()` reads it after `-ENOENT`.
- `fname->hash` and `fname->minor_hash`: filled from `dirhash[]` for every
  decoded no-key name, short or long.
- `fname->disk_name` in a no-key lookup: points at `bytes` inside `crypto_buf`
  for the short form; stays NULL with length 0 when the decoded length equals
  `FSCRYPT_NOKEY_NAME_MAX`.
- `-ENAMETOOLONG`: returned only when the plaintext length exceeds `NAME_MAX`.
- Padded length above the maximum: `__fscrypt_fname_encrypted_size()` clamps it
  to the maximum, so a ciphertext name can have a length that is not a
  multiple of the policy's padding.
- Maximum length: `fscrypt_setup_filename()` passes the constant `NAME_MAX`, not
  a per-filesystem limit; a filesystem tests its own limit itself, as
  `ubifs_lookup()` does with `UBIFS_MAX_NLEN`.
- IV: `fscrypt_generate_iv()` in `fs/crypto/crypto.c` is called with index 0 and
  the directory's `struct fscrypt_inode_info`; the `union fscrypt_iv` is all
  zero when the policy has none of the three flags below.

| Policy flag, tested in this order | IV for a filename |
|---|---|
| `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64` | index holds the directory's `i_ino` in its upper 32 bits |
| `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32` | index is `ci_hashed_ino` |
| `FSCRYPT_POLICY_FLAG_DIRECT_KEY` | index 0, and `ci_nonce` copied into the IV |

- Filename modes: the accepted set is in `fscrypt_valid_enc_modes_v1()` and
  `fscrypt_valid_enc_modes_v2()` in `fs/crypto/policy.c`; it includes
  `FSCRYPT_MODE_AES_128_CTS` and `FSCRYPT_MODE_SM4_CTS`.

- `setup_v1_file_key_derived()` in `fs/crypto/keysetup_v1.c`: does the
  derivation inline; there is no derive_key_aes() in this tree.
- Crypto interface: the AES library, not the skcipher API;
  `aes_prepareenckey()` keys a stack `struct aes_enckey`, then
  `aes_encrypt()` runs once per 16-byte block.
- No transform is allocated, so the derivation itself has no allocation or
  `-ENOPKG` failure; errors come only from the size check and from
  `fscrypt_set_per_file_enc_key()`.
- Roles: the file nonce `ci_nonce` is the AES-128 key; the first
  `ci_mode->keysize` bytes of the master key are the plaintext.
- `keysize` not a multiple of `AES_BLOCK_SIZE`, or above
  `FSCRYPT_MAX_RAW_KEY_SIZE`: `WARN_ON_ONCE()` and `-EINVAL`.
- Derived key buffer: on the stack, wiped with `memzero_explicit()`; the
  `struct aes_enckey` is not wiped because the nonce is not secret.
- Master key lookup order: `setup_file_encryption_key()` in
  `fs/crypto/keysetup.c` searches `s_master_keys` first and calls
  `fscrypt_setup_v1_file_key()` with `mk_secret.bytes`.
- `fscrypt_setup_v1_file_key_via_subscribed_keyrings()`: runs only when that
  search finds nothing; it, not `fscrypt_setup_v1_file_key()`, calls
  `find_and_lock_process_key()`.
- `find_or_insert_direct_key()`: reuses a `struct fscrypt_direct_key` only
  if descriptor, `dk_sb`, `dk_mode`, the prepared form and the raw key
  (`crypto_memneq()`) all match.

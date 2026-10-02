- Models allocate transforms with a zero mask. `fscrypt_allocate_skcipher()`
  passes `FSCRYPT_CRYPTOAPI_MASK`, which excludes async, memory-allocating
  and driver-only implementations.
- Models take the secret bytes to be sized by `FSCRYPT_MAX_KEY_SIZE`.
  `fs/crypto/fscrypt_private.h` undefines `FSCRYPT_MAX_KEY_SIZE`, so use
  `FSCRYPT_MAX_RAW_KEY_SIZE` or `FSCRYPT_MAX_ANY_KEY_SIZE`.
- Models take `i_ino` to be `unsigned long`. It is `u64` in `struct inode`,
  so `fs/crypto/` prints it with `%llu`; the 32-bit inode number limit for
  `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64` and
  `FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32` policies comes from
  `has_32bit_inodes`, tested in `supported_iv_ino_lblk_policy()`, not from
  the type.

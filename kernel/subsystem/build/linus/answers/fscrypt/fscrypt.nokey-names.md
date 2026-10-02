- `struct fscrypt_nokey_name`: defined in `fs/crypto/fname.c`, not in a header.
- There is no FSCRYPT_FNAME_MAX_UNDIGESTED_SIZE here; the 149-byte limit is the
  array size of `bytes`, written as `sizeof(nokey_name.bytes)`.
- There is no fscrypt_base64url_encode() here; `fscrypt_fname_disk_to_usr()`
  calls `base64_encode()` and `fscrypt_setup_filename()` calls
  `base64_decode()`, both in `lib/base64.c`, with `BASE64_URLSAFE` and `padding`
  false.
- `dirhash[]`: always the first 8 bytes of what `fscrypt_fname_disk_to_usr()`
  encodes, for every caller and for short names too, so a no-key name from it
  is never the encoding of the bare ciphertext.
- `dirhash[]` is zero when the caller passes 0 for `hash` and `minor_hash`, as
  `fscrypt_get_symlink()` does.
- `fscrypt_match_name()`: chooses its branch on `fname->disk_name.name` being
  non-NULL, not on `is_nokey_name`; a short no-key name takes the plain
  compare.
- `fscrypt_match_name()` reads only `disk_name` and `crypto_buf`;
  `ext4_match()` and `f2fs_match_name()` pass it a `struct fscrypt_name` on the
  stack with only `usr_fname`, `disk_name` and `crypto_buf` filled in.
- ubifs does not call `fscrypt_match_name()`: when `disk_name.name` is NULL,
  `ubifs_lookup()` finds the entry with `nm.hash` and `nm.minor_hash` through
  `ubifs_tnc_lookup_dh()`.
- ubifs `minor_hash`: the entry's `cookie`, which `ubifs_readdir()` passes to
  `fscrypt_fname_disk_to_usr()`.

- Block-based filesystems make no fs/crypto call after a read completes; the
  bio's crypt context is the only fscrypt involvement.
- There is no fscrypt_decrypt_pagecache_blocks(), fscrypt_decrypt_bio(),
  fscrypt_enqueue_decrypt_work() or fscrypt_read_workqueue here; `fscrypt_init()`
  creates no workqueue.
- Software decryption: `blk_crypto_fallback_bio_prep()` in
  `block/blk-crypto-fallback.c` wraps `bi_end_io`; the work runs on
  `blk_crypto_wq`.
- Filesystem `bi_end_io` after fallback decryption: called from the
  `blk_crypto_wq` worker by `blk_crypto_fallback_decrypt_bio()`; on an I/O error
  it is called straight from `blk_crypto_fallback_decrypt_endio()`.
- Decryption failure: reaches the filesystem only as `bio->bi_status`.
- `fs/ext4/readpage.c`: has no `struct bio_post_read_ctx`; only
  `struct ext4_verity_work`, queued by `mpage_end_io()`.
- `fs/f2fs/data.c`: `enum bio_post_read_step` has `STEP_DECOMPRESS` and
  `STEP_VERITY` only.

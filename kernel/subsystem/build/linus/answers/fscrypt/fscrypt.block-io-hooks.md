- Position unit: `fscrypt_set_bio_crypt_ctx()`, `fscrypt_mergeable_bio()` and
  `fscrypt_zeroout_range()` take `loff_t pos` in bytes; `fscrypt_zeroout_range()`
  also takes `len` in bytes. A block number passed as `pos` gives a wrong DUN
  silently: `fscrypt_generate_dun()` only shifts it by `ci_data_unit_bits`.
- `fscrypt_limit_io_blocks()`: still takes `lblk` and `nr_blocks` in filesystem
  blocks.
- There is no fscrypt_set_bio_crypt_ctx_bh() or fscrypt_mergeable_bio_bh() here;
  buffer-head code passes `folio_pos() + bh_offset()`, as
  `buffer_set_crypto_ctx()` in `fs/buffer.c` does.
- `fscrypt_set_bio_crypt_ctx()`: tests only
  `fscrypt_needs_contents_encryption()`, then reads `ci_enc_key.blk_key` through
  `fscrypt_get_inode_info_raw()`; the key must already be set up.
- Writes on ext4 and f2fs: no `fscrypt_encrypt_pagecache_blocks()` call; ext4
  puts the pagecache folio into the bio, in `io_submit_add_bh()`.
- Bios that move raw ciphertext carry no context: `f2fs_set_bio_crypt_ctx()`
  skips the call when `fio->encrypted_page` is set.
- Segment not aligned to the data unit size: `bio_split_io_at()` returns
  `-EINVAL`; blk-crypto-fallback ends the bio with `BLK_STS_INVAL`.
- **Unsafe usage**: submitting a bio that has a crypt context with
  `submit_bio()`.
  - Unsafe: `submit_bio_noacct()` ends it with `BLK_STS_NOTSUPP` unless
    `blk_crypto_supported()`, which is always false without `SB_INLINECRYPT`.
  - Safe: `blk_crypto_submit_bio()`, as `ext4_io_submit()` does;
    `__blk_crypto_submit_bio()` hands the bio to blk-crypto-fallback when the
    device has no native support.
  - Safe: a `submit_io` hook in `struct iomap_dio_ops` that calls
    `blk_crypto_submit_bio()`, as `f2fs_dio_read_submit_io()` does;
    `iomap_dio_submit_bio()` does not call it when the hook is set.
- **Unsafe usage**: passing `fscrypt_set_bio_crypt_ctx()` a `gfp_mask` without
  `__GFP_DIRECT_RECLAIM`.
  - Unsafe: `bio_crypt_set_ctx()` warns and dereferences the `mempool_alloc()`
    result unchecked.
  - Safe: `GFP_NOIO`, as `io_submit_init_bio()` in `fs/ext4/page-io.c` passes.

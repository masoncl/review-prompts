- There is no fscrypt_dio_supported() here, and nothing in fs/crypto decides;
  each filesystem tests alignment itself.
- inlinecrypt is not a condition: neither `ext4_dio_alignment()` nor
  `f2fs_force_buffered_io()` tests `SB_INLINECRYPT` or refuses a file for being
  encrypted.
- ext4: `ext4_dio_alignment()` returns `i_blocksize()` for `IS_ENCRYPTED()`;
  `ext4_should_use_dio()` falls back to buffered I/O when misaligned, with no
  error.
- f2fs: `f2fs_force_buffered_io()` has no encryption test;
  `f2fs_should_use_dio()` applies the block-size rule to every file.
- f2fs misaligned I/O: buffered fallback when aligned to the device logical
  block size; otherwise direct I/O is attempted, and `iomap_dio_bio_iter()`
  returns `-EINVAL` for a position or length not aligned to the logical block
  size.
- `iomap_dio_read_simple()` in `include/linux/iomap.h`: returns `-ENOTBLK` for
  `IS_ENCRYPTED()`; `__iomap_dio_read_simple()` sets no crypt context and uses
  `submit_bio()` or `submit_bio_wait()`.
- `fscrypt_set_bio_crypt_ctx()` callers in `fs/iomap/direct-io.c`:
  `iomap_dio_bio_iter_one()` and `iomap_dio_zero()`, with the byte `pos`.
- `fscrypt_limit_io_blocks()`: not called in `fs/iomap/`; `ext4_iomap_begin()`
  and `f2fs_iomap_begin()` call it.

- Bits 0 to 43 are all defined; the highest is
  `FUSE_HAS_IO_URING_BUFPOOL`.
- A flag at bit 32 or above is defined as the full value `(1ULL << n)`,
  not relative to `flags2`; `fuse_new_init()` and `process_init_reply()`
  do the shift by 32.
- State that `fs/fuse/dev.c` needs: add it to `struct fuse_chan_param` and
  set it in `fuse_chan_set_initialized()`, as `io_uring_enabled` is.
- **Potentially unsafe usage**: enabling a feature in
  `process_init_reply()` whose flag `fuse_new_init()` offers only under a
  condition.
  - Unsafe: when nothing tests the condition again;
    `process_init_reply()` does not mask the reply with the offered flags,
    so a server can set a bit the kernel never sent.
  - Safe: test the condition again at the reply, as `FUSE_PASSTHROUGH` does
    with `IS_ENABLED(CONFIG_FUSE_PASSTHROUGH)` and `FUSE_OVER_IO_URING`
    with `fuse_uring_enabled()`.
  - Safe: when every user of the bit tests the condition first, as
    `fuse_should_enable_dax()` tests `fc->dax_mode` and `fc->dax` before
    `fc->inode_dax`.

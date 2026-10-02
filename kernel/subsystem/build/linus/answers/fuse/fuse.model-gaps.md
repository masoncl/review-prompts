- Models take ring commands to need a ring set up with 128-byte entries.
  `io_uring_cmd()` in `io_uring/uring_cmd.c` also sets `IO_URING_F_SQE128`
  for opcode `IORING_OP_URING_CMD128`.
- Models treat `in_args[]` as an unordered list. On the ring path
  `fuse_uring_args_to_ring()` copies `in_args[0]` to the `op_in` header and
  only the rest to the payload; a request with no per-op header calls
  `fuse_set_zero_arg0()` first, as `fuse_lookup_init()` does.
- Models take READDIR to use one page. `fuse_readdir_uncached()` sizes the
  buffer from `ctx->count`, up to `fc->max_pages` pages.
- Models take `fuse_mkdir()` to return int and pass the mode through. It
  returns `struct dentry *` and clears `S_IFDIR` before sending;
  `create_new_entry()` returns the dentry from `d_splice_alias()`.
- Models do not know `fc->no_link` and `fc->no_copy_file_range_64`. After
  `-ENOSYS` `fuse_link()` returns `-EPERM`; `__fuse_copy_file_range()` tries
  `FUSE_COPY_FILE_RANGE_64` first and falls back to `FUSE_COPY_FILE_RANGE`.
- Models take the FUSE iomap ops to supply `.iomap_begin`. `fuse_iomap_ops`
  in `fs/fuse/file.c` sets `.iomap_next`, built with
  `DEFINE_IOMAP_ITER_NEXT()`.

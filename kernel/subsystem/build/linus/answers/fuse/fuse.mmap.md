- Inode with a backing file, file not opened passthrough:
  `fuse_file_mmap()` returns `-ENODEV`.
- Shared test for `FOPEN_DIRECT_IO`: `VM_MAYSHARE`, so it also covers a
  read-only `MAP_SHARED` mapping; the test for `fuse_link_write_file()` is
  `VM_SHARED` with `VM_MAYWRITE`.
- Private mapping of a `FOPEN_DIRECT_IO` file: set up by
  `generic_file_mmap()`, so it does not get `fuse_file_vm_ops`.
- `fuse_file_cached_io_open()`: waits while the inode is in uncached mode
  with no backing file (parallel direct writes); returns `-ETXTBSY` only
  when the inode has a backing file.
- `fuse_vma_close()`: calls `write_inode_now(inode, 1)` on every close of a
  vma that has `fuse_file_vm_ops`, read-only and private cached mappings
  included; it does not call `filemap_write_and_wait()`.
- VMA tracking: there is none; a shared writable mapping adds only the
  entry on `fi->write_files`, and a shared mapping of a `FOPEN_DIRECT_IO`
  file also takes caching io mode in `fuse_file_cached_io_open()`.

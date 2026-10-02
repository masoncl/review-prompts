- Order of the tests, first match wins:

  | Operation | Order |
  |---|---|
  | read, write | `FUSE_IS_DAX(inode)`, `FOPEN_DIRECT_IO`, `fuse_file_passthrough(ff)`, page cache |
  | `fuse_file_mmap()` | `FUSE_IS_DAX(inode)`, `fuse_file_passthrough(ff)`, `FOPEN_DIRECT_IO`, page cache |
  | `fuse_splice_read()`, `fuse_splice_write()` | passthrough only without `FOPEN_DIRECT_IO`, else `filemap_splice_read()` or `iter_file_splice_write()` |

- `fuse_cache_read_iter()`: has no direct-read branch of its own; it may
  call `fuse_update_attributes()` and return its error, else it calls
  `generic_file_read_iter()`, which serves `IOCB_DIRECT` through
  `fuse_direct_IO()`.

- Default page count: the constant is `FUSE_DEFAULT_MAX_PAGES_PER_REQ`.
- `fuse_max_pages_limit`: variable in `fs/fuse/inode.c`; its sysctl is in
  `fs/fuse/sysctl.c`, range 1 to 65535, built only with `CONFIG_SYSCTL`.
- `fc->max_write`: floor is the literal 4096; `process_init_reply()` does
  not cap it by `fc->max_pages`.
- `FUSE_MIN_READ_BUFFER`: 8192; it is the floor of the server's read
  buffer, not of `max_write`.
- `fuse_dev_do_read()`: tests `fch->max_write`, which is 0 until an INIT
  reply is accepted, so until then only `FUSE_MIN_READ_BUFFER` applies.
- Header room in that test: `sizeof(struct fuse_in_header)` plus
  `sizeof(struct fuse_write_in)`; there is no FUSE_BUFFER_HEADER_SIZE.
- io_uring payload: `fuse_uring_create()` sizes it as the largest of
  `FUSE_MIN_READ_BUFFER`, `fch->max_write` and `fch->max_pages` pages.
- `fc->name_max`: the file name limit; `FUSE_NAME_LOW_MAX` (1024) from
  `fuse_conn_init()`.
- `fc->name_max` becomes `FUSE_NAME_MAX` (`PATH_MAX - 1`) only when the
  reply has `FUSE_MAX_PAGES` and the resulting `fc->max_pages` is above 1.
- statfs: `f_namelen` is the server's `namelen`, copied by
  `convert_fuse_statfs()`; it neither sets nor reports `fc->name_max`.
- `fc->name_max` is tested in three places: `fuse_lookup_name()`,
  `fuse_notify_inval_entry()` and `fuse_notify_delete()`, each
  `-ENAMETOOLONG`; create, mkdir and rename have no test of their own.
- Readdir entries: tested against the constant `FUSE_NAME_MAX`, not
  `fc->name_max`; failure is `-EIO` (`parse_dirfile()` in
  `fs/fuse/readdir.c`).

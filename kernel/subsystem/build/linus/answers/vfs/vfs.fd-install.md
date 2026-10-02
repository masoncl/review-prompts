- `fd_install()` on a `FMODE_BACKING` file: `WARN_ON_ONCE()` and return;
  nothing is installed and the reference is not consumed.
- Combined helpers, all in `include/linux/file.h`:

| Helper | Use |
|---|---|
| `FD_ADD(flags, file_expr)` | reserve, create, install; returns the fd or an error |
| `FD_PREPARE(fdf, flags, file_expr)` | reserve and create; test `fdf.err`; setup may follow |
| `fd_publish(fdf)` | install; returns the fd; cannot fail |
| `CLASS(get_unused_fd, fd)(flags)` with `take_fd()` | reservation only |

- `FD_PREPARE()` scope exit without `fd_publish()`: `put_unused_fd()` and
  `fput()` run from `class_fd_prepare_destructor()`.
- `fd_prepare_fd()` and `fd_prepare_file()`: the only accessors; after
  `fd_publish()` they give `-EBADF` and NULL.
- File expression: evaluated only if the descriptor was reserved; see
  `__FD_PREPARE_INIT()`.
- Existing file passed as the expression: when the reservation fails the file
  is not put and the caller still owns its reference; `receive_fd()` in
  `fs/file.c` calls `get_file()` only after `fdf.err` was checked.
- There is no anon_inode_getfd_secure() here; `anon_inode_create_getfd()` in
  `fs/anon_inodes.c` does that.
- `anon_inode_getfile()`: creates the file only; `anon_inode_getfd()` is the
  combined form, built on `FD_ADD()`.
- There is no `DEFINE_FREE()` wrapper for `put_unused_fd()`; `DEFINE_FREE(fput,
  ...)` gives `__free(fput)` for the file.

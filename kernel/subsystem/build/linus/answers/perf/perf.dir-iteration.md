- `for_each_drm_fdinfo_in_dir()` and `for_each_drm_fdinfo()`: walk with libc
  `fdopendir()` or `opendir()` and `readdir()`, not with `struct io_dir`.
- Other `fdopendir()` walks under `tools/perf`: search for `fdopendir`; for
  example `dump_perf_event_processes()` in `tools/perf/util/evsel.c`.
- Raw fd after `fdopendir()`: still passed to `fstatat()`, `readlinkat()` or
  `openat()` while the `DIR` is open; `for_each_drm_fdinfo_in_dir()` does
  `fstatat(fd_dir_fd, ...)` inside the loop.
- Descriptors `for_each_drm_fdinfo_in_dir()` opens:

| Descriptor | Opened | Released by |
|---|---|---|
| `fd_dir_fd` (`<pid>/fd`) | on entry | `closedir(fd_dir)`; `close()` only if `fdopendir()` failed |
| `fdinfo_dir_fd` (`<pid>/fdinfo`) | lazily, at the first DRM fd | `close()`, only if not -1 |

- Both `openat()` calls pass `O_DIRECTORY` only.
- Callback error path: `goto close_fdinfo`, the same label the loop falls
  into when `readdir()` ends.
- `<pid>/fd` open failure: returns 0 before anything else is open.
- `<pid>/fdinfo` open failure: `continue`; the open is tried again at the
  next DRM fd.
- Callback arguments: `args`, `fdinfo_dir_fd` and the entry name; the callback
  gets no per-file descriptor.
- `proc_dir`: borrowed; `for_each_drm_fdinfo()` passes `dirfd(proc_dir)` and
  goes on calling `readdir(proc_dir)`, `drm_pmu__read_for_pid()` closes its
  own.
- **Unsafe usage**: leaving the `readdir()` loop of
  `for_each_drm_fdinfo_in_dir()` with `return`, which skips both releases.
  - Safe: `continue`, or `goto close_fdinfo` as the callback error path does.
- **Unsafe usage**: a callback that closes or keeps `fdinfo_dir_fd`; the next
  entry reuses it and `close_fdinfo` closes it again.
  - Safe: open the entry with `openat(fdinfo_dir_fd, fd_name, O_RDONLY)` and
    close only that descriptor before returning, as `read_drm_event()` does.
- **Unsafe usage**: closing `proc_dir` inside `for_each_drm_fdinfo_in_dir()`.
  - Safe: leave it to the caller, as `for_each_drm_fdinfo()` does with
    `closedir(proc_dir)`.

- `smb2_get_name()`: returns `-EINVAL` for an empty converted name and for a
  name that starts with `\`. It does not strip a leading separator, and a
  leading `/` passes.
- The leading-`\` test is in `smb2_get_name()`, so it applies to the rename
  and link names too, not only to `smb2_open()`.
- `ksmbd_validate_filename()`: does not reject `:` or `/`. Bytes with the
  high bit set always pass.
- `ksmbd_validate_filename()`: its only caller is `smb2_open()`. The rename
  and link paths of set-info do not call it.
- `ksmbd_share_veto_filename()`: called by `smb2_open()`, `smb2_rename()`
  and `__query_dir()`; `smb2_create_link()` does not call it.
- Confinement to the share does not depend on either check; it comes from the
  lookup (see "Confining names to the share").
- POSIX create context (`posix_ctxt`, needs `tcon->posix_extensions`):
  `smb2_open()` skips the `:` handling and `ksmbd_validate_filename()`. The
  veto check still runs.
- `:` without `KSMBD_SHARE_FLAG_STREAMS`: `smb2_open()` fails with `-EBADF`.
- Zero `NameLength` in `smb2_open()`: `smb2_get_name()` and every name check
  are skipped; the name is `""`.
- Bounds: `smb2_open()` passes `NameOffset` and `NameLength` to
  `smb2_get_name()` with no check of its own; it relies on
  `ksmbd_smb2_check_message()` in `fs/smb/server/smb2misc.c`.
- Set-info names: `set_rename_info()` and `smb2_create_link()` check
  `FileNameLength` against the buffer length before `smb2_get_name()`.
  `set_rename_info()` also rejects a zero length.

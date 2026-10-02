- Never-retrieved file: `can_finish` and `finish` get `retrieve_status` 0 and
  `file` NULL.
- `luo_file_finish()` failure: `-EBUSY` from the first `can_finish` that
  returns false is the only error; `finish` returns void.
- File reference count: `luo_file_finish()` does not look at it.
- After `-EBUSY`: nothing was finished, and `LIVEUPDATE_SESSION_FINISH` can
  be tried again while the session file descriptor is open.
- Serialized file entries: freed through `kho_block_set_shrink()` and
  `kho_block_set_destroy()`, not by a direct `kho_restore_free()` call in
  `luo_file_finish()`.

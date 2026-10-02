- Name length constant: `LIVEUPDATE_SESSION_NAME_LENGTH` in
  `include/uapi/linux/liveupdate.h`.
- `luo_session_create()`: returns `-EINVAL` for an empty name and for a name
  with no NUL within `LIVEUPDATE_SESSION_NAME_LENGTH` bytes.
- `luo_session_retrieve()`: validates nothing; it compares with `strncmp()`
  over the size of the name array, and a name that matches no incoming
  session returns `-ENOENT`.
- Session count: no LUO_SESSION_MAX in this tree; the bound is
  `KHO_MAX_BLOCKS` blocks per `struct kho_block_set`, past which
  `kho_block_add()` returns `-ENOSPC` and `kho_block_set_grow()` passes it
  up.
- `luo_session_insert()`: for the outgoing list it returns whatever
  `kho_block_set_grow()` returns, and grows before it checks for a duplicate
  name.
- Second retrieve of the same session: `-EINVAL`, from the test of
  `session->retrieved` in `luo_session_retrieve()`.
- Close after the update when `luo_session_finish_one()` fails:
  `luo_session_release()` returns the error without removing or freeing the
  session.
- That session stays on the incoming list with `retrieved` true and no file
  descriptor, so a later retrieve returns `-EINVAL` and nothing can finish
  it.

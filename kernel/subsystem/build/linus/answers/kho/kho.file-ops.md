The table lists what is easy to miss; see `struct liveupdate_file_ops` in
`include/linux/liveupdate.h` for the rest.

| Callback | Required | Kernel, caller | Easy to miss |
|---|---|---|---|
| `can_preserve` | yes | old, `luo_preserve_file()` | Handlers are tried in registration order; the first that returns true is used and no other is tried. |
| `get_id` | no | both, `luo_get_id()` | Key in `luo_preserved_files`; without it the key is the `struct file` pointer. A key already present makes `luo_preserve_file()` fail with `-EBUSY`. |
| `preserve` | yes | old, `luo_preserve_file()` | On failure LUO does not call `unpreserve`; `preserve` must undo its own partial work. |
| `unpreserve` | yes | old, `luo_file_unpreserve_files()` | Reached only from `luo_session_release()`; there is no per-file unpreserve ioctl. Newest file first. |
| `freeze` | no | old, `luo_file_freeze_one()` | Oldest file first. `kernel_kexec()` does not call `freeze_processes()` on this path, so other tasks still run. |
| `unfreeze` | no | old, `luo_file_unfreeze_one()` | Not called for the file whose `freeze` failed; that `freeze` must undo its own work. |
| `retrieve` | yes | new, `luo_retrieve_file()` | Called at most once per file, whether it succeeds or fails; `luo_file_finish()` does not call it. |
| `finish` | yes | new, `luo_file_finish_one()` | Newest file first. |

- `liveupdate_register_file_handler()`: does not test `owner`; returns
  `-EOPNOTSUPP` when `liveupdate_enabled()` is false and `-EEXIST` for a
  `compatible` already registered.
- Locks: `can_preserve`, `preserve` and `unpreserve` run under
  `session->mutex` without the mutex of the `struct luo_file`; `freeze`,
  `unfreeze`, `retrieve`, `can_finish` and `finish` hold both.
- New kernel: a handler must be registered before `/dev/liveupdate` is first
  opened; `luo_file_deserialize_one()` returns `-ENOENT` for an unknown
  `compatible`, and that fails the whole deserialization.

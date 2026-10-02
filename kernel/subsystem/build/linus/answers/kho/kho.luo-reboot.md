- `kernel_kexec()` in `kernel/kexec_core.c`: calls `liveupdate_reboot()` when
  it holds the kexec lock, `kexec_image` is set and
  `kexec_image->preserve_context` is false.
- `kernel_kexec()` does not test `liveupdate_enabled()`; `liveupdate_reboot()`
  returns 0 itself when LUO is disabled.
- The call is before `kernel_restart_prepare()`; an error goes to the caller
  of `kernel_kexec()` and no shutdown step has run.
- Steps of `liveupdate_reboot()`: `luo_session_serialize()`, then
  `luo_flb_serialize()`, which returns void.
- kho_finalize is defined nowhere in this tree, and `liveupdate_reboot()`
  rewrites no error to `-EAGAIN`.
- Undo: `liveupdate_reboot()` undoes nothing itself; `luo_session_serialize()`
  is the only step that can fail and rolls back before it returns.
- `luo_session_serialize()` rollback: unfreezes the sessions frozen before
  the failing one, zeroes their serialized names, and releases both rwsems;
  `luo_session_deserialize()` takes no part.
- Locks on success: `luo_session_serialize_rwsem` stays write-held and is
  never released; the outgoing `rwsem` is released, and each
  `session->mutex` is dropped inside `luo_session_freeze_one()`.
- After a successful `liveupdate_reboot()`: `luo_session_create()`,
  `luo_session_retrieve()`, `luo_session_ioctl()` and
  `luo_session_release()` block on the read side of
  `luo_session_serialize_rwsem`.

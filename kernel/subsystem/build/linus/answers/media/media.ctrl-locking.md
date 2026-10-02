- Lock held around the ops: `ctrl->handler->lock`, the lock of the handler
  that owns the control, taken for example with `v4l2_ctrl_lock(master)` in
  `try_set_ext_ctrls_common()` and `get_ctrl()`. The handler passed to the
  ioctl, which may be an inheriting one, is locked only for the lookup in
  `find_ref_lock()` and `prepare_ext_ctrls()`.
- Getters: there is no unlocked getter and no string getter.
  `v4l2_ctrl_g_ctrl()` and `v4l2_ctrl_g_ctrl_int64()` both lock in
  `get_ctrl()`; inside an op read `ctrl->val` or `ctrl->cur.val` instead.
- `v4l2_ctrl_find()`: takes `hdl->lock` through `find_ref_lock()`, so it
  deadlocks inside an op of the same handler.
- `v4l2_ctrl_activate()`: neither takes nor asserts the lock, but calls
  `send_event()`, which walks `ctrl->ev_subs`; `v4l2_ctrl_add_event()` and
  `v4l2_ctrl_del_event()` change that list under the handler lock.
- Shared lock with sub-device state: drivers set `sd->state_lock` to
  `hdl->lock`, as `imx219_probe()` does, or point both at one driver mutex.
- `v4l2_ctrl_handler_free()`: locks `hdl->lock` and destroys only
  `hdl->_lock`. A driver mutex installed in `hdl->lock` must still be valid
  then and is destroyed by the driver afterwards, as `ov8865_remove()` does.

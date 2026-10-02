- `v4l2_subdev_get_unlocked_active_state()`: calls
  `lockdep_assert_not_held()` on the active state's lock when the state is
  non-NULL.
- `sd->state_lock`: the core never sets it and there is no
  _synthetic_state_lock field; `v4l2_subdev_init()` does not write it. NULL
  means each state uses its own `_lock`.
- Try states: use `sd->state_lock` too. Every state allocated while it is
  set shares it, including the one from `v4l2_subdev_call_state_try()`.
- With a shared lock, `v4l2_subdev_get_unlocked_active_state()` trips
  lockdep whenever the caller holds that mutex for any reason, for example
  with a try state locked, or inside `s_ctrl` when the mutex is also the
  control handler's lock.
- `v4l2_ctrl_handler_init()`: is what sets the `lock` field of
  `struct v4l2_ctrl_handler`. Assigning `sd->state_lock` from it earlier
  copies NULL, and each state silently gets its own lock.
- Driver mutex as the one lock: overwrite the handler's `lock` after
  `v4l2_ctrl_handler_init()`, and point `sd->state_lock` at the same mutex;
  see `ccs_init_controls()` and `ccs_init_subdev()` in
  `drivers/media/i2c/ccs/ccs-core.c`.
- `v4l2_subdev_enable_streams()` and `v4l2_subdev_disable_streams()`: lock
  the active state and pass it locked to the op; the op must not lock it
  again.
- `call_s_stream()`: locks nothing; an `s_stream` op locks the active state
  itself.
- `subdev_do_ioctl_lock()`: locks only a non-NULL state; an op of a
  sub-device with no active state runs with no state lock held for
  `V4L2_SUBDEV_FORMAT_ACTIVE`.
- `v4l2_subdev_lock_states()`: its only caller is
  `v4l2_subdev_link_validate()`, with the active states of the sink and
  source sub-devices, and only when both are non-NULL. The pointer compare
  covers two sub-devices on one mutex.
- **Unsafe usage**: with `sd->state_lock` equal to the control handler's
  lock, calling a control helper that takes it through `v4l2_ctrl_lock()`
  (for example `v4l2_ctrl_s_ctrl()`, `v4l2_ctrl_modify_range()`,
  `v4l2_ctrl_grab()`) or `v4l2_ctrl_handler_setup()` while the state is
  locked: in a pad op that takes a state, called by the core, in
  `enable_streams`, in `init_state`. The mutex is taken twice by one task.
  - Safe: the unlocked variants, as `imx219_set_pad_format()` does with
    `__v4l2_ctrl_modify_range()` and `__v4l2_ctrl_s_ctrl()`, and
    `imx219_enable_streams()` with `__v4l2_ctrl_handler_setup()`;
    `__v4l2_ctrl_handler_setup()` asserts the lock is held.
  - Safe: the locking helpers where the state is not locked, as
    `imx214_ctrls_init()` does through `imx214_pll_update()` in probe,
    before `v4l2_subdev_init_finalize()`.
- **Unsafe usage**: with the same shared lock, calling
  `v4l2_subdev_lock_and_get_active_state()` inside `s_ctrl`; the control
  framework already holds the handler lock there.
  - Safe: `v4l2_subdev_get_locked_active_state()`, as `imx219_set_ctrl()`
    does.

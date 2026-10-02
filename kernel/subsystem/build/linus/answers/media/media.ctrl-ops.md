- `V4L2_CTRL_FLAG_VOLATILE` control in `cluster_changed()`: its value is never
  compared and it gets `has_changed = false`. A write reaches `s_ctrl` only if
  a cluster member, this one included, has `V4L2_CTRL_FLAG_EXECUTE_ON_WRITE`
  or a non-volatile member differs.
- Forced set: `try_or_set_cluster()` has none; `V4L2_CTRL_FLAG_EXECUTE_ON_WRITE`
  in `cluster_changed()` is the only way to get `s_ctrl` from it with an
  unchanged value. There is no has_new field.
- `cluster_changed()`: tests every non-NULL member, not only those with
  `is_new`, so an `V4L2_CTRL_FLAG_EXECUTE_ON_WRITE` member the caller did not
  set still triggers `s_ctrl`.
- 64-bit value: there is no val64 field in `struct v4l2_ctrl`; ops use
  `*ctrl->p_new.p_s64`.
- Validation before `try_ctrl`: there is no std_validate() here;
  `validate_new()` in `drivers/media/v4l2-core/v4l2-ctrls-api.c` calls
  `type_ops->validate`, by default `v4l2_ctrl_type_op_validate()`.
- Handler bound to a request: `try_set_ext_ctrls_common()` passes
  `!hdl->req_obj.req && set`, so only `try_ctrl` runs and the value is stored
  with `new_to_req()`; `s_ctrl` runs later from `v4l2_ctrl_request_setup()`.
- `ops` used: every call is `call_op(master, ...)` from
  `drivers/media/v4l2-core/v4l2-ctrls-priv.h`; the `ops` of other cluster
  members are not called.

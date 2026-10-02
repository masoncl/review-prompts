- `v4l2_ctrl_cluster()`: stores the array pointer in `ctrl->cluster` of every
  member; nothing is copied.
- NULL entries: `controls[0]` NULL or `ncontrols` 0 gives `WARN_ON()` and
  nothing is clustered; `v4l2_ctrl_cluster()`, `try_or_set_cluster()` and
  `cluster_changed()` skip NULL entries after the first.
- `has_volatiles`: `v4l2_ctrl_cluster()` samples `V4L2_CTRL_FLAG_VOLATILE` of
  the members once, at the call. `v4l2_g_ext_ctrls_common()` tests only the
  master's flag and `has_volatiles`, so a flag set on a member afterwards is
  not seen there.
- `ops`: only `controls[0]->ops` is called for the cluster.
- **Unsafe usage**: passing an array that does not outlive the controls, such
  as a local array; `try_or_set_cluster()` reads `master->cluster[i]` on every
  later set.
  - Safe: consecutive `struct v4l2_ctrl *` fields in the driver state, as
    `&ctrls->auto_wb` in `ov5640_init_controls()`.
- **Unsafe usage**: calling `v4l2_ctrl_auto_cluster()` when `controls[0]` may
  be NULL; it reads `controls[0]->minimum` after `v4l2_ctrl_cluster()` has
  only warned.
  - Safe: check `hdl->error` first, as `ov5640_init_controls()` does; every
    NULL return of `v4l2_ctrl_new_std()` leaves `hdl->error` set.

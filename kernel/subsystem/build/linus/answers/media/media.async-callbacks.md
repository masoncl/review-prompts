- `unbind`: `v4l2_async_unbind_subdev_one()` calls it only when the
  connection is the last one left on `sd->asc_list`.
- Sub-device bound through several connections: one `bound` per connection,
  one `unbind`, for the connection removed last.
- `asc->sd`: cleared, and `v4l2_device_unregister_subdev()` called, only in
  that same last-connection case.
- `bound` on a sub-device notifier: never runs inside that notifier's own
  `v4l2_async_nf_register()`; `v4l2_async_nf_try_all_subdevs()` returns 0
  while `v4l2_async_nf_find_v4l2_dev()` finds no `struct v4l2_device`.
- `parent` of a sub-device notifier: set only by
  `v4l2_async_nf_try_subdev_notifier()`, when the notifier's own sub-device
  is bound; its `bound` calls start then.
- `v4l2_async_match_notify()`: does not touch the sub-device's own notifier;
  its callers call `v4l2_async_nf_try_subdev_notifier()` after it, when the
  parent's connection is already on `done_list`.
- `complete`: can run more than once for one notifier; the core keeps no
  completed state, so unbinding and re-binding a sub-device calls it again.
- Root notifier with no connections: `complete` runs inside
  `v4l2_async_nf_register()`.
- `bound` or `complete` error in `__v4l2_async_nf_register()`:
  `v4l2_async_nf_unbind_all_subdevs()` unbinds everything bound through the
  notifier and its sub-notifiers, and the notifier is not added to
  `notifier_list`.
- Error in `__v4l2_async_register_subdev()`: the unwind depends on the step
  that failed.

| Failing step | Undone by the caller |
|---|---|
| `v4l2_async_match_notify()`, including `bound` | nothing beyond what `v4l2_async_match_notify()` undid itself |
| `v4l2_async_nf_try_subdev_notifier()` | `v4l2_async_unbind_subdev_one()` for the current connection |
| `v4l2_async_nf_try_complete()` | `v4l2_async_nf_unbind_all_subdevs()` on the sub-device's own notifier, then `v4l2_async_unbind_subdev_one()` |

- `vb2_core_reqbufs()` after the first `queue_setup`: besides the return
  value, checks only that `num_planes` and each `plane_sizes[i]` are
  non-zero; there is no upper bound on `num_planes` and no test of
  `*num_buffers`.
- `vb2_core_create_bufs()` after the first `queue_setup`: checks only the
  return value.
- `__vb2_queue_alloc()` writes `vb->planes[]` for every plane up to
  `num_planes`, so `queue_setup` must keep it at or below `VB2_MAX_PLANES`.
- `vb2_create_bufs()`: rejects a zero requested size and a plane count of 0 or
  above `VIDEO_MAX_PLANES` before the core is called, and always passes at
  least one plane.
- CREATE_BUFS sizes: whatever `queue_setup` leaves in `sizes[]` becomes
  `min_length`; the core never compares it with the current format.
- `*num_buffers` in CREATE_BUFS: the number being added, already limited to
  the free slots; `vb2_get_num_buffers()` gives the existing count.
- `q->min_reqbufs_allocation`: applied to the count before `queue_setup` in
  REQBUFS only; if fewer buffers end up allocated the result is `-ENOMEM`.
- Second `queue_setup` call (fewer buffers allocated than asked): REQBUFS
  zeroes `num_planes` first; CREATE_BUFS passes the values the first call
  left.
- Error from the second call: REQBUFS returns it; CREATE_BUFS returns
  `-ENOMEM` whatever the driver returned.
- Buffers already allocated at the second call keep the first call's sizes.
- CREATE_BUFS on an empty queue: is the first allocation and sets
  `q->memory`, still with a non-zero `*num_planes`.

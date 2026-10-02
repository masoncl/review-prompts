- `v4l2_update_last_buf_state()`: is the STOP handler, static in
  `drivers/media/v4l2-core/v4l2-mem2mem.c`; called only from
  `v4l2_m2m_encoder_cmd()` and `v4l2_m2m_decoder_cmd()`, never on buffer
  completion.
- START in `v4l2_m2m_encoder_cmd()` and `v4l2_m2m_decoder_cmd()`: returns
  `-EBUSY` while `is_draining` is set; otherwise clears only `has_stopped`.
- `next_buf_last`: `v4l2_update_last_buf_state()` sets it only when no source
  buffer and no capture buffer is on the ready list;
  `v4l2_m2m_update_stop_streaming_state()` sets it for the OUTPUT queue while
  draining when no capture buffer is on the ready list.
- `last_src_buf`: `drivers/media/v4l2-core/v4l2-mem2mem.c` never compares it
  with a buffer, and `v4l2_m2m_buf_done_and_job_finish()` has no draining
  logic. The driver tests `v4l2_m2m_is_last_draining_src_buf()` for each job
  and ends the drain.
- Last capture buffer of a drain, two in-tree forms:
  - in the job that consumes `last_src_buf`, set `V4L2_BUF_FLAG_LAST` on the
    destination buffer and call `v4l2_m2m_mark_stopped()`, then complete the
    buffers as usual, as `hantro_job_finish_no_pm()` does;
  - `v4l2_m2m_last_buffer_done()`, which completes the buffer itself, always
    with `VB2_BUF_STATE_DONE`; not usable with
    `v4l2_m2m_buf_done_and_job_finish()`, which completes the first
    destination buffer on the ready list itself.
- `v4l2_m2m_mark_stopped()`: clears `next_buf_last` as well as `is_draining`.
- `v4l2_m2m_clear_state()`: does not clear `last_src_buf`.
- `v4l2_m2m_qbuf()` on a CAPTURE buffer: completes the first buffer on the
  queue's `queued_list` as LAST through `v4l2_m2m_force_last_buf_done()` only
  when the queue is streaming, `vb2_start_streaming_called()` is false, and
  `has_stopped` is set or `v4l2_m2m_dst_buf_is_last()` is true. Once
  `start_streaming` has run, the driver's `buf_queue` must test
  `v4l2_m2m_dst_buf_is_last()` itself, as `hantro_buf_queue()` does.

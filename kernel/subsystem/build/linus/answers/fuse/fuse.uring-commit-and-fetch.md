- There is no fuse_uring_next_fuse_req() here;
  `fuse_uring_get_next_fuse_req()` assigns the next request and the caller
  calls `fuse_uring_send()`.
- Entry of a commit: taken from `req->ring_entry`; nothing compares it with the
  `qid` of the SQE beyond the lookup in that queue's `fpq`.
- `fuse_uring_cmd_index_ok()`: tested under `queue->lock` before the lookup;
  with a registered buffer pool the SQE must carry `IORING_URING_CMD_FIXED` and
  the pool's `buf_index`, else `-EINVAL`.
- Entry not in `FRRS_USERSPACE`: `fuse_uring_commit_fetch()` recycles the pool
  buffer, calls `zero_copy_unregister()` with the new command, ends the request
  with `-EIO` and returns `-EIO`.
- Reply header: checked in `fuse_uring_commit()` by
  `fuse_uring_out_header_has_err()`, not in `fuse_uring_copy_from_ring()`.
- `fuse_uring_out_header_has_err()`: tests `unique` and `error` only; no
  opcode test.
- Bad header or failed copy: the request ends with that error, the fetch still
  runs, and the handler returns `-EIOCBQUEUED`.
- No further request: the entry stays `FRRS_AVAILABLE` on `ent_avail_queue`
  with the command held and already marked cancelable.
- Buffer-pool queue with a request waiting and no free buffer:
  `fuse_uring_ent_assign_req()` returns NULL, same outcome as no request.

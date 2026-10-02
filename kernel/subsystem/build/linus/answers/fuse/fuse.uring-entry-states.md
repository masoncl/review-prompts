- There is no FRRS_FUSE_REQ_COMMIT state and no ent_release list.

| State | List | `ent->cmd` |
|---|---|---|
| `FRRS_INVALID` | none | NULL after allocation; set after a failed copy |
| `FRRS_AVAILABLE` | `ent_avail_queue` | set |
| `FRRS_FUSE_REQ` | `ent_w_req_queue` | set |
| `FRRS_USERSPACE` | `ent_in_userspace` | NULL |
| `FRRS_COMMIT` | `ent_commit_queue` | set, the commit command |
| `FRRS_TEARDOWN` | local list in `fuse_uring_stop_list_entries()` | as before |
| `FRRS_RELEASED` | `ent_released` | NULL |

- `ent->cmd`: cleared in `fuse_uring_send()`, under `queue->lock`, just before
  `io_uring_cmd_done()`; the entry holds the command through the whole copy.
- `FRRS_INVALID` after a failed copy: `fuse_uring_prepare_send()` unlinks the
  entry; the caller then puts it back with `fuse_uring_get_next_fuse_req()`.
- `fuse_uring_cancel()` on `FRRS_AVAILABLE`: unlinks and frees the entry; it
  does not move it to `ent_in_userspace`.
- Cancelled task work on `FRRS_FUSE_REQ`: `fuse_uring_send_in_task()` unlinks
  and frees the entry; it never reaches `FRRS_RELEASED`.
- Request in `FRRS_FUSE_REQ`: on no list and reachable only through
  `ent->fuse_req`; `req->ring_entry` is not set yet.
- `fuse_uring_add_to_pq()`: called from `fuse_uring_send()`, so the request
  enters `queue->fpq.processing` at the move to `FRRS_USERSPACE`.
- `ent->payload` and `ent->buf_id` of a pool queue: written under
  `queue->lock` by `fuse_uring_select_buffer()` and
  `fuse_uring_recycle_buffer()`, which assert it; `ent->zero_copied` is written
  without it.

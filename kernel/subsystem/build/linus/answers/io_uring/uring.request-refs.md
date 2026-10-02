- `REQ_F_REFCOUNT` is enabled at three places only, none in `io_uring/poll.c`
  (poll uses `poll_refs`):

| Where | Request | Initial value |
|---|---|---|
| `io_wq_submit_work()` | the request | 2, or `req_ref_get()` if enabled |
| `__io_prep_linked_timeout()` | head (`io_req_set_refcount()`) | 1 |
| `__io_prep_linked_timeout()` | `req->link`, the timeout | 2 |

- `__io_req_set_refcount()`: tests the flag; on a request whose count is
  enabled it changes nothing, so the count passed is dropped.
- There is no req_set_refcount() here; the helper is `io_req_set_refcount()`.
- `req_ref_put_and_test_atomic()` on a request without the flag: warns, then
  decrements; `io_wq_free_work()` is its caller.

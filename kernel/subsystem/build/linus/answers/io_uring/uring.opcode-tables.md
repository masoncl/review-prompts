- `struct io_issue_def` has no iopoll_queue member; whether a request goes on
  the iopoll list is the request flag `REQ_F_IOPOLL`, set by the handler at
  issue (`io_rw_init_file()` in `io_uring/rw.c`, `io_uring_cmd()`).
- `struct io_issue_def` also holds `is_128`, `filter_pdu_size` and
  `filter_populate`; `io_init_req()` reads `is_128`, and
  `io_uring_populate_bpf_ctx()` in `io_uring/bpf_filter.c` reads the other two.
- `struct io_cold_def` has exactly `name`, `sqe_copy`, `cleanup`, `fail`.
- `io_uring_optable_init()` build checks: each array is compared to
  `IORING_OP_LAST` separately, not to the other array.
- `io_uring_optable_init()` boot checks: `BUG_ON()` for a NULL `prep`, and for
  a NULL `issue` unless `prep` is `io_eopnotsupp_prep()`; `WARN_ON_ONCE()`
  only for a NULL `name`.
- `io_uring_optable_init()` checks no other member: flag bits, `async_size`,
  `filter_pdu_size` and the cold callbacks are unchecked.
- **Unsafe usage**: an `io_issue_defs[]` entry with `filter_pdu_size` set and
  no `filter_populate`.
  - Unsafe: with a BPF filter registered for the opcode,
    `io_uring_populate_bpf_ctx()` calls `filter_populate` with no NULL test.
  - Safe: set both together, as the `IORING_OP_OPENAT` entry does.

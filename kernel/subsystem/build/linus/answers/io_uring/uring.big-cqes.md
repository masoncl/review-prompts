- `cqe32` on an `IORING_SETUP_CQE32` ring: must be false; the ring flag alone
  makes `io_get_cqe_overflow()` advance `cqe_cached` by two.
- **Unsafe usage**: `cqe32` true on an `IORING_SETUP_CQE32` ring.
  `io_cqe_cache_refill()` then applies the wrap test and the two-slot minimum
  to 32-byte slots, and `io_fill_nop_cqe()` writes the filler at the
  unshifted index.
  - Safe: `__io_cqring_overflow_flush()` forces `is_cqe32` to false when the
    ring has `IORING_SETUP_CQE32`.
  - Safe: `io_defer_get_uncommited_cqe()` passes
    `ctx->flags & IORING_SETUP_CQE_MIXED`.
  - Safe: `io_req_set_res32()` sets `IORING_CQE_F_32` only through
    `ctx_cqe32_flags()`, which returns 0 unless the ring has
    `IORING_SETUP_CQE_MIXED`.
- There is no REQ_F_CQE32_INIT in this tree; `io_fill_cqe_req()` derives
  `cqe32` from `IORING_CQE_F_32` in `req->cqe.flags`.
- `IORING_SETUP_CQE_MIXED` size of an entry: taken from `IORING_CQE_F_32` in
  the CQE's own flags by `io_alloc_ocqe()` and `__io_cqring_overflow_flush()`,
  so a CQE without the flag is stored and flushed as 16 bytes.
- `io_defer_get_uncommited_cqe()` on an `IORING_SETUP_CQE_MIXED` ring: always
  reserves 32 bytes; the caller sets `IORING_CQE_F_32` itself, as
  `io_zcrx_queue_cqe()` does.
- `IORING_SETUP_CQE_MIXED` with `cq_entries` below 2: `rings_size()` returns
  `-EOVERFLOW`.

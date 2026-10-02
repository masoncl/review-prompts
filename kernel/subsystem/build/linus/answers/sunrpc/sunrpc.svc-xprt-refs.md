- `sp_xprts` queue entry: no reference. `svc_xprt_enqueue()` takes none;
  `svc_xprt_dequeue()` takes the thread's reference after `lwq_dequeue()`.
- `bc_xprt` in `struct rpc_xprt`: no reference; `xs_setup_bc_tcp()` and
  `xprt_setup_rdma_bc()` assign it plainly. The reverse pointer
  `xpt_bc_xprt` does hold one on the `struct rpc_xprt`.
- nfsd holds references in `cn_xprt` (`alloc_conn()`, dropped by
  `free_conn()`) and in `cl_cb_conn.cb_xprt` (`fs/nfsd/nfs4callback.c`).
- `svc_find_xprt()` and `svc_find_listener()`: return with a reference that
  the caller must put.
- `svc_age_temp_xprts()`: skips a transport whose `kref_read()` is above 1,
  so any long-held reference also exempts the connection from idle ageing.
- `svc_tcp_handshake()`: takes `svc_xprt_get()` before
  `tls_server_hello_x509()`; `svc_tcp_handshake_done()` puts it as its last
  step, after `complete_all()`.
- `svc_tcp_handshake()` puts the reference itself on the two paths where the
  callback never runs: `tls_server_hello_x509()` failed, or
  `tls_handshake_cancel()` returned true.
- `tls_handshake_cancel()` returning false: the callback is in flight;
  `svc_tcp_handshake()` then does `wait_for_completion()` and leaves the put
  to the callback.
- **Potentially unsafe usage**: giving a `struct svc_xprt` pointer to a
  callback that runs later, without `svc_xprt_get()`.
  - Unsafe: when the callback can run, or still be running, after the
    submitter's own reference is put; `svc_xprt_free()` calls `xpo_free`,
    which frees the structure.
  - Safe: take a reference before submitting and put it exactly once on
    every outcome, as `svc_tcp_handshake()` and `svc_tcp_handshake_done()`
    do, and as `svc_defer()` and `svc_revisit()` do.
  - Safe: when `xpo_free` stops the source of callbacks before it frees, as
    `svc_rdma_free()` does: it drains and destroys the QP, the CQs and the
    CM ID before `kfree()`.

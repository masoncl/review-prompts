- Models take a bad reply verifier to be retried or to refresh the cred.
  With an up-to-date cred and `-EACCES`, `rpc_decode_header()` returns
  `-EBADMSG`.
- Models take device removal to reach the client as a CM event. Client and
  server both register with `rpcrdma_rn_register()` in
  `net/sunrpc/xprtrdma/ib_client.c`.
- Models do not know the third argument of `svc_xprt_destroy_all()`. It
  decides whether `svc_rpcb_cleanup()` runs.
- Models take the temporary-connection limit to scale with the service.
  `svc_check_conn_limits()` compares `sv_tmpcnt` with `XPT_MAX_TMP_CONN`.
- Models take the thread total to equal the request.
  `svc_set_num_threads()` gives every pool at least one thread when
  `nrservs` is nonzero, so the total may exceed the request.
- Models do not know the write-pad MR. `rpcrdma_encode_write_list()` uses
  `re_write_pad_mr` unchecked.
- Models take `RPCSVC_MAXPAYLOAD` to be 1 MB. It is 4 MB in
  `include/linux/sunrpc/svc.h`.
- Models name rpcrdma_recv_buffer_put(). Here reps go back through
  `rpcrdma_rep_put()` or `rpcrdma_reply_put()`.
- Models name svc_rqst_release_page() and rq_vec. Here:
  `svc_rqst_page_release()`, `rq_bvec`.
- Models do not expect `kzalloc_obj()`, `kzalloc_objs()`, `kzalloc_flex()`
  or `kmalloc_obj()`. They are allocation macros defined in
  `include/linux/slab.h`.
- Models expect del_timer_sync() and from_timer(). This tree has
  `timer_delete_sync()` and `timer_container_of()`.
- Models expect `kernel_bind()` to take a `struct sockaddr`. It takes a
  `struct sockaddr_unsized`; see `svc_create_socket()`.

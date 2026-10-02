- `sk_pages`: a flexible array at the end of `struct svc_sock` with
  `sk_maxpages` entries, sized by `svc_serv_maxpages()` in
  `svc_setup_socket()`.
- `svc_tcp_save_pages()`: besides moving the pages it sets
  `rq_pages_nfree`; `svc_alloc_arg()` refills only that many entries of
  `rq_pages`.
- `svc_tcp_restore_pages()`: releases the thread's own page in each slot
  with `svc_rqst_page_release()` before it puts the saved page there.
- Record length: there is no sk_reclen field; `svc_sock_reclen()` masks
  `sk_marker`. The bound is `sv_max_mesg`, not `svc_max_payload()`.
- Oversized record: `svc_tcp_read_marker()` calls
  `svc_xprt_deferred_close()` itself and returns `-EAGAIN`, so
  `svc_tcp_recvfrom()` takes its no-close exit.
- End of stream: a 0 return from the socket is a short read, not an error;
  the receive path keeps the state and does not close.
  `svc_tcp_state_change()` closes when `sk_state` leaves `TCP_ESTABLISHED`.
- TLS: `svc_tcp_sock_process_cmsg()` turns a fatal alert into `-ENOTCONN`,
  which closes; a non-fatal alert becomes `-EAGAIN`.
- Backchannel reply: `receive_cb_reply()` returns `-EAGAIN` when
  `xpt_bc_xprt` is NULL, no request matches the XID, or the reply buffer is
  too small; the record is dropped and the connection stays open.

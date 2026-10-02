- The negotiate response is posted from inside `smbdirect_socket_accept()`, not
  when the negotiate request arrives.
- `smbdirect_accept_negotiate_recv_work()`: for a socket with
  `sc->accept.listener` set it parses the request, moves the socket from
  `listen.pending` to `listen.ready`, wakes the listener and returns without
  sending.
- `smbdirect_listen_connect_request()` sets `accept.listener` on every socket
  it creates, and it is the only caller of
  `smbdirect_socket_create_accepting()`.
- `smbdirect_socket_accept()`: takes the socket off `listen.ready`, sets status
  to `SMBDIRECT_SOCKET_CONNECTED`, then calls
  `smbdirect_accept_negotiate_finish()` with status 0.
- When `smbdirect_socket_accept()` returns, the data receives and the response
  are posted, or cleanup is scheduled; the send completion may not have run
  yet.
- Before the application accepts, the peer holds no credits, so no data
  transfer message can be in the reassembly queue.
- Version mismatch: `smbdirect_accept_negotiate_recv_work()` calls
  `smbdirect_accept_negotiate_finish()` at once with `STATUS_NOT_SUPPORTED`;
  that response grants 0 credits and the socket is cleaned up after it is sent.
- Waiting in `listen.ready`: no local timer ends it;
  `smbdirect_accept_negotiate_recv_work()` sets `SMBDIRECT_KEEPALIVE_NONE`, and
  `smbdirect_connection_idle_timer_work()` then returns while status is not
  `SMBDIRECT_SOCKET_CONNECTED`.
- ksmbd: `smb_direct_listener_kthread_fn()` in
  `fs/smb/server/transport_rdma.c` calls `smbdirect_socket_accept()`; there is
  no smb_direct_prepare() and `struct ksmbd_transport_ops` has no prepare
  member.

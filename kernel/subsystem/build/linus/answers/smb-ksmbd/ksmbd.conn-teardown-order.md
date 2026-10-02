| Step | Action in `ksmbd_conn_handler_loop()` | Needs first |
|---|---|---|
| 1 | `ksmbd_conn_set_releasing()` | receive loop left |
| 2 | `ksmbd_conn_cancel_async_requests()` | step 1; `ksmbd_conn_link_async_request()` refuses a link once it sees releasing |
| 3 | `wait_event(conn->r_count_q, ...)` for `r_count == 0` | step 2, which wakes handlers blocked in `smb2_lock()` |
| 4 | `utf8_unload()`, `unload_nls()` | step 3 |
| 5 | `default_conn_ops.terminate_fn()` | step 3 |
| 6 | `t->ops->disconnect()` | step 5 |
| 7 | `module_put(THIS_MODULE)` | step 6 |

- Step 2: sets every `KSMBD_WORK_ACTIVE` item on `conn->async_requests` to
  `KSMBD_WORK_CANCELLED` and calls its `cancel_fn`, if set, under
  `conn->request_lock`.
- Step 5 is `ksmbd_server_terminate_conn()`: `ksmbd_conn_sessions_cleanup()`
  then `destroy_lease_table()`. There is no ksmbd_sessions_deregister() here.
- `destroy_lease_table(conn)`: selects tables by `ClientGUID`, not by conn
  pointer, and puts each matching table's reference on `lb->conn`.
- Step 6: `ksmbd_tcp_disconnect()` and `smb_direct_disconnect()` shut the
  socket down and call `ksmbd_conn_free()`; neither releases the socket.
- Socket release: `sock_release()` in `ksmbd_tcp_free_transport()` and
  `smbdirect_socket_release()` in `smb_direct_free_transport()`, run by the
  final free after the last `ksmbd_conn_put()`.
- The final free can run after step 7; `ksmbd_server_exit()` covers it with
  `rcu_barrier()` followed by `ksmbd_conn_wq_destroy()`.
- `conn->request_lock`: orders status against async linking.
  `ksmbd_conn_link_async_request()` in `fs/smb/server/smb2pdu.c` tests
  exiting and releasing and links under it.
- Status writers that take `conn->request_lock`: `ksmbd_conn_abort()`,
  `stop_sessions()` and `ksmbd_all_conn_set_status()`; none overwrites
  `KSMBD_SESS_RELEASING`.
- `ksmbd_conn_set_releasing()` and the other setters in
  `fs/smb/server/connection.h`: plain `WRITE_ONCE()`. Step 1 holds no lock;
  the ordering comes from step 2 taking `conn->request_lock` after the store.

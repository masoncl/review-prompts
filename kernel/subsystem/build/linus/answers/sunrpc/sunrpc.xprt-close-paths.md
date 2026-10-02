- `svc_xprt_close()`: needs no ownership. It sets `XPT_CLOSE` and tries
  `test_and_set_bit(XPT_BUSY)` itself; it deletes inline only if it won the
  bit.
- `svc_xprt_close()` when `XPT_BUSY` was already set: does not enqueue. The
  owner's `svc_xprt_received()` enqueues the transport, and the thread that
  dequeues it deletes it in `svc_handle_xprt()`.
- `svc_xprt_close()` needs process context: `svc_delete_xprt()` sleeps in
  `lock_sock()` under `svc_sock_detach()` and in `svc_register()`.
- A server thread may call `svc_xprt_close()` on its own `rq_xprt`:
  `svc_process_common()` does so for an `XPT_TEMP` transport; the thread's
  reference keeps the structure until `svc_xprt_release()`.
- `svc_delete_xprt()`, in order:
  1. if `XPT_RPCB_UNREG` is set, `svc_register()` with port 0; this runs
     before the `XPT_DEAD` test;
  2. `test_and_set_bit(XPT_DEAD)`, return if it was set;
  3. `xpo_detach`;
  4. `close` of `xpt_bc_xprt`, if set;
  5. under `sv_lock`: `list_del_init()` of `xpt_list`, and `sv_tmpcnt--`
     only if `XPT_TEMP` is set and `XPT_PEER_VALID` is clear;
  6. `free_deferred()` of everything left on `xpt_deferred`;
  7. `call_xpt_users()`;
  8. `svc_xprt_put()` of the reference from `kref_init()` in
     `svc_xprt_init()`.
- `svc_delete_xprt()` does not call `xpo_kill_temp_xprt` and does not take
  the transport off `sp_xprts`.
- `call_xpt_users()`: runs each callback with `xpt_lock` held, so a callback
  cannot sleep or call `register_xpt_user()` or `unregister_xpt_user()` on
  that transport.

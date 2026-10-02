- Three references exist on a connected `struct rpcrdma_ep`:

| Taken | For | Dropped |
|---|---|---|
| `kref_init()` in `rpcrdma_ep_create()` | the transport | `rpcrdma_xprt_disconnect()` |
| `rpcrdma_ep_get()` in `rpcrdma_xprt_connect()`, before the first `rpcrdma_post_recvs()` | posted Receives | `rpcrdma_xprt_drain()` |
| `rpcrdma_ep_get()` on `RDMA_CM_EVENT_ESTABLISHED` | the connection | `RDMA_CM_EVENT_DISCONNECTED` |

- `RDMA_CM_EVENT_DISCONNECTED`: the only event that drops a reference; the
  put is unconditional, with no test of `re_connect_status`.
- `RDMA_CM_EVENT_ADDR_CHANGE`: never drops a reference. Old status 0 wakes
  `re_connect_wait`; old status 1 calls `rpcrdma_force_disconnect()` and
  returns 0, leaving the ESTABLISHED reference for the DISCONNECTED case.
- `RDMA_CM_EVENT_ADDR_ERROR` and `RDMA_CM_EVENT_ROUTE_ERROR`: set
  `re_async_rc` and complete `re_done`; they do not touch
  `re_connect_status` or `re_connect_wait`.
- `RDMA_CM_EVENT_DEVICE_REMOVAL`: has no case in
  `rpcrdma_cm_event_handler()`; it falls to `default` and returns 0.
- `rpcrdma_rn_register()`: called as the last step of
  `rpcrdma_create_id()`, after route resolution. It returns `-ENETUNREACH`
  when the device has `RPCRDMA_RD_F_REMOVING` set, which fails the connect.
- `rpcrdma_ep_removal_done()`: calls `xprt_force_disconnect()` directly, not
  `rpcrdma_force_disconnect()`, so `re_force_disconnect` does not gate it.
- `rpcrdma_rn_unregister()`: uses `rn_done` as the "registered" marker and
  is a no-op when it is NULL; `svc_rdma_free()` relies on that after
  `rpcrdma_rn_register()` failed in `svc_rdma_accept()`.
- `rpcrdma_ep_destroy()`: also drops the module reference that
  `rpcrdma_ep_create()` took.

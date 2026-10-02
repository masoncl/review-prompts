- `pc_release` runs after the reply is sent: `svc_process()` calls
  `svc_send()`, then `svc_release_rqst()`, which is the only caller of
  `pc_release` in the tree.
- `svc_process_common()` does not call `pc_release`.
- Request dropped by `svc_process_common()`: `svc_process()` calls
  `svc_release_rqst()` before `svc_drop()`.
- `svc_release_rqst()` clears `rq_procinfo`, and `svc_process()` clears it on
  entry, so the hook runs at most once per request.
- `svc_xprt_release()` is called from `svc_handle_xprt()` after
  `svc_process()` returns, not from `svc_send()` or `svc_drop()`;
  `svc_drop()` only traces.
- Order for a sent reply: `svc_send()`, `pc_release`, `svc_xprt_release()`;
  the hook runs with `rq_xprt` set.
- There is no SVC_SYSERR or SVC_NEGOTIATE value in `enum svc_auth_status`.

| Value | `svc_process_common()` |
|---|---|
| `SVC_OK` | goes on to `pg_init_request` and the dispatch |
| `SVC_DENIED` | sends an `RPC_AUTH_ERROR` denial with `rq_auth_stat` unchanged |
| `SVC_DROP` | `svc_authorise()`, returns 0; no reply, transport not closed |
| `SVC_GARBAGE` | sets `rq_auth_stat` to `rpc_autherr_badcred`, sends an `RPC_AUTH_ERROR` denial; does not encode `rpc_garbage_args` |
| `SVC_CLOSE` | `svc_authorise()`, then `svc_xprt_close()` only if `rq_xprt` has `XPT_TEMP`; no reply |
| `SVC_COMPLETE` | the reply is encoded but not sent; goes through `svc_authorise()` and returns 1 so `svc_process()` sends it |
| `SVC_VALID`, `SVC_NEGATIVE`, `SVC_PENDING` | `pr_warn_once()`, `rq_auth_stat` set to `rpc_autherr_failed`, `RPC_AUTH_ERROR` denial |

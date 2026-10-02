- Work items of an accepting socket other than `connect.work` and
  `disconnect_work`, all in `fs/smb/smbdirect/`:

| Work item | Real handler | Armed in | Posts receives or grants |
|---|---|---|---|
| `recv_io.posted.refill_work` | `smbdirect_connection_recv_io_refill_work()` | `smbdirect_connection_negotiation_done()` | posts receives, then queues `idle.immediate_work` |
| `idle.immediate_work` | `smbdirect_connection_send_immediate_work()` | `smbdirect_connection_negotiation_done()` | sends an empty message that carries the grant |
| `idle.timer_work` | `smbdirect_connection_idle_timer_work()` | `smbdirect_accept_connect_request()`, after `rdma_accept()` | neither; only queues `idle.immediate_work` |

- There is no smb_direct_post_recv_credits() in this tree.
- `smbdirect_connection_negotiation_done()`: runs from
  `smbdirect_accept_negotiate_send_done()`, the send completion of the
  negotiate response, and only when the completion succeeded and the response
  status was 0.
- Until then `recv_io.posted.refill_work` and `idle.immediate_work` are still
  disabled from `smbdirect_socket_init()`; every `queue_work()` on them is
  dropped.
- `smbdirect_accept_negotiate_finish()`: arms no work item; it posts the data
  receives by calling `smbdirect_connection_recv_io_refill()` directly, takes
  the grant from `smbdirect_connection_grant_recv_credits()` and posts the
  response.
- `idle.timer_work` runs during negotiation as the negotiate timeout; it cannot
  cause a grant, because its handler returns unless status is
  `SMBDIRECT_SOCKET_CONNECTED` and `idle.immediate_work` is still disabled.
- `smbdirect_connection_put_recv_io()`: queues `recv_io.posted.refill_work`
  unconditionally; during negotiation only the disabled state stops a refill.
- **Potentially unsafe usage**: arming `recv_io.posted.refill_work` or
  `idle.immediate_work` of an accepting socket with their real handlers.
  - Unsafe: before the negotiate response is sent;
    `smbdirect_accept_negotiate_recv_work()` calls
    `smbdirect_connection_put_recv_io()`, which would start a refill that
    queues `idle.immediate_work` ahead of the response.
  - Safe: in `smbdirect_connection_negotiation_done()`, reached from
    `smbdirect_accept_negotiate_send_done()` after the response completed.

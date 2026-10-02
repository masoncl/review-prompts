- Socket reference: it is the creator's reference from `l2cap_chan_create()`;
  `l2cap_sock_alloc()` takes no extra one.
- `l2cap_sock_put_chan()`: drops the socket's reference once and clears
  `chan->data` and `l2cap_pi(sk)->chan`; called from `l2cap_sock_kill()` under
  `lock_sock()` and from `l2cap_sock_destruct()`.
- `chan->conn`: set in `__l2cap_chan_add()` with `l2cap_conn_get()` and not
  cleared afterwards; `l2cap_chan_destroy()` drops that conn reference.
- Deleted channel: marked by `FLAG_DEL`, set in `l2cap_chan_del()`. All four
  timer handlers test `FLAG_DEL`, not `chan->conn`.
- `l2cap_chan_timeout()`: tests `FLAG_DEL` before taking any lock and puts;
  it tests again under `conn->lock` and the channel lock.
- Timer handlers: take no reference; each consumes the one that
  `l2cap_set_timer()` took.
- `l2cap_set_timer()`: calls `l2cap_chan_hold()` when `cancel_delayed_work()`
  returned false, then `schedule_delayed_work()`, whose result it ignores.
- `__set_retrans_timer()`: a static function in
  `net/bluetooth/l2cap_core.c`; arms nothing while `monitor_timer` is pending
  or `chan->retrans_timeout` is 0.
- `__set_monitor_timer()`: clears the retransmission timer first; arms
  nothing if `chan->monitor_timeout` is 0.
- `__set_ack_timer(c)`: the macro body names `chan->ack_timer`, so it holds
  `c` and arms the timer of the variable `chan` in scope.
- `l2cap_chan_hold_unless_zero()`: dereferences its argument;
  `l2cap_conn_hold_unless_zero()` returns NULL for NULL.
- **Potentially unsafe usage**: plain `l2cap_chan_hold()` on a channel reached
  through a list or a back pointer.
  - Unsafe: on a channel found by walking `chan_list`; `l2cap_chan_destroy()`
    unlinks it only after the count has reached zero.
  - Safe: on an entry of `conn->chan_l` under `conn->lock`, as
    `l2cap_conn_del()` does; `l2cap_chan_del()` drops the list's reference
    only after `list_del()`.
  - Safe: on a non-NULL `l2cap_pi(sk)->chan` under the socket lock, as
    `l2cap_sock_cleanup_listen()` does; `l2cap_sock_kill()` clears that
    pointer and drops the reference under `lock_sock()`.

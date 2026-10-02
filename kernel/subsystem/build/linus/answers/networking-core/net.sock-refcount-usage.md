- `sk_stop_timer()`: calls `timer_delete()`; there is no del_timer() timer
  function in this tree.
- `__sock_put()` (used by `sk_stop_timer()` and `sk_stop_timer_sync()`): a
  plain `refcount_dec()` that never calls `sk_free()`.
- **Potentially unsafe usage**: calling `sk_stop_timer()` or
  `sk_stop_timer_sync()`.
  - Unsafe: when the timer's reference may be the last one; `refcount_dec()`
    warns of a leak and nothing frees the socket.
  - Safe: when the caller holds its own reference across the call, as
    `tcp_close()` does: when `sk_net_refcnt` is 0 it calls
    `inet_csk_clear_xmit_timers_sync()` before its own `sock_put()`.
    `__sock_put()` being a bare `refcount_dec()` defines the requirement.
- `inet_csk_clear_xmit_timer()`: does not stop the timer or drop a reference;
  its `sk_stop_timer()` calls are under `#ifdef INET_CSK_CLEAR_TIMERS`, which
  `include/net/inet_connection_sock.h` undefines.
- After `inet_csk_clear_xmit_timer()`: the timer stays armed with its
  reference; the handler runs, finds the pending flag clear, and does
  `sock_put()`.
- `inet_csk_clear_xmit_timers()` and `inet_csk_clear_xmit_timers_sync()`: do
  call `sk_stop_timer()` and `sk_stop_timer_sync()`, on the retransmit,
  delayed-ACK and keepalive timers.
- There is no inet_csk_reset_keepalive_timer() here;
  `tcp_reset_keepalive_timer()` in `net/ipv4/tcp_timer.c` calls
  `sk_reset_timer()`.
- **Potentially unsafe usage**: arming a timer embedded in a socket with
  plain `mod_timer()`.
  - Unsafe: when the handler ends in `sock_put()`, as `tcp_write_timer()`
    does, and nothing took a reference for the timer; the put drops someone
    else's reference.
  - Safe: when the timer's reference is counted another way, as
    `reqsk_queue_hash_req()` does by setting `rsk_refcnt` to 2 + 1 after
    `mod_timer()`; `reqsk_timer_handler()` drops it with `reqsk_put()` when
    it does not re-arm.

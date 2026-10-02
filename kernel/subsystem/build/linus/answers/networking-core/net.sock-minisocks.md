- `sk_to_full_sk()` and `sk_const_to_full_sk()` in `include/net/inet_sock.h`:
  return NULL for a `TCP_TIME_WAIT` socket, not the socket itself.
- `sk_to_full_sk()` on a request sock: returns `rsk_listener`, which is NULL
  when the request sock was allocated with `attach_listener` false, as
  `cookie_tcp_reqsk_alloc()` does.
- Result of `sk_to_full_sk()`: needs a NULL test before any dereference,
  unless the caller has already ruled out a timewait sock and a request sock
  without listener.
- Members of `struct sock_common` that hold other data on a non-full socket:

| `struct sock` name | Request sock holds | Timewait sock holds |
|---|---|---|
| `sk_flags` | `skc_listener` | `skc_tw_dr` |
| `sk_incoming_cpu` | `skc_rcv_wnd` | `skc_tw_rcv_nxt` |
| `sk_rxhash` | `skc_window_clamp` | `skc_tw_snd_nxt` |

- **Potentially unsafe usage**: `sock_flag()`, `sk_incoming_cpu` or
  `sk_rxhash` on a pointer that may be a request or timewait sock.
  - Unsafe: when the value is used as flags, a CPU number or a hash with no
    `sk_fullsock()` test; the storage holds the members in the table above,
    and being in `struct sock_common` does not make them valid.
  - Safe: after `sk_fullsock()` returned true, as `sk_is_refcounted()` tests
    before `sock_flag()`; the unions in `struct sock_common` define the
    overlap.
  - Safe: copying the value unchanged from one request sock to another, as
    `inet_reqsk_clone()` does with `sk_incoming_cpu`.
- `sk_tx_queue_mapping`: is `skc_tx_queue_mapping` in `struct sock_common`
  and valid on all three kinds; `reqsk_alloc_noprof()` clears it,
  `tcp_time_wait()` copies it, and `sk_tx_queue_get()` reads it before its
  `sk_fullsock()` test.

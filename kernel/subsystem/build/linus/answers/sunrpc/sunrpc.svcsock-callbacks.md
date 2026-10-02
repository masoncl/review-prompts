- A child of a listener inherits `sk_user_data` as well as `sk_data_ready`:
  `sk_clone()` in `net/core/sock.c` clears the field only when
  `sk_user_data_is_nocopy()`, and `svc_setup_socket()` stores an untagged
  pointer.
- On the child, `sk_user_data` is therefore non-NULL and points to the
  listener's `struct svc_sock`, on which the child holds no reference; the
  NULL test does not catch this case.
- `svc_tcp_listen_data_ready()` is the only server callback a child
  inherits: `svc_tcp_init()` installs only `sk_data_ready` on a listener.
- The callbacks take no lock: `net/sunrpc/svcsock.c` uses neither
  `sk_callback_lock` nor RCU for `sk_user_data`.
- `svc_setup_socket()` order: save the three original callbacks in
  `struct svc_sock`, `wmb()`, store `sk_user_data`, then `svc_tcp_init()` or
  `svc_udp_init()` runs `svc_xprt_init()` and only then installs the new
  callbacks.
- `svc_tcp_accept()`: resets the child's three callbacks to the listener's
  saved originals before it calls `svc_setup_socket()`; otherwise the
  child's `sk_odata` would be `svc_tcp_listen_data_ready()`.
- **Potentially unsafe usage**: dereferencing `sk_user_data` in a socket
  callback after only the NULL test and `rmb()`.
  - Unsafe: in a callback installed on a listening socket, where it also
    runs on unaccepted children with the listener's pointer.
  - Safe: in a listener callback that returns when `sk_state` is not
    `TCP_LISTEN` before touching the pointer, as
    `svc_tcp_listen_data_ready()` does.
  - Safe: in callbacks installed only on connected TCP or UDP sockets, as
    `svc_data_ready()`, `svc_write_space()` and `svc_tcp_state_change()`
    are; those sockets have no children.

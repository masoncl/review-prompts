- `struct sock` carries no marker for lockless members: `include/net/sock.h`
  does not use `__data_racy`, and the `__cacheline_group_begin()` groups such
  as `sock_write_rx` describe cache layout, not locking.
- The sign is a `READ_ONCE()` of the member somewhere in the tree, or an
  accessor in `include/net/sock.h` that wraps `WRITE_ONCE()`, for example
  `sk_wmem_queued_add()`.
- `sk_flags` has no `WRITE_ONCE()` accessor: `sock_flag()` reads it without
  the lock through `test_bit()`, while `sock_set_flag()` and
  `sock_reset_flag()` are non-atomic `__set_bit()` and `__clear_bit()`.
- **Potentially unsafe usage**: calling `sock_set_flag()` or
  `sock_reset_flag()` on a socket other tasks can reach.
  - Unsafe: when a second writer of `sk_flags` can run at the same time; one
    of the two flag changes is lost.
  - Safe: under `lock_sock()`, as `sock_gettstamp()` in `net/core/sock.c`
    takes the lock only to set one flag.
- Lockless setters in `sk_setsockopt()`: the ones in the first `switch`, before
  `sockopt_lock_sock()`; for example `sock_set_priority()`, which uses
  `WRITE_ONCE()`.

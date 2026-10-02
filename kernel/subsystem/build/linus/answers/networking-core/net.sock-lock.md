- `lock_sock_nested()` uncontended, under `CONFIG_64BIT` when
  `sizeof(struct slock_owned) == sizeof(long)`: one `try_cmpxchg()` on
  `sk->sk_lock.combined` sets `owned` and returns; it takes no spinlock and
  does not disable BH.
- `lock_sock_nested()` when that `try_cmpxchg()` fails, or in other
  configurations: `spin_lock_bh()` on `slock`, wait in `__lock_sock()` if
  owned, set `owned`, `spin_unlock_bh()`.
- `release_sock()`: has no such shortcut; it takes `slock` with
  `spin_lock_bh()` every time.
- `release_sock()` on a socket whose `release_cb` is `tcp_release_cb()`:
  `tcp_release_cb_cond()` in `include/net/tcp.h` calls it directly, and only
  when `sk->sk_tsq_flags` has a `TCP_DEFERRED_ALL` bit; other protocols that
  set `release_cb` get `sk->sk_prot->release_cb()` on every release.
- `bh_lock_sock()` and `bh_lock_sock_nested()`: plain `spin_lock()`, BH is not
  disabled; process context disables BH first, as `__tcp_close()` does with
  `local_bh_disable()`.

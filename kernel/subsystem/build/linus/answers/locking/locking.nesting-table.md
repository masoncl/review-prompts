- `spinlock_t`, `rwlock_t` and `local_lock_t`: one level; each may be taken
  while holding any of the others (all carry `LD_WAIT_CONFIG`).
- `Documentation/locking/locktypes.rst` ("Lock type nesting rules"): states the
  rule for the lock rows only; the file never mentions RCU.
- RCU rows: stated in `Documentation/RCU/Design/Requirements/Requirements.rst`,
  quick quiz "What about sleeping locks?": sleeping locks are forbidden in a
  read-side section, RT `spinlock_t` is allowed, and `mutex_trylock()` is legal
  there.
- `Documentation/RCU/checklist.rst`: does not say which lock types may be
  taken in a read-side section; item 13 says only that blocking is permitted
  in SRCU readers, unlike most flavors of RCU.
- RCU flavours differ:

| Held | `raw_spinlock_t` | `spinlock_t`, `rwlock_t`, `local_lock_t` | `struct mutex` |
|---|---|---|---|
| `rcu_read_lock()` | ok | ok | no |
| `rcu_read_lock_bh()` | ok | ok | no |
| `rcu_read_lock_sched()` | ok | no | no |

- Full matrix, hardirq and softirq contexts included: the comment table above
  `wait_context_tests()` in `lib/locking-selftest.c`; those tests run only with
  `CONFIG_PROVE_RAW_LOCK_NESTING`.

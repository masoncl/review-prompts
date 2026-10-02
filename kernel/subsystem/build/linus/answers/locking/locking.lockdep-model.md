- Wait-context rule: `check_wait_context()` in `kernel/locking/lockdep.c` is
  built under `CONFIG_PROVE_LOCKING` and reports "Invalid wait context", for
  example for a mutex taken under a spinlock.
- Static lock with no key: `assign_lock_key()` uses the address of the lock
  itself as the key.
- Per-CPU static lock: the key is the canonical address with the per-CPU
  offset removed, so the copies on all CPUs are one class.
- Trylock acquisition: `validate_chain()` records no "held lock -> new lock"
  edge for it and runs no recursion check.
- Lock held through a trylock: `check_prevs_add()` still uses it as the source
  of an edge to a lock taken later without trylock.
- First lock taken in a new irq context: `separate_irq_context()` makes it a
  chain head, so no edge is recorded from the locks of the interrupted
  context; the irq usage bits cover that case.

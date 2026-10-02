- Lock state: all three kinds (`REF_TYPE_LOCK`, `REF_TYPE_RES_LOCK`,
  `REF_TYPE_RES_LOCK_IRQ`) are `refs[]` entries and share `active_locks`,
  `active_lock_id` and `active_lock_ptr` in `struct bpf_verifier_state`.
- `active_lock_id` and `active_lock_ptr`: name the most recently taken lock;
  `release_lock_state()` resets them to the previous lock entry.
- Unlock order: last in, first out across both lock kinds;
  `process_spin_lock()` fails with "cannot be out of order" otherwise.
- `process_spin_lock()`: tests no nesting depth for res locks.
- Helper and kfunc calls while `active_locks` is nonzero, for either lock
  kind: `do_check_insn()` allows only helpers `BPF_FUNC_spin_unlock` and
  `BPF_FUNC_kptr_xchg`, and kfuncs flagged `KF_SPINLOCK_SAFE`.
- `kfunc_spin_allowed()`: tests the `KF_SPINLOCK_SAFE` flag, not a fixed list;
  search for the flag, which also marks for example `bpf_arena_alloc_pages()`
  and `bpf_stream_vprintk()`.
- Mixing: `bpf_spin_lock()` cannot be taken with any lock held, since
  `BPF_FUNC_spin_lock` is not an allowed helper; `bpf_res_spin_lock()` can be
  taken while a `struct bpf_spin_lock` is held.
- Sleepable kfunc with `KF_SPINLOCK_SAFE`: still rejected under a lock,
  because `in_sleepable_context()` is false.
- `check_resource_leak()`: called with `check_lock` true for tail call,
  `BPF_LD_ABS`, `BPF_LD_IND` and `bpf_throw()`, and for `BPF_EXIT` only in
  frame 0; it then rejects when `active_locks` is nonzero.
- `BPF_EXIT` from a static subprog with a lock held: allowed; the caller
  inherits the lock.
- Program types, in `check_map_prog_compatibility()`:

| Map value has | Rejected for |
|---|---|
| `BPF_SPIN_LOCK` or `BPF_RES_SPIN_LOCK` | `BPF_PROG_TYPE_SOCKET_FILTER` |
| `BPF_SPIN_LOCK` | types in `is_tracing_prog_type()` |

- `is_tracing_prog_type()`: does not include `BPF_PROG_TYPE_TRACING`.
- While a lock is held: `in_rcu_cs()` is true, so a pointer load is typed as
  inside an RCU region (`MEM_RCU` where the field allows it), even in a
  sleepable program.
- Unlock: after `invalidate_non_owning_refs()`, `process_spin_lock()` calls
  `invalidate_rcu_protected_refs()` if no RCU-like region remains.
- RCU region counter in `struct bpf_verifier_state`: the field is
  `active_rcu_locks`.

| Kind (flavor bit) | Acquire / release | For | Domain declared with | Release in another context |
|---|---|---|---|---|
| Normal (`SRCU_READ_FLAVOR_NORMAL`) | `srcu_read_lock()` / `srcu_read_unlock()` | default; not for NMI | `DEFINE_SRCU()`, `DEFINE_STATIC_SRCU()`, `init_srcu_struct()` | no, lockdep tracks the holder |
| Normal, semaphore-like (same bit) | `srcu_down_read()` / `srcu_up_read()` | hand-off to another task or irq; not for NMI | same as normal; may share a domain with `srcu_read_lock()` | yes, no lockdep call |
| NMI-safe (`SRCU_READ_FLAVOR_NMI`) | `srcu_read_lock_nmisafe()` / `srcu_read_unlock_nmisafe()` | NMI handlers | same as normal, no special declaration | no, lockdep tracks the holder |
| Fast (`SRCU_READ_FLAVOR_FAST`) | `srcu_read_lock_fast()` / `srcu_read_unlock_fast()` | no `smp_mb()` in the reader; allowed in NMI; RCU must be watching | `DEFINE_SRCU_FAST()`, `DEFINE_STATIC_SRCU_FAST()`, `init_srcu_struct_fast()` | no, lockdep tracks the holder |
| Fast-updown (`SRCU_READ_FLAVOR_FAST_UPDOWN`) | `srcu_read_lock_fast_updown()` / `srcu_read_unlock_fast_updown()`; `srcu_down_read_fast()` / `srcu_up_read_fast()` | fast reader that can be handed off; not for NMI; RCU must be watching | `DEFINE_SRCU_FAST_UPDOWN()`, `DEFINE_STATIC_SRCU_FAST_UPDOWN()`, `init_srcu_struct_fast_updown()` | only the down/up pair |

- There is no lite kind here: no srcu_read_lock_lite() and no
  SRCU_READ_FLAVOR_LITE.
- `srcu_down_read_fast()` and `srcu_up_read_fast()`: pass
  `SRCU_READ_FLAVOR_FAST_UPDOWN`, so they go with
  `srcu_read_lock_fast_updown()` domains and, under `CONFIG_PROVE_RCU`, WARN on
  a `DEFINE_SRCU_FAST()` domain; `uretprobes_srcu` in
  `kernel/events/uprobes.c` is an example.
- `srcu_read_lock_notrace()` and `srcu_read_lock_fast_notrace()`: same flavor
  bits as normal and fast, no lockdep call; the fast one also has no
  `rcu_is_watching()` test.
- `CONFIG_NEED_SRCU_NMI_SAFE`: when set, the NMI-safe and both fast kinds
  count with `atomic_long_inc()` while the normal kind still uses
  `this_cpu_inc()` on the same counters.
- In-NMI WARNs: `srcu_down_read()` and `srcu_up_read()` WARN unconditionally;
  the normal and fast-updown readers WARN only under `CONFIG_PROVE_RCU`.
- `srcu_check_read_flavor()`: does nothing without `CONFIG_PROVE_RCU`, and is
  an empty macro under `CONFIG_TINY_SRCU`; there is no
  srcu_check_read_flavor_force().
- `__srcu_check_read_flavor()` in `kernel/rcu/srcutree.c`: records the flavor
  in the `srcu_reader_flavor` field of the running CPU's `struct srcu_data`,
  and WARNs if that CPU already holds a different one.
- Mixing across CPUs that the declaration checks below do not catch: reported
  only by the grace-period scan, "Mixed reader flavors" in
  `srcu_readers_unlock_idx()` and `srcu_readers_lock_idx()`, also only under
  `CONFIG_PROVE_RCU`.
- Declaration checks in `__srcu_check_read_flavor()`: WARN when the domain was
  declared with a flavor and the reader's differs, and WARN for a
  `SRCU_READ_FLAVOR_FAST` reader on a domain declared with none.
- `SRCU_READ_FLAVOR_FAST_UPDOWN` reader on a domain declared with none:
  `__srcu_check_read_flavor()` has no test for it.
- Without `CONFIG_PROVE_RCU`: the per-CPU `srcu_reader_flavor` is never
  written, so `srcu_readers_active_idx_check()` chooses `synchronize_rcu()` or
  `smp_mb()` from `ssp->srcu_reader_flavor`, the declaration, alone.
- **Unsafe usage**: a fast or fast-updown reader on a domain not declared with
  the matching flavor.
  - Unsafe: without `CONFIG_PROVE_RCU`, on a domain declared with no flavor
    the scan uses `smp_mb()` while the reader has only `barrier()`, and
    nothing reports it.
  - Safe: `tracepoint_srcu` in `kernel/tracepoint.c` is declared with
    `DEFINE_SRCU_FAST()`, which sets `SRCU_READ_FLAVOR_FAST` in
    `ssp->srcu_reader_flavor`, and read with `guard(srcu_fast_notrace)`.
  - Safe: `uretprobes_srcu` is declared with `DEFINE_STATIC_SRCU_FAST_UPDOWN()`
    and read with `srcu_down_read_fast()`.

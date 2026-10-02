- `kernel/locking/lockdep_states.h`: lists `HARDIRQ` and `SOFTIRQ` only;
  reclaim is not a state and has no usage bits.
- Usage characters: `get_usage_chars()` returns four, in the order hardirq
  write, hardirq read, softirq write, softirq read.
- `-{n:n}` after the usage characters: outer and inner wait type from
  `enum lockdep_wait_type`, printed by `print_lock_name()`; it is not irq
  state.
- `LOCK_ENABLED_*` bits: `mark_held_locks()` also sets them on every held lock
  with `check` set at the moment interrupts are enabled, not only on locks
  acquired with interrupts on.
- `LOCK_ENABLED_SOFTIRQ`: `mark_usage()` sets it only if hardirqs are on as
  well, so a class that is only ever held with hardirqs off never becomes
  softirq-unsafe.
- Trylock in interrupt context: `mark_usage()` sets no `LOCK_USED_IN_*` bit;
  it still sets the `LOCK_ENABLED_*` bits.
- Hardirq-enabled at acquire: `lock_acquire()` takes it from the CPU flags
  saved by `raw_local_irq_save()`; in-hardirq, in-softirq and
  softirq-enabled come from lockdep's own per-CPU and per-task state.
- Two-lock inversion: `check_irq_usage()` looks for any irq-safe class that
  reaches the held lock and any irq-unsafe class reachable from the new lock,
  so the two classes named in the report need not be the two being nested.
- Reports for one inversion:

  | Found when | Function | Heading |
  |---|---|---|
  | the edge is added | `check_irq_usage()` | "-safe -> -unsafe lock order detected" |
  | a usage bit is set later | `check_usage_forwards()`, `check_usage_backwards()` | "possible irq lock inversion dependency detected" |

- NMI: `verify_lock_unused()` reports a non-trylock acquire in NMI of a class
  that already has `LOCK_USED` set (or `LOCK_USED_READ`, for a write
  acquire), as "inconsistent {INITIAL USE} -> {IN-NMI} usage"; it keeps no
  usage bit for NMI.

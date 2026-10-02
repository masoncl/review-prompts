Rows where this tree differs from the usual picture;
every other non-fast `ktime_get` accessor declared in
`include/linux/timekeeping.h` loops on `tk_core.seq` and can spin forever in
NMI.

| Accessor | Clock | NMI and tracing |
|---|---|---|
| `ktime_get_seconds()` | `CLOCK_MONOTONIC` seconds | plain read of `ktime_sec` on 32-bit and 64-bit, no seqcount; `WARN_ON()` if suspended; not `notrace` |
| `ktime_get_real_seconds()` | `CLOCK_REALTIME` seconds | `CONFIG_64BIT`: one `READ_ONCE()`; 32-bit: `tk_core.seq` loop, can spin |
| `__ktime_get_real_seconds()` | `CLOCK_REALTIME` seconds | `noinstr`, no seqcount on any arch; 64-bit `xtime_sec` unprotected on 32-bit |
| `ktime_get_boottime_seconds()`, `ktime_get_clocktai_seconds()` | `CLOCK_BOOTTIME`, `CLOCK_TAI` seconds | `tk_core.seq` loop through `ktime_get_coarse_with_offset()`; can spin |
| `ktime_get_real_fast_ns()` | `CLOCK_REALTIME` | latch, does not spin; not `notrace` |
| `ktime_get_aux()`, `ktime_get_aux_ts64()` | one `CLOCK_AUX` id | seqcount of that aux `struct tk_data`; can spin |
| `ktime_get_coarse_real_ts64_mg()`, `ktime_get_real_ts64_mg()` | `CLOCK_REALTIME` with a floor | `tk_core.seq` loop; can spin |
| `ktime_get_snapshot_id()` | clock id passed in | seqcount of the selected `struct tk_data`; can spin |

- There is no ktime_get_tai_seconds(); the `CLOCK_TAI` seconds accessor is
  `ktime_get_clocktai_seconds()` in `include/linux/timekeeping.h`.
- ktime_get_raw_seconds is defined nowhere; only
  `Documentation/core-api/timekeeping.rst` names it.
- `CLOCK_MONOTONIC_RAW` has no coarse accessor either; the accessors named
  for it are `ktime_get_raw()`, `ktime_get_raw_ns()`, `ktime_get_raw_ts64()`
  and `ktime_get_raw_fast_ns()`.
- There is no ktime_get_snapshot(); `ktime_get_snapshot_id()` in
  `kernel/time/timekeeping.c` does that job and leaves `valid` false when
  `timekeeping_suspended` is set.
- `__ktime_get_real_seconds()`: the accessor for restricted contexts; its
  callers are in `arch/x86/kernel/cpu/mce/core.c` and
  `kernel/debug/kdb/kdb_main.c`.
- `ktime_get_real_fast_ns()`: reads `base_real` from `tk_fast_mono` inside
  the latch loop, so base and realtime offset are consistent with each other.
- `ktime_get_boot_fast_ns()` and `ktime_get_tai_fast_ns()`: add `offs_boot`
  or `offs_tai` read with `data_race()` outside the latch loop; the offset
  can be newer than the base, and torn on 32-bit.
- `ktime_get_real_fast_ns()` is not in `trace_clocks[]` in
  `kernel/trace/trace.c`; the four `notrace` fast accessors are.
- `tk_core.seq` is write-held only inside `timekeeping_update_from_shadow()`
  and `tk_update_leap_state_all()`; the rest of `__timekeeping_advance()`
  works on `shadow_timekeeper` with only the lock held.
- `WARN_ON(timekeeping_suspended)` is not in every non-fast accessor; for
  example `ktime_get_raw()`, `ktime_get_raw_ts64()`,
  `ktime_get_coarse_ts64()`, `ktime_get_coarse_real_ts64()` and
  `ktime_get_real_seconds()` have none.
- `ktime_get_aux()` and `ktime_get_aux_ts64()`: `__must_check`, return
  `false` when the id is not an aux clock or the clock is not enabled;
  without `CONFIG_POSIX_AUX_CLOCKS` they are stubs that return `false`.
- `ktime_get_coarse_real_ts64_mg()` and `ktime_get_real_ts64_mg()`: for
  filesystem timestamps only; callers are in `fs/inode.c`; not exported.

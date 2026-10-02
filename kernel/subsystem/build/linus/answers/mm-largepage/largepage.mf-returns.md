- 0: `action_result()` in `mm/memory-failure.c` returns it only for
  `MF_RECOVERED` and `MF_DELAYED`; `MF_IGNORED` and `MF_FAILED` give `-EBUSY`.
- `-EOPNOTSUPP`: every such return from `memory_failure()` comes from
  `hwpoison_filter()`.
- `MF_SOFT_OFFLINE`: not a `memory_failure()` case; `memory_failure_work_func()`
  sends those entries to `soft_offline_page()`.
- `-EIO` from `get_hwpoison_page()`: never reaches the caller; `memory_failure()`
  turns it into `action_result()` with `MF_IGNORED`, so `-EBUSY`.
- `-EHWPOISON` has two sources in `mm/memory-failure.c`:
  - the page, or the hugetlb folio that holds it, was already poisoned;
  - a first error hit a large folio that could not be split to order 0, after
    `kill_procs_now()` ran.
- Already-poisoned page with `MF_ACTION_REQUIRED`: the return value is that of
  `kill_accessing_process()`:

| Value | Meaning |
|---|---|
| 0 | the walk found no entry for the pfn in `current`; no signal sent |
| `-EHWPOISON` | the walk found the pfn |
| `-EFAULT` | `current->mm` is NULL |

- `-ENXIO`: also returned by `mf_generic_kill_procs()` for
  `MEMORY_DEVICE_PRIVATE` and `MEMORY_DEVICE_COHERENT`.
- `kill_me_maybe()` on `-EHWPOISON` or `-EOPNOTSUPP`: returns at once; it sends
  no signal and makes no further check.
- `memory_failure_cb()` in `drivers/acpi/apei/ghes.c`: makes the same test as
  `kill_me_maybe()`; quiet on 0, `-EHWPOISON`, `-EOPNOTSUPP`, else
  `force_sig(SIGBUS)`.
- `arch/arm64`: has no call to `memory_failure()`; it goes through
  `drivers/acpi/apei/ghes.c`.
- `enum mf_result` in `include/linux/mm.h`: `MF_IGNORED` is 0, so a raw result
  passed on would read as success; convert with `action_result()`.
- `-ENOENT` from `try_memory_failure_hugetlb()`: means "not hugetlb, carry on";
  `memory_failure()` consumes it and never returns it.

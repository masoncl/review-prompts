- Default: `all` exits with the product of the per-directory statuses,
  starting from `ret=1`. The status is zero as soon as one directory builds,
  so one failed directory does not fail make.
- `FORCE_TARGETS` set: each sub-make is followed by `|| exit`, so the first
  failing directory stops the loop and make fails.
- `FORCE_TARGETS` is tested with `$(if ...)`: any non-empty value enables it,
  `FORCE_TARGETS=0` included.
- Empty list: `ret` stays 1 and `all` fails. `make TARGETS=bpf` with the
  default `SKIP_TARGETS` ends this way.
- `install`: depends on `all`, then runs its own loop with the same product
  and the same `FORCE_TARGETS` test.
- A non-zero status from the `install` loop stops the recipe after
  `kselftest-list.txt` was removed and before it is written again.

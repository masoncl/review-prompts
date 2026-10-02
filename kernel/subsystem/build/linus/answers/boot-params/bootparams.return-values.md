- `__setup()` handler returning 0 for a bad value: the word is treated as
  unclaimed; see "Unclaimed words".
- `__setup()` example returning 1: `set_reset_devices()` and `init_setup()` in
  `init/main.c`; `quiet_kernel()` and `debug_kernel()` are `early_param()`
  handlers and return 0.
- `early_param()` handler returning non-zero: only the `pr_warn()`;
  `obsolete_checksetup()` still counts the word as handled.
- `parse_args()` after a failing word: goes on to the next word; `err` is
  overwritten each time, so the value returned is the last error.
- `parse_args()` messages: "Unknown parameter" for `-ENOENT`, "too large for
  parameter" for `-ENOSPC`, "invalid for parameter" for any other non-zero
  value.
- Set function returning a positive value: logged as invalid and stored with
  `ERR_PTR()`; `IS_ERR_OR_NULL()` in `start_kernel()` does not recognise it, so
  if it is the last error `start_kernel()` passes it to `parse_args()` as the
  init-argument string.

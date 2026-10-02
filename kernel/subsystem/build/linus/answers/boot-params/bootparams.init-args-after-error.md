- `parse_args()`: does not stop at the failing word; it parses up to `--` and
  there returns `err ?: args`.
- Words after `--`: `start_kernel()` skips them when `after_dashes` is an
  error (`IS_ERR_OR_NULL()` test); nothing is logged about them, the only
  message is the `pr_err()` for the failing word.
- `extra_init_args` from bootconfig: still passed to `set_init_arg()`; that
  call does not test `after_dashes`.
- Source of the error: only a word whose name matches a `struct kernel_param`
  of level -1, because `unknown_bootoption()` returns 0 on every path.

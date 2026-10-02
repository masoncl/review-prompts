- Models take every boolean parameter to accept a bare word. In
  `kernel/params.c` only `param_ops_bool`, `param_ops_bool_enable_only` and
  `param_ops_bint` set `KERNEL_PARAM_OPS_FL_NOARG`; `param_ops_invbool` and
  ops built by `module_param_call()` do not, so `parse_one()` gives `-EINVAL`.
- Models take `core_param_cb()` to be `core_param()` with custom ops. It is
  the level 1 macro and keeps `MODULE_PARAM_PREFIX`; the unprefixed level -1
  form is `__core_param_cb()` in `include/linux/moduleparam.h`, as
  `kernel/panic.c` uses.
- Models take `scripts/checkpatch.pl` to check a `__setup()` name against the
  tree. `UNDOCUMENTED_SETUP` searches only the `+` lines the same patch adds
  to `Documentation/admin-guide/kernel-parameters.txt`.
- Models take any string to be a legal `MODULE_PARAM_PREFIX`.
  `__module_param_call()` has a `static_assert` that the prefix is no longer
  than `__MODULE_NAME_LEN`.
- Models take the command line to be parsed only from `start_kernel()` and
  `do_initcall_level()`. `dynamic_debug_init()` (an `early_initcall`) and
  `bootconfig_cmdline_requested()` each run their own `parse_args()` pass;
  search for `parse_args(` to list the rest.
- Models take `hugepages`, `hugepagesz` and `default_hugepagesz` to be
  handled when parsed. `hugetlb_early_param()` in `mm/hugetlb.c` only copies
  the value; `hugetlb_parse_params()` runs the real handlers later.
- Models take "Kernel command line:" to be one log line.
  `print_kernel_cmdline()` in `init/main.c` splits it at spaces according to
  `CONFIG_CMDLINE_LOG_WRAP_IDEAL_LEN`, each piece with the prefix repeated.

- `syscon_list_lock`: a mutex, not a spinlock; there is no syscon_list_slock
  in this tree.
- `device_node_get_regmap()`: holds the mutex across the list search and
  `of_syscon_register()`, so two first lookups of one node create one regmap.
- Lookups need no `struct device`, so they also run from early init code, for
  example `at91sam9rl_pmc_setup()` declared with `CLK_OF_DECLARE()`.

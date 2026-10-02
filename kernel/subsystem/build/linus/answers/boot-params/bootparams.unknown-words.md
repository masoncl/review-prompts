- `unknown_bootoption()` tests, in order:
  - `sysctl_is_alias()` on the name alone: claimed, `unknown_bootoption()`
    returns 0.
  - `repair_env_string()`.
  - word starts with `BOOT_IMAGE=` or `kexec`: dropped.
  - `obsolete_checksetup()`.
  - `.` in the name: dropped.
  - `panic_later` set: dropped.
- `kexec` test: `strstarts()`, so any word beginning with `kexec` is dropped
  before `obsolete_checksetup()` and is neither logged nor passed to init; a
  `__setup()` string with that start never runs.
- `.` test: covers the name only (`len` is taken before
  `repair_env_string()`); a `.` in the value does not count.
- `init_setup()` and `rdinit_setup()`: clear `argv_init[1]` onwards, so bare
  unknown words that came before `init=` or `rdinit=` are neither passed to
  init nor logged.
- `print_unknown_bootoptions()`: there is no counter; it returns early when
  `panic_later` is set or when `argv_init[1]` and `envp_init[2]` are both
  NULL.
- Log output: one `pr_notice()` for all words, no line per word.
- Logged text: the words as modified in place in `static_command_line`
  (quotes stripped), not text from `saved_command_line`.

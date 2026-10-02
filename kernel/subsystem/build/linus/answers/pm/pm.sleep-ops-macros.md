- "Deprecated" in `include/linux/pm.h`: only two macros carry the word.

| Marked deprecated | Named in its place | Defined in |
|---|---|---|
| `SIMPLE_DEV_PM_OPS()` | `DEFINE_SIMPLE_DEV_PM_OPS()` | `include/linux/pm.h` |
| `UNIVERSAL_DEV_PM_OPS()` | `DEFINE_RUNTIME_DEV_PM_OPS()` | `include/linux/pm_runtime.h` |

- `SET_SYSTEM_SLEEP_PM_OPS()`, `SET_LATE_SYSTEM_SLEEP_PM_OPS()`,
  `SET_NOIRQ_SYSTEM_SLEEP_PM_OPS()`, `SET_RUNTIME_PM_OPS()`: no deprecation
  comment and no named replacement in `include/linux/pm.h`.
- Those four macros: each expands to the macro of the same name without the
  `SET_` prefix under `CONFIG_PM_SLEEP` (`CONFIG_PM` for
  `SET_RUNTIME_PM_OPS()`), and to nothing otherwise.
- DEFINE_UNIVERSAL_DEV_PM_OPS(): not in this tree.
- `RUNTIME_PM_OPS()`: assigns `runtime_suspend`, `runtime_resume` and
  `runtime_idle` bare, with no `pm_ptr()`.
- Runtime callbacks set through `RUNTIME_PM_OPS()`: become unreferenced
  without `CONFIG_PM` when the struct is `static` and referenced only through
  `.pm = pm_ptr(&ops)`.
- `pm_ptr()` and `pm_sleep_ptr()`: `include/linux/pm.h` has no comment saying
  where each goes; the mechanism is described in the `PTR_IF()` kerneldoc in
  `include/linux/util_macros.h`.
- Exported structs: the symbol exists only under the option the export macro
  keys on; otherwise `_DISCARD_PM_OPS()` emits a static `__static_##name`.

| Export family | Symbol defined under | Wrapper for `.pm` |
|---|---|---|
| `EXPORT_DEV_SLEEP_PM_OPS()`, `EXPORT_SIMPLE_DEV_PM_OPS()` and their GPL and NS forms, for example `EXPORT_NS_GPL_SIMPLE_DEV_PM_OPS()` | `CONFIG_PM_SLEEP` | `pm_sleep_ptr()` |
| `EXPORT_DEV_PM_OPS()`, `EXPORT_RUNTIME_DEV_PM_OPS()` and their GPL and NS forms, for example `EXPORT_NS_GPL_RUNTIME_DEV_PM_OPS()` | `CONFIG_PM` | `pm_ptr()` |

- `pm_ptr()` around a struct from the `CONFIG_PM_SLEEP` family: with
  `CONFIG_PM=y` and `CONFIG_PM_SLEEP=n` the reference survives and the symbol
  has no definition.

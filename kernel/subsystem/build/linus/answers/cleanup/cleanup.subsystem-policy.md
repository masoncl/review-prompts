- `Documentation/process/maintainer-netdev.rst`, section "Using
  device-managed and cleanup.h constructs", is the only document under
  `Documentation/` (translations aside) that restricts the helpers.

| Construct | What the section says |
|---|---|
| all "auto-cleanup" APIs, `devm_` included | "not the preferred style of implementation, merely an acceptable one" |
| `guard()` | discouraged in any function longer than 20 lines |
| `scoped_guard()` | "considered more readable" |
| plain lock/unlock | "still (weakly) preferred" |
| `__free()` | usable when building APIs and helpers, "especially scoped iterators"; direct use in networking core and drivers discouraged |
| mid-function declarations | one sentence: "Similar guidance applies to declaring variables mid-function." |

- The section has no maintainer-approval exception.
- "Clean-up patches" section of the same file: lists conversions to `devm_`
  helpers among discouraged standalone clean-ups; it does not list
  conversions to cleanup.h constructs.
- Reverse-xmas-tree ordering: a separate section of the same file ("Local
  variable ordering"); the cleanup section does not refer to it.
- `Documentation/dev-tools/checkpatch.rst`, under
  `UNINITIALIZED_PTR_WITH_FREE`: says the opposite for `__free()` pointers,
  that the declarations-at-top rule "can be relaxed"; this and the DOC block in
  `include/linux/cleanup.h` conflict with the netdev sentence on mid-function
  declarations.
- `Documentation/RCU/checklist.rst` and
  `Documentation/hwmon/hwmon-kernel-api.rst`: present the `guard()` and
  `scoped_guard()` forms as available, with no restriction.

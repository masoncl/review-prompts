| Rule | Strength | Where |
|---|---|---|
| Local variable order | Stated as "a convention", given as an imperative; no word of refusal | `Documentation/process/maintainer-netdev.rst` |
| `guard()` | Discouraged in a function longer than 20 lines; plain lock/unlock "(weakly) preferred" | `Documentation/process/maintainer-netdev.rst` |
| `__free()` | Allowed when building APIs and helpers; direct use in core and drivers discouraged | `Documentation/process/maintainer-netdev.rst` |
| `devm_` helpers | Allowed with no condition: "not the preferred style of implementation, merely an acceptable one" | `Documentation/process/maintainer-netdev.rst` |
| Stand-alone clean-up patches | Discouraged, not refused | `Documentation/process/maintainer-netdev.rst` |
| Exports meant only for the core | Allowed under a condition on who uses the symbol | `Documentation/networking/netdevices.rst` |

- None of the `Documentation/process/maintainer-netdev.rst` rules in the table
  is worded as a refusal; where the document objects, its word is
  "discouraged" or "discourages".
- Scope-based cleanup: the document sets no condition about maintainer agreement
  or about code that already uses it.
- Clean-up patches: the discouraged examples are `checkpatch.pl` and trivial
  style fixes, variable-order fixes and `devm_` conversions.
- Spelling and grammar fixes: "not discouraged", so a typo-only patch is not a
  clean-up in this sense.
- `Documentation/process/maintainer-netdev.rst`: has no text on exports, symbol
  namespaces or core-only symbols.
- `NETDEV_INTERNAL` section of `Documentation/networking/netdevices.rst`:
  symbols "can only be used in networking core and drivers which exclusively
  flow via the main networking list and trees".
- `NETDEV_INTERNAL` section: states who may use the symbols and says nothing
  about `MODULE_IMPORT_NS()`.
- EXPORT_IPV6_MOD does not exist in this tree; core-only exports are written
  `EXPORT_SYMBOL_NS_GPL(sym, "NETDEV_INTERNAL")`, for example in
  `net/core/dev.c`.

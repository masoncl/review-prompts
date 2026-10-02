- Precedence in `led_compose_name()`, first match wins:

  | Source | Name |
  |---|---|
  | `label` | `label`, or `devicename:label` if `devicename` set |
  | `function` or valid `color` | `color:function`, `-N` appended when `function-enumerator` was read |
  | `init_data->default_label` | `devicename:default_label` |
  | OF node | node name |
  | software node | `fwnode_get_name()` |

- `function-enumerator`: read only when `function` is present.
- `function`/`color` row: the colon is always printed, a missing part is
  empty; `devicename:` is prepended only with `devname_mandatory`.
- Output: `snprintf()` into the caller's buffer of `LED_MAX_NAME_SIZE`;
  nothing is allocated.
- Too long: `-E2BIG`, for the final name and for the intermediate
  `color:function` string; the name is never silently truncated here.
- `-EINVAL` cases:
  - NULL output buffer;
  - `default_label` reached with NULL `devicename`;
  - no source and the node is neither OF nor software node, including a
    NULL `fwnode`.
- `devname_mandatory` without `devicename`: checked only in
  `led_classdev_register_ext()`; `led_compose_name()` itself has no such
  test, and it is exported and called directly by
  `pci_npem_set_led_classdev()` in `drivers/pci/npem.c`.

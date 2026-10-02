- `set` and `set_multiple` in `struct gpio_chip`: return `int`; the tree has
  no void setter and no set_rv member.

| Callback | Wrapper | Value outside the permitted set |
|---|---|---|
| `get` | `gpiochip_get()` | above 1: `gpiochip_warn()`, then becomes 1 |
| `get_multiple` | `gpio_chip_get_multiple()` | above 0: `-EBADE` |
| `set` | `gpiochip_set()` | above 0: `-EBADE` |
| `set_multiple` | `gpiochip_set_multiple()` | above 0: `-EBADE` |
| `direction_input` | `gpiochip_direction_input()` | above 0: `-EBADE` |
| `direction_output` | `gpiochip_direction_output()` | above 0: `-EBADE` |
| `get_direction` | `gpiochip_get_direction()` | above 1: `-EBADE` |

- `gpiochip_get()`: the only wrapper that keeps a bad value as success, and
  the only one that logs it.
- `-EBADE` conversions: silent in the wrapper, no `WARN_ON()` and no message.
- `WARN_ON()` in the wrappers: fires only when the callback pointer is NULL,
  and the wrapper returns `-EOPNOTSUPP`; `gpiochip_get()` has no such test,
  its caller `gpio_chip_get_value()` returns `-EIO`.
- `gpio_chip_get_multiple()` and `gpiochip_set_multiple()` without the
  multiple callback: loop over `gpiochip_get()` or `gpiochip_set()`, so the
  per-line handling above applies.
- Registration in `gpiochip_add_data_with_key()`: calls `gc->get_direction()`
  directly and stores `!ret`, so a negative errno or any other non-zero
  value marks the line as input; no `-EBADE`.

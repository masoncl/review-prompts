- Values: `split`, `per-op`, `global`; there is no other value.

| Value | Policies | Op table |
|---|---|---|
| `global` | one, over the request attributes of all ops | `struct genl_small_ops` |
| `per-op` | one per op and mode that has a request, as under `split` | `struct genl_ops` |
| `split` | one per op and mode that has a request | `struct genl_split_ops` |

- `global`: `_load_global_policy()` raises unless every op that has an
  `attribute-set` uses the same one.
- `global`: op table entries carry no policy; the hand-written
  `struct genl_family` must set `.policy` and `.maxattr`, as
  `net/ipv4/fou_core.c` does with `fou_nl_policy`.
- `per-op`: `print_kernel_op_table()` builds each entry's `.policy` and
  `.maxattr` from the `do` request attributes only.
- `pre` and `post`: put into the op table only under `split`; under `global`
  and `per-op` the generator only declares the hook prototypes in the
  header.

| Source | Default |
|---|---|
| `Documentation/core-api/netlink.rst` | `per-op` |
| `Family.resolve()` in `tools/net/ynl/pyynl/ynl_gen_c.py` | `split` |
| schema description of `kernel-policy` | `split` |

- Accepted by `Documentation/netlink/genetlink-legacy.yaml` and
  `Documentation/netlink/netlink-raw.yaml` only.
- `genetlink.yaml` and `genetlink-c.yaml`: set `additionalProperties: False`
  at the top level, so a spec with `kernel-policy` fails validation and
  those levels always get `split`.

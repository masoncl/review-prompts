- Spec-level `checks` properties: `flags-mask`, `min`, `max`, `min-len`,
  `max-len`, `exact-len`, `unterminated-ok`; `range`, `full-range` and
  `sparse` are keys that `_init_checks()` adds and the schema rejects in a
  spec.
- `unterminated-ok`: switches `NLA_NUL_STRING` to `NLA_STRING`;
  `Documentation/netlink/genetlink.yaml` does not accept it, the other three
  schemas do.
- Big-endian `u16`/`u32`: `Type.attr_policy()` changes the type to
  `NLA_BE16`/`NLA_BE32` and uses the same macros; there is no
  NLA_POLICY_MAX_BE in this tree.
- Precedence in `TypeScalar._attr_policy()`: `flags-mask`, a flags enum or
  `enum-as-flags` first, then full range, range, `min`, `max`, sparse enum;
  with a mask, `min` and `max` are dropped silently.
- Limit outside -32768..32767: `NLA_POLICY_FULL_RANGE()` for every scalar
  type; the generator does not emit `NLA_POLICY_FULL_RANGE_SIGNED()`.
- **Unsafe usage**: a signed attribute type with `min` or `max` outside
  -32768..32767, on a request attribute of a spec that kernel code is
  generated from.
  - Unsafe: the generator pairs `NLA_POLICY_FULL_RANGE()` with a
    `struct netlink_range_validation_signed`;
    `NLA_ENSURE_UINT_OR_BINARY_TYPE()` in `include/net/netlink.h` rejects
    the signed type at build time.
  - Safe: an unsigned type, as `NETDEV_A_PAGE_POOL_IFINDEX` (`NLA_U32`) in
    `net/core/netdev-genl-gen.c`; `NLA_ENSURE_UINT_OR_BINARY_TYPE()`
    accepts unsigned types.

| Type | Check | Initialiser |
|---|---|---|
| string | `max-len` | `{ .type = NLA_NUL_STRING, .len = N, }` |
| string | `exact-len` | `NLA_POLICY_EXACT_LEN(N)` |
| string | `min-len` | ignored by `TypeString._attr_policy()` |
| binary | `max-len` | `NLA_POLICY_MAX_LEN(N)` |

- String with `exact-len`: `NLA_POLICY_EXACT_LEN()` has type `NLA_BINARY`,
  so `max-len` and `unterminated-ok` on the same attribute have no effect.
- `Documentation/core-api/netlink.rst` forms for `max-len`: a literal
  integer, the name of a defined constant, and `CONST - 1` for strings.
- `len-or-define` in the schemas: accepts the `CONST - 1` form.
- `get_limit_str()`: handles the integer and the name; it has no handling
  for ` - 1`, and `c_upper()` turns that `-` into `_`.
- No spec under `Documentation/netlink/specs/` uses the `CONST - 1` form.
- `get_limit_str()` on a constant from `definitions`: prints the bare
  upper-case name when the definition has `header`, otherwise the name
  prefixed with the family name.

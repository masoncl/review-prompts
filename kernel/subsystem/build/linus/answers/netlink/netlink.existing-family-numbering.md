- Neither document states a rule for adding to an existing family; the
  `unspec` advice in `Documentation/core-api/netlink.rst` is addressed to new
  families.
- Nearest statement: the `unspec` value 0 of older families "is supported
  (`type: unused`) but should be avoided in new families".
- `value-start`: a property of `definitions` entries (`enum`, `flags`) only;
  attributes and operations are numbered with per-entry `value`.
- `value` omitted: the entry takes the previous value plus one, so an entry
  appended to the list continues the existing numbering.
- `enum-model`: one property of `operations` for the whole family; a spec
  cannot give one operation a different model.
- `directional` family, `value` omitted: `_dictify_ops_directional()` in
  `tools/net/ynl/pyynl/lib/nlspec.py` continues the request and the
  from-kernel counters separately; explicit values are not required.

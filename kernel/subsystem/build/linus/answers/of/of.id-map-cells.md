- Cell count: read per entry from the entry's target node with
  `of_property_read_u32(phandle_node, cells_name, &cells)`.
- `cells_name`: passed by the caller (`"#iommu-cells"` or `"#msi-cells"` in
  the wrappers); it is not derived from the map name.
- Entry layout: id-base, phandle, `cells` output cells, length; `3 + cells`
  cells, so entries in one map can differ in size.
- Target lacks the property: `cells` is 1.
- Largest count: `MAX_PHANDLE_ARGS`; a larger one returns `-EINVAL` after a
  `pr_err()`.
- Count of 0: accepted; a match sets `args_count` to 0 and writes no
  `args[]`.
- Length check: the property must be a whole number of cells and every entry
  walked must fit; otherwise `-EINVAL`.
- Unresolvable phandle: `-ENODEV` for any entry reached before the match, not
  only the matching one, because the target is needed to size the entry.
- `of_check_bad_map()`: when the first entry's target says 2 cells and the
  whole map parses as 4-cell entries with one phandle and length 1, every
  entry is read as 1-cell, with a `pr_warn_once()`.
- More than one output cell with an entry length above 1: `-EINVAL` when the
  ID falls in that entry.

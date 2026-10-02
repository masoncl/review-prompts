- Unresolved phandle with `cells_name` NULL (`of_parse_phandle()`,
  `of_parse_phandle_with_fixed_args()`, `of_parse_phandle_with_args()` with
  NULL `cells_name`): `__of_parse_phandle_with_args()` returns 0 with
  `out_args->np` NULL; the caller must test `np`.
- Unresolved phandle with `cells_name` set: `-EINVAL` after "could not find
  phandle".
- Any error return from `__of_parse_phandle_with_args()`: `out_args` is not
  written, so `out_args->np` holds whatever the caller left there.
- Empty entry in the iterator: `of_phandle_iterator_next()` returns 0 with
  `it->phandle` 0 and `it->node` NULL; the body of `of_for_each_phandle()`
  runs for it and must not dereference `it->node`.
- Empty entry at the requested index: `__of_parse_phandle_with_args()`
  returns `-ENOENT`.
- `of_for_each_phandle()`: discards the return of
  `of_phandle_iterator_init()`; a missing property, and the case of no
  `cells_name` with a negative `cell_count`, both end the loop with `-ENOENT`.
- `out_args` NULL on success: `__of_parse_phandle_with_args()` puts the node
  itself; the caller has nothing to drop.

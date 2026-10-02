- Non-NULL, non-error return: taken as a different dentry that carries its own
  reference. `__lookup_slow()`, `lookup_one_qstr_excl()` and `lookup_open()`
  `dput()` the passed dentry without comparing the two.
- **Unsafe usage**: `->lookup` returning the dentry it was passed, with no
  reference of its own; the caller's `dput()` drops the only reference to the
  dentry it then uses.
  - Safe: return NULL when the passed dentry was used, as `d_splice_alias()`
    does; `__lookup_slow()` then keeps the passed dentry and its reference.
- NULL return: the passed dentry may be positive, hashed negative, or left
  unhashed; `simple_lookup()` returns NULL without hashing for a casefolded
  directory under `CONFIG_UNICODE`.
- `lookup_one_qstr_excl()`: allocates with `d_alloc()`, not
  `d_alloc_parallel()`, so `->lookup` gets a dentry that is not in-lookup, and
  no `d_lookup_done()` follows. Callers such as `__start_dirop()` hold the
  directory's `i_rwsem` exclusive.
- `->lookup` therefore sees both kinds of dentry; `d_add_ci()` tests
  `d_in_lookup()` to pick `d_alloc_parallel()` or `d_alloc()`.

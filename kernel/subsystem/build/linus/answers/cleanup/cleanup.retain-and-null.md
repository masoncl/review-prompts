- `retain_and_null_ptr()`: defined in `include/linux/cleanup.h` as
  `((void)__get_and_null(p, NULL))`.
- Comment above it, first statement: only for an allocation that is handed in
  to another function and consumed by that function on success.
- Comment above it, second statement: after the call the variable is NULL and
  cannot be dereferenced.
- Comment's example: `ret = bar(f);` with `f` still armed, then
  `retain_and_null_ptr(f)` only under `if (!ret)`.
- Callee behaviour on failure: not stated in the comment; the variable is still
  armed on that path, so `__free()` frees the object and the callee must not
  have freed or kept it.

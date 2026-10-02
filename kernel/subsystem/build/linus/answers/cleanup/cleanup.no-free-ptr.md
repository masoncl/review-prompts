- Ignored value, compile time: `no_free_ptr()` passes the value through
  `__must_check_fn()`, which is `static __always_inline __must_check` in
  `include/linux/cleanup.h`, so a `no_free_ptr(p);` statement draws the
  unused-result warning.
- DOC comment at the top of `include/linux/cleanup.h`: its `init()` example
  writes `no_free_ptr(obj);` as a bare statement; that is the form
  `__must_check_fn()` warns about, and the statement form in this tree is
  `retain_and_null_ptr()`.
- `(void)no_free_ptr(p)`: appears nowhere in this tree.
- NULL test in a `DEFINE_FREE()` expression: a convention, not enforced; after
  `no_free_ptr()` the cleanup still runs with NULL.

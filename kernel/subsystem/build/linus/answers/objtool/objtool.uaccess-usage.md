- What objtool tests: the state at each RET and call instruction, not the C
  `return` statement; a `return` written inside the region is accepted if
  access is ended before the RET.
- **Potentially unsafe usage**: a fault label that returns without calling
  `user_access_end()`.
  - Unsafe: when the region was opened directly with `user_access_begin()` or
    a read/write variant and nothing ends access between the faulting access
    and the RET; `validate_return()` warns "return with UACCESS enabled".
  - Safe: when the region is a scope such as
    `scoped_user_write_access_size()` and the label is outside it;
    `__scoped_user_access()` in `include/linux/uaccess.h` ends access through
    `__cleanup` when the scope is left, as in `filldir()` in `fs/readdir.c`.
  - Safe: when the label is inside an `__always_inline` helper and the caller
    ends access after the helper, as `strncpy_from_user()` does with
    `user_read_access_end()` after `do_strncpy_from_user()`.
- Indirect call in the region, retpoline thunk call included: always warns,
  because `func_uaccess_safe()` returns false for a NULL symbol.
- `tools/objtool/Documentation/objtool.txt`, before adding funcB to
  `uaccess_safe_builtin`: funcB "obviously does not call schedule(), and is
  marked notrace". It states no other condition.
- Other fixes the document lists first: remove the call from the region, or
  put the correct guards around the low-level access helpers.
- Enforced by objtool, not by the document: `validate_symbol()` starts a
  listed function with access on, so each call in its body must target a
  listed function or lie between `user_access_save()` and
  `user_access_restore()`, as in `kasan_report()` in `mm/kasan/report.c`.

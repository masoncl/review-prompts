- `NLA_NUL_STRING` with non-zero `len`: `strlen()` of `nla_data()` is at most
  `len`, so a `len` + 1 byte buffer holds it; `ethnl_parse_header_dev_get()`
  in `net/ethtool/netlink.c` reads it in place.
- `NLA_NUL_STRING` with `len` 0: the string is bounded only by `nla_len()`.
- The NUL guarantee exists only if a parse with that policy entry ran over
  the attribute; a `NULL` policy or a bare for-each walk gives none.
- `nla_strscpy()`: copies by payload length, not up to the first NUL; it
  drops one trailing NUL only, so embedded NULs are copied and counted in the
  return value.
- `nla_strscpy()` into a buffer of policy `len` + 1 bytes: cannot truncate,
  so the return value may be ignored, as `rtnl_dev_get()` in
  `net/core/rtnetlink.c` does.
- `nla_strscpy()` with policy `len` 0 or larger than the buffer minus one:
  can truncate, and then returns `-E2BIG`; the destination is still
  terminated.
- `nla_strscpy()` with `dstsize` above `U16_MAX`: `WARN_ON_ONCE()` and
  `-E2BIG`, nothing copied.
- `nla_strdup()`: allocates the payload length less one trailing NUL, plus 1;
  with no policy `len` the sender chooses the allocation size.
- `nla_strscpy()`, `nla_strdup()`, `nla_strcmp()`: dereference the attribute;
  the caller tests the `tb[]` slot for `NULL` first.

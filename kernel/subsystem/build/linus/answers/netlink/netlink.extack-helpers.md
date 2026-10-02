- `NL_SET_ERR_MSG()` argument: must be a string literal, or a macro that
  expands to one; it initialises `static const char __msg[]`, so a
  `const char *` variable does not compile. There is no __NL_SET_ERR_MSG()
  in this tree.
- `NL_SET_ERR_MSG_FMT()` `fmt` argument: must also be a string literal, since
  it is pasted between `"%s"` literals.
- `NL_SET_ERR_MSG_FMT()` truncation: logged with `net_warn_ratelimited()`,
  with the untruncated text; it is not a `WARN_ON()`.
- `NL_SET_ERR_MSG_FMT_MOD()`: the `KBUILD_MODNAME ": "` prefix counts against
  the `NETLINK_MAX_FMTMSG_LEN` bytes.
- NULL extack, `NL_SET_ERR_MSG()` and `NL_SET_ERR_MSG_ATTR_POL()`:
  `do_trace_netlink_extack()` still runs; only the stores are skipped.
- NULL extack, `NL_SET_ERR_MSG_FMT()` and `NL_SET_ERR_MSG_ATTR_POL_FMT()`:
  nothing runs, not even the tracepoint.
- `NL_SET_BAD_ATTR()`: writes `bad_attr` and also `policy = NULL`, so it
  clears a policy recorded earlier; `NL_SET_ERR_MSG_ATTR()` does the same.

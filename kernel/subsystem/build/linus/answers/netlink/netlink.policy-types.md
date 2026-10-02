- Rows below are only the types whose checks are easy to get wrong; all are
  in `validate_nla()` in `lib/nlattr.c`.

| Type | Liberal | `NL_VALIDATE_STRICT_ATTRS` | `len` |
|---|---|---|---|
| integer types in `nla_attr_len[]` | at least `len` if non-zero, else at least the `nla_attr_minlen[]` size; a size mismatch only warns | exactly the `nla_attr_len[]` size | non-zero `len` replaces the table minimum, it is not added |
| `NLA_MSECS` | at least 8, or at least `len` if non-zero | same as liberal; never exact | as for integers |
| `NLA_STRING` | at least 1 byte; with non-zero `len`, one trailing NUL is dropped, then at most `len` | same | maximum, one trailing NUL not counted; 0 = no limit |
| `NLA_NUL_STRING` | a NUL among the first min(payload, `len` + 1) bytes, then the `NLA_STRING` checks | same | maximum without the NUL; 0 = NUL anywhere, no limit |

- `NLA_MSECS`: is in `nla_attr_minlen[]` but not in `nla_attr_len[]`, so a
  payload longer than 8 bytes passes strict validation.
- `NLA_NUL_STRING`: bytes may follow the first NUL; the payload need not end
  in NUL.
- There are no NLA_EXACT_LEN or NLA_MIN_LEN types here; exact and minimum
  lengths are `NLA_BINARY` entries with `validation_type`
  `NLA_VALIDATE_RANGE` or `NLA_VALIDATE_MIN`, built by
  `NLA_POLICY_EXACT_LEN()` and `NLA_POLICY_MIN_LEN()`.

- The set is exactly four `static inline` functions: `libbpf_err()`,
  `libbpf_err_errno()`, `libbpf_err_ptr()`, `libbpf_ptr()`.
- None of them tests any mode; the comment above `libbpf_err_errno()` that
  mentions strict mode settings does not match its body.
- Inputs a helper does not expect:

| Helper | Given | Result |
|---|---|---|
| `libbpf_err()` | raw `-1` from a syscall or libc call | `errno` becomes 1; returns `-1` |
| `libbpf_err_errno()` | any negative value, including a real `-Exxx` | value discarded; returns `-errno`; never writes `errno` |
| `libbpf_err_ptr()` | 0 or a positive value | `errno` becomes 0 or negative; still returns `NULL` |
| `libbpf_ptr()` | plain `NULL` | returns `NULL`; `errno` untouched |

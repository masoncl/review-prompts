- `fs_put_dax()` with non-NULL `dax_dev` and `holder`: first
  `WRITE_ONCE(dax_dev->holder_ops, NULL)`, unconditionally; then
  `cmpxchg(&dax_dev->holder_data, holder, NULL)`; then
  `WARN_ON(prev && prev != holder)`; no lock is held across these steps.
- `fs_put_dax()` has no test of `holder_data` before it clears `holder_ops`, so
  a mismatched caller removes the real holder's operations.
- `dax_holder_notify_failure()`: never reads `holder_data`; it reads
  `holder_ops` once with `READ_ONCE()` and returns `-EOPNOTSUPP` if NULL, which
  is what a call racing with `fs_put_dax()` gets.
- `kill_dax()` with a holder whose ops are NULL: the holder is told nothing;
  the `-EOPNOTSUPP` is ignored and the holder is cleared all the same.

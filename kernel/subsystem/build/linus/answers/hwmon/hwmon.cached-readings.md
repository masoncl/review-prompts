- `lm90_update_device()` after a failed read: `data->valid` is false (cleared
  before the first read), `data->last_updated` is unchanged, and
  `data->temp[]` can hold a mix of old and new values.
- Only `data->valid` protects readers from that mix, so every callback that
  uses the cache must call `lm90_update_device()` first and return its error;
  all four callers do, the two write helpers included.
- Write paths do not invalidate the cache: `data->valid` is written only in
  `lm90_update_device()`. `lm90_set_temp()`, `lm90_set_temphyst()`,
  `lm90_set_temp_offset()` and `lm90_set_convrate()` update the cached copy
  themselves.
- The limits that `lm90_update_limits()` reads are re-read from the chip only
  while `data->valid` is false, so a write to one of them that skips the
  cached copy stays invisible until a refresh fails.
- `data->alarms`: a bit is cleared by `lm90_temp_read()` when the matching
  alarm attribute is read, and `data->current_alarms` is ORed back in;
  `lm90_report_alarms()` only updates `data->reported_alarms`. The read
  callback therefore writes cached state and relies on the core lock.

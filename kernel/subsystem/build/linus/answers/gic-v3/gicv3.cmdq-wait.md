- `prev_idx` is the sender's raw read of `GITS_CREADR`, taken after the
  commands are built and flushed; it is not derived from the slot that
  `its_allocate_entry()` returned.
- Wrap-around: each poll adds the read pointer's advance since the previous
  poll to `linear_idx`, plus `ITS_CMD_QUEUE_SZ` when the pointer went
  backwards.
- The wait ends when `linear_idx >= to_idx`, not when the read pointer
  leaves a range.
- Timeout: `its_wait_for_range_completion()` returns -1 after printing
  "ITS queue timeout"; `BUILD_SINGLE_CMD_FUNC` then prints "ITS cmd %ps
  failed" and returns `void`.
- `GITS_CREADR` is used unmasked and no stall or error bit is tested, so a
  stalled ITS shows up only as a timeout, here or in
  `its_allocate_entry()`.

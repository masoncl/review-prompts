- Short report after `raw_event`: either zero-padded or rejected with
  `-EINVAL`; see "Feeding input reports" for which.
- `size` against the buffer: the `bufsize < size` test is in
  `hid_report_raw_event()`, so it too runs after `raw_event`.
- Example that tests `size` before indexing: `gfrm_raw_event()` in
  `drivers/hid/hid-gfrm.c` (`size < 2` before `data[1]`).

- `drm_dp_dpcd_read()`: returns `size` or a negative errno, never a smaller
  positive count.
- Short transfer on a local aux: `drm_dp_dpcd_access()` turns it into
  `-EPROTO` and retries, up to 32 tries.
- Short read on a remote aux: `drm_dp_send_dpcd_read()` returns `-EPROTO`.
- `drm_dp_dpcd_write()` on a local aux: same, `size` or negative.
- Error returned after the retries: the first one seen, not the last.
- `aux->powered_down`: `-EBUSY` at once, no transfer; set by
  `drm_dp_dpcd_set_powered()`.
- Probe: on a local aux `drm_dp_dpcd_read()` reads one byte at
  `DP_TRAINING_PATTERN_SET` before every read, not only the first; a remote
  aux (`is_remote`) is never probed.
- Probe failure: `drm_dp_dpcd_read()` returns that error without the real
  read.
- Probe is on by default; `drm_dp_dpcd_set_probe()` with false turns it off
  for one aux.
- `drm_dp_dpcd_read_data()`: after any negative result it reads again byte by
  byte with `drm_dp_dpcd_readb()` and returns 0 if every byte succeeds.
- `drm_dp_dpcd_write_data()`: no such fallback.

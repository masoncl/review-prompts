- `hid_safe_input_report()`: defined in `drivers/hid/hid-core.c`; arguments
  are `(hid, type, data, bufsize, size, interrupt)`, `bufsize` before `size`.
- `hid_input_report()`: passes `size` as both `bufsize` and `size`.
- `hid_report_raw_event()` tests, in order, each returning `-EINVAL` with
  `hid_warn_ratelimited()`:
  - numbered enum and (`size < 1` or `bufsize < 1`)
  - `bufsize < size`
  - `bufsize` (less the id byte) below the declared length `rsize`
- Short data with enough buffer: `dbg_hid()` only, then the tail is zeroed and
  processing continues.
- `rsize`: from `hid_compute_report_size()`, not `hid_report_len()`; it
  excludes the id byte.
- Data longer than `rsize`: not clamped; hidraw receives the full `size`.
- Short report via `hid_input_report()` with no HID-BPF program attached:
  rejected with `-EINVAL`, never padded, because `bufsize == size`.
- Rejected report: `raw_event` has already run; hiddev, hidraw, parsing and
  `report` do not see it.
- HID-BPF attached (`hdev->bpf.device_data` set):
  `dispatch_hid_bpf_device_event()` replaces `data` with its own buffer and
  `bufsize` with `hdev->bpf.allocated_data`, so short reports are padded
  even when they came through `hid_input_report()`.
- **Unsafe usage**: passing a `bufsize` larger than the writable bytes that
  start at `data`; the `memset()` in `hid_report_raw_event()` writes up to
  `rsize` bytes there.
  - Safe: `data` points past a header and `bufsize` is reduced by the same
    amount, as `i2c_hid_get_input()` does with `sizeof(__le16)`.
  - Safe: `bufsize` is the URB buffer length, as `hid_irq_in()` and
    `hid_ctrl()` pass `urb->transfer_buffer_length` (not `usbhid->bufsize`).
  - Safe: `bufsize` is the fixed array size, as `uhid_dev_input()` passes
    `UHID_DATA_MAX` and clamps `size` to it.

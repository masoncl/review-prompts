- `->request`: of the transports that implement it, only `usbhid_request()`
  is usable in atomic context.
- `amdtp_hid_request()`: sleeps for a GET; `amd_sfh_get_report()` takes a
  mutex and allocates with `GFP_KERNEL`.
- `ishtp_hid_request()`: can sleep; it allocates with `GFP_KERNEL` for a SET.
- i2c-hid input context: `i2c_hid_irq()` is a threaded handler
  (`request_threaded_irq()` with no hard handler), so callbacks run in process
  context there; on usbhid they run from `hid_irq_in()` and `hid_ctrl()`.
- Deferred send from `raw_event`: `dualsense_parse_report()` in
  `drivers/hid/hid-playstation.c` records state under a spinlock and calls
  `dualsense_schedule_work()`; `dualsense_output_worker()` then reaches
  `hid_hw_output_report()` through `dualsense_send_output_report()`.

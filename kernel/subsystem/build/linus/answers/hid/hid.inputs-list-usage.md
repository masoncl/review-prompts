- `hid_hw_start()` with `connect_mask` 0: skips `hid_connect()` entirely and
  succeeds if the transport's `->start()` does, as in
  `drivers/hid/hid-ft260.c`.
- `hid_connect()`: apart from an error of `hid_bpf_connect_device()`, fails
  only when `hdev->claimed` is 0 and the driver has no `raw_event`;
  `HID_CONNECT_DRIVER` alone sets `HID_CLAIMED_DRIVER`.
- `hdev->claimed & HID_CLAIMED_INPUT`: set only when `hidinput_connect()`
  returned 0, which requires a non-empty `hdev->inputs` whose entries are all
  registered.
- `hdev->inputs`: the core initialises it only at the top of
  `hidinput_connect()`; `hid_allocate_device()` leaves it zeroed.
- **Potentially unsafe usage**: `list_empty(&hdev->inputs)` as the only test
  before taking the first entry.
  - Unsafe: when `hidinput_connect()` never ran on this device (mask 0 or no
    `HID_CONNECT_HIDINPUT`); the zeroed head is not "empty" and the entry is
    computed from a NULL pointer.
  - Safe: when the driver itself passed `HID_CONNECT_HIDINPUT` to
    `hid_hw_start()`, as `lg_probe()` does before `lgff_init()`.
  - Safe: testing `HID_CLAIMED_INPUT` first, as `elo_raw_event()` does.
  - Safe: initialising the list before `hid_hw_start()`, as
    `sensor_hub_probe()` does.
- `field->hidinput`: `hidinput_configure_usage()` sets it before any mapping
  decision, for every field of input and output reports, mapped or not.
- `field->hidinput` is NULL: for feature-report fields, for output fields
  under `HID_QUIRK_SKIP_OUTPUT_REPORTS`, when `hidinput_connect()` returned
  before its report loop, and after `hidinput_cleanup_hidinput()` dropped
  that input.
- `hidinput_connect()` failure after `input_configured` ran: an
  `input_configured` error or an `input_register_device()` error goes to
  `hidinput_disconnect()`, which frees every `struct hid_input` on the list,
  including ones the driver already saved.
- Input with no capability: `hidinput_cleanup_hidinput()` frees it right
  after its `input_configured` call, also when the connect then succeeds; if
  no input is left the connect fails.
- **Potentially unsafe usage**: dereferencing `field->hidinput` or a
  `struct hid_input` saved in `input_configured` after `hid_hw_start()`
  succeeded.
  - Unsafe: when `HID_CLAIMED_INPUT` is not set; the pointer can be non-NULL
    and freed, because hidraw or `raw_event` let `hid_connect()` succeed.
  - Safe: `field->hidinput` after testing `hdev->claimed & HID_CLAIMED_INPUT`
    and the pointer for NULL, as `gyration_event()` does;
    `hidinput_cleanup_hidinput()` sets it to NULL for an input it frees.
  - Safe: a saved input after testing `hdev->claimed & HID_CLAIMED_INPUT`,
    when it is the device's only input or `input_configured` gave it a
    capability, as `asus_probe()` does before it uses `drvdata->input`.

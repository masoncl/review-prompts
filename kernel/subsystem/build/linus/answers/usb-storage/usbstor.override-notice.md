- Entries checked: any id with a nonzero `idVendor` or `idProduct`; only the
  generic `USUAL_DEV()` ids are exempt.
- Run-time ids: checked too. `for_dynamic_ids` carries explicit SCSI and
  Bulk-only codes, so a device that reports 06/50 logs "unneeded SubClass
  and Protocol entries".
- Sub-driver entries: checked too, since every sub-driver probe calls
  `usb_stor_probe1()`; the text names `unusual_devs.h` whichever header holds
  the entry.
- Level and text: `dev_notice()`; the three variants are in `msgs[]` in
  `get_device_info()`, and the message asks for a copy to be sent to
  linux-usb@vger.kernel.org and usb-storage@lists.one-eyed-alien.net.
- Suppression: `US_FL_NEED_OVERRIDE` in `us->fflags`; nothing else.
- `US_FL_IGNORE_DEVICE`: `get_device_info()` returns `-ENODEV` before the
  check, so such an entry never logs the notice.
- Each override is tested alone: one field that equals the descriptor logs
  the notice even when the other override is needed.
- Entry for a device with one wrong field: overrides that field only, as in
  `USB_SC_DEVICE, USB_PR_BULK`.

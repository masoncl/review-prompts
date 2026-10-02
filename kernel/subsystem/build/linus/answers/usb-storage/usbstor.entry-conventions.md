- Sort order asked by both headers: VendorID, then ProductID; neither
  mentions `bcdDevice`.
- Above the entry, both headers: the submitter's email address, plus maybe a
  brief explanation of the reason; neither asks for a name or a copyright.
- With an `unusual_devs.h` patch: a copy of `/sys/kernel/debug/usb/devices`,
  taken with the device plugged in and the patch running.
- With an `unusual_uas.h` patch: lsusb -v output for the device.
- Recipient, `unusual_devs.h`: linux-usb@vger.kernel.org only; the submission
  note names no person and not the usb-storage list.
- Recipient, `unusual_uas.h`: Hans de Goede <hdegoede@redhat.com>, with CC to
  linux-usb@vger.kernel.org.
- `COMPLIANT_DEV()`: for an entry added only to set `US_FL_CAPACITY_OK`; the
  header says such a device works correctly.
- Mode switching: the header calls in-kernel mode switching deprecated,
  forbids new entries added only for it, and points to the usb_modeswitch
  database.
- `unusual_uas.h` and the sub-driver headers: may use only `UNUSUAL_DEV()`.
  `drivers/usb/storage/uas.c` and the ignore table in
  `drivers/usb/storage/usual-tables.c` define no `COMPLIANT_DEV()` or
  `USUAL_DEV()`.

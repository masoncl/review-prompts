- Allocation on `&hdev->dev` made while no driver is bound: `really_probe()`
  in `drivers/base/dd.c` finds the devres list not empty and fails the next
  bind with `-EBUSY`.
- The rest is as models expect; see `__hid_device_probe()` and
  `hid_device_remove()` in `drivers/hid/hid-core.c`.

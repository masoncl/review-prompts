# Headers

Changes should not add new includes for the header <linux/mod_devicetable.h>.
The subsystem headers generally provide the needed `*_device_id` structs, so
for example `#include <linux/i2c.h>` already gives a definition of `struct
of_device_id` and `struct i2c_device_id`. Including the full
`<linux/mod_devicetable.h>` results in many unneeded build dependencies.

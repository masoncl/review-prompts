- `drivers/hwmon/lm90.c`: has no mutex of its own; `struct lm90_data` holds
  none. Comments there that name an update_lock in the client mean the core
  lock.
- A driver registered with info may still keep its own mutex, taken inside
  the callbacks (core lock outer, driver mutex inner). For example
  `drivers/hwmon/adt7470.c` shares `data->lock` between
  `adt7470_temp_write()`, `adt7470_update_thread()`, its extra attributes and
  `adt7470_pwm_write_waveform()`; removing it there is not a cleanup.

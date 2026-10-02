- `input_device_tune_vals()` at registration: only grows `dev->vals`, when
  `hint_events_per_packet + 2` exceeds `max_vals`.
- `input_allocate_device()`: does not set `dev->dev.groups`; the attribute
  groups come from `input_dev_type` in `drivers/input/input.c`.
- `input_cleanse_bitmasks()`: zeroes each whole per-type bitmap whose `EV_`
  bit is clear in `evbit`; it does not touch `propbit`.
- Softrepeat: `input_register_device()` calls
  `input_enable_softrepeat(dev, 250, 33)` whenever `rep[REP_DELAY]` and
  `rep[REP_PERIOD]` are both 0; it does not test `EV_REP` and does not set
  it.
- Driver-handled autorepeat: set either `rep[]` value non-zero before
  registering, otherwise `input_repeat_key()` is installed in `dev->timer`.
- `input_register_device()` also fills in `getkeycode` and `setkeycode`
  defaults and, when `dev->poller` is set, calls
  `input_dev_poller_finalize()`.
- `input_setup_polling()`, `input_mt_init_slots()` and `input_ff_create()`
  belong before registration: poller sysfs visibility, `dev->vals` sizing and
  `EV_FF` are evaluated there.
- The only precondition `input_register_device()` checks is `EV_ABS` with
  `dev->absinfo` NULL; a missing `name`, `id` or parent is accepted.

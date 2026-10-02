# What the input measurement found

Three models were asked the 74 questions in `input-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Readers A and C said they assumed
kernels 6.12 to 6.18 and know the input core well in outline; reader C needed
the fewest corrections. Reader B said 6.10 to 6.12 but answered from something
older: it still has the separate polled-device file, a function to free a
sparse keymap and a kernel thread for serio. The hand-written guide was never
checked against current sources, so differences between it and the built guide
are expected and are noted near the end.

The input core is small and old, and the two current readers describe most of
it correctly: allocation and registration, the two devres entries of a managed
device, the event path, the keymap callbacks, handler connect and disconnect.
What all three got wrong is what changed in the last few releases, and nearly
all of it is about when the core calls into the driver.

## What all three readers got wrong

- **The `ready` flag.** None knew `struct input_dev` has `bool ready`. Readers
  A and C said in so many words that no readiness field exists and that
  `event()` can run as soon as a handler connects; reader B said the gate is
  the user count. `input_event_dispose()` and `input_dev_toggle()` call
  `dev->event()` only while `dev->ready` is set. `input_start_device()` and
  `input_uninhibit_device()` set it after `open()` succeeds and replay LED,
  sound and repeat state; `input_close_device()` and `input_inhibit_device()`
  turn LEDs and sounds off and clear it before `close()`. The mistake leaked
  into each reader's answers on visibility at registration, on callbacks after
  unregistration, on events sent to the device and on core suspend. It changes
  a verdict: a driver's `event()` cannot run before its `open()` or after its
  `close()`.
- **The force-feedback hook at unregistration.** All three said
  `input_unregister_device()` calls no force-feedback hook, or that it calls
  `destroy()`. `__input_unregister_device()` calls `dev->ff->stop()` after the
  handlers are disconnected and before `device_del()`. The memoryless helper
  sets it to `ml_ff_stop()`, which does `timer_shutdown_sync()`; `destroy()`
  runs only when the last reference goes. Readers A and C therefore said the
  memoryless timer can fire until release, and reader B thought it was an
  hrtimer.
- **The handler `start()` callback.** All three said it runs at the end of
  `input_register_handle()` or right after `connect()`. It runs from
  `input_open_device()` when the handle's open count becomes one, from
  `__input_release_device()` on every open handle after a grab ends, and from
  `input_uninhibit_device()`, each time under `dev->mutex`.
- **Where `struct input_device_id` is.** Two readers put it and the
  `INPUT_DEVICE_ID_` maxima in `include/linux/mod_devicetable.h`, one in the
  user-space header. They are in `include/linux/device-id/input.h`, which the
  other two include. The `#error` checks that keep the maxima in step are in
  `include/linux/input.h`.
- **`input_default_setkeycode()`.** Readers A and C said both default keymap
  functions are static and drivers cannot call them; reader B said both can be
  called. Only the set function is exported; it asserts that `event_lock` is
  held, and `cros_ec_keyb.c` calls it from its own callback.
- **Polling.** Reader B named `input-polldev.c` and a configuration symbol for
  it; neither exists, and the poller is `drivers/input/input-poller.c` inside
  the core module. Readers A and C knew `input_setup_polling()` but had the
  order wrong: the poller starts after `open()` succeeds and is stopped before
  `close()`, inhibit stops it and suspend does not (the workqueue is
  freezable), the 500 ms interval is only a default for a driver that set
  none, and the sysfs `poll` attribute is bounded by the declared minimum and
  maximum.
- **Handlers outside `drivers/input/`.** Every list was short, and every
  reader named `evbug.c`, which this tree does not have. The callers of
  `input_register_handler()` outside the directory are the VT keyboard, sysrq,
  kgdboc, rfkill, the input-events LED trigger, `mac_hid.c`,
  `hid-appletb-kbd.c` and `sound/usb/mixer_quirks.c`.
- **What is always in the core module.** All left out `touch-overlay.c`;
  reader B also left out the poller, `input-compat.c` and `ff-core.c`.
- **Helpers that need `dev.parent`.** Each reader got a different one wrong.
  `matrix_keypad_build_keymap()` warns and returns `-EINVAL` without a parent;
  `touchscreen_parse_properties()` passes the NULL parent to the property
  calls and dereferences it.
- **`include/linux/uinput.h`.** All three named it. It no longer exists; the
  state enum and the structures are in `drivers/input/misc/uinput.c`.

## What only some readers got wrong

- **Inhibit on a device that is going away** (readers A and C). Both said
  there is no check. `input_inhibit_device()` and `input_uninhibit_device()`
  return `-ENODEV` once `going_away` is set. Reader B had this right.
- **The lowest valid effect type** (readers A and B) is `FF_HAPTIC`, not
  `FF_RUMBLE`.
- **Releasing contacts** (readers A and B). Both said the core lifts active
  contacts on suspend, reset or frame sync. Only `input_inhibit_device()`
  calls `input_mt_release_slots()`, which is private to the core. The other
  paths release keys only.
- **The lock order** (readers A and B). Both nested the force-feedback mutex
  inside the device mutex through upload and erase. Those take `ff->mutex`
  and then `event_lock` only; the device mutex comes first on the flush path.
  A handler's mutex (`evdev->mutex`) is taken outside the device mutex, not
  inside `event_lock`.
- **Serio** (readers A and B). Reader A said `reconnect()` runs on a rescan
  and that `interrupt()` is always in hard interrupt context; reader B said
  unregistering a port is asynchronous and that a thread does the work. Both
  called unregistering the input device before `serio_close()` unsafe, which
  is what `atkbd_disconnect()` does, safely, after disabling reporting under a
  receive pause.
- **Reader A alone.** A new tracking id on a change of tool type, taken from
  the comment above `input_mt_report_slot_state()`; the body assigns a new id
  only when the stored one is negative. Events reported before registration
  are not dropped for want of a value queue (allocation already creates one
  with ten entries); they are queued and flushed to an empty handle list. A
  managed interrupt requested after registration is fine only if `close()`
  never touches it.
- **Reader B alone**, and at length. A frame holding only a sync is dropped,
  not passed; a synthetic sync carries value one; `input_report_key()` turns a
  value of two into one, so hardware autorepeat needs `input_event()`; an
  out-of-range slot number leaves the previous slot selected, so the values
  that follow corrupt it; the sparse keymap copy is devres on the input device
  itself and there is no function to free it; `matrix_keypad_build_keymap()`
  fills in the keycode fields itself with two-byte entries; slot counts above
  1024 are refused; `erase()` is optional; PS/2 drivers install
  `ps2_interrupt()` and do not write their own handler; the core uses lock
  guards and scope-based cleanup throughout.
- **Reader C alone.** That the devres release entry drops "the last
  reference" (handlers hold their own), and that `event_lock` protects the
  grab pointer (the mutex does, and readers use RCU).

## What the readers already knew

Readers A and C: allocation and registration, that the core requires none of
the identity fields, freeing versus unregistering including the shared error
path that clears the pointer, the two devres entries and where each fires, that
manual calls on a managed device are safe, the event path and the filtering
rules per type, frames and the synthetic sync, the lock `input_event()` takes,
the keymap callback context, the force-feedback callback contexts apart from
`stop`, ownership of the memoryless data pointer, handler methods, connect and
disconnect, grab, `input_device_enabled()` and its lock, slot initialisation
and the out-of-range slot.

## Where the hand-written guide is stale

`input.md` is mostly right about the core, because it is recent: it knows
`ff->stop`, the two devres steps and that manual calls on managed devices are
safe. What it gets wrong or leaves out:

- It says `input_ff_create_memless()` takes ownership of the data pointer and
  that a driver freeing it is a bug. Ownership passes on success only; on
  failure the caller must free it, as `gamecon.c` does.
- It says an event before registration updates `keybit`. That is the
  capability bitmap; the state is `key`.
- It says `open()` may run before registration returns "if a userspace handler
  is already waiting". It is in-kernel handlers such as the VT keyboard and
  `input-leds` that open from `connect()`.
- It says the core filters redundant events. That is true of keys, switches,
  LEDs and ordinary or slotted absolute axes, and not of relative, misc or
  sound events or of multitouch axes without slots.
- It says `input_unregister_device()` calls `close()`. The handlers do, from
  their `disconnect()`, and not while the device is inhibited.
- Its quick checks ask for `name` and `dev.parent` to be set. The core needs
  neither; three helper libraries need the parent.
- It says nothing of `dev->ready`, of inhibit calling `close()` and `open()`
  with no handler involved, of polling, of multitouch, or of serio, all of
  which load under the same trigger.
- Its "analysis protocol" and `REPORT as bugs` lines tell a reviewer what to
  report. The build set asks for the unsafe usage and the correct usage that
  looks like it.
- The maintainer's style is written down nowhere in the tree. What the tree
  shows is kept as one question.

## What was left out of the build set and why

The build set has 30 of the 74 questions, sized to the 1,685 words of the
hand-written guide. Left out:

- What readers A and C answer and only the oldest reader does not: the
  structures, declaring capabilities, absolute axis storage, the identity
  fields, the library configuration symbols, allocation, registration failure,
  reference counting, managed allocation, open and close counting, the path of
  an event, report helpers, timestamps, packet size, autorepeat, injection,
  the keymap callback context and the two keymap libraries, creating a
  force-feedback device, handler methods, connect, match and grab, the event
  device client and its state after disconnect.
- What all got partly wrong but few patches touch: core suspend and resume,
  the keymap default, in-kernel tracking, the touchscreen property helper,
  passive observers, the effect type range, the user-space device, serio port
  lifetime, serio driver callbacks, the PS/2 library, event codes and device
  ids, the documentation and the tests. They stay in the measurement set.
- Folded into a kept question: the device mutex (into inhibit and the enabled
  check), events sent to the device (into the ready state and the reporting
  context), the force-feedback callback table (into the two memoryless
  questions and the unregistration steps), reporting a frame of contacts (into
  slot initialisation).

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          142        29%     16     20   6.12 to 6.16
reader B          194        76%      0     71   6.10 to 6.12
reader C          109        23%     29     16   6.12 to 6.18

question                           reader A      reader B      reader C   verdict
input.core-files                    2% ( 2)      21% ( 7)       3% ( 2)   middling
input.docs                         21% ( 1)      71% ( 1)      17% ( 1)   weak: reader B
input.tests                        10% ( 1)      98% ( 1)       0% ( 0)   weak: reader B
input.kconfig-libraries            27% ( 1)      83% ( 1)      24% ( 2)   weak: reader B
input.dev-struct                   20% ( 7)      52% ( 1)      60% ( 5)   weak: reader B, reader C
input.handler-handle               19% ( 1)      77% ( 2)      28% ( 3)   weak: reader B
input.registration-bitmaps         31% ( 1)      81% ( 1)       6% ( 1)   weak: reader B
input.set-capability               55% ( 1)      72% ( 1)       4% ( 1)   weak: reader A, reader B
input.absinfo                       9% ( 1)      70% ( 1)       3% ( 1)   weak: reader B
input.identity-fields              26% ( 2)      81% ( 2)      31% ( 1)   weak: reader B
input.alloc-register               30% ( 3)      77% ( 5)       7% ( 1)   weak: reader B
input.register-visible             52% ( 4)      81% ( 1)      30% ( 4)   weak: reader A, reader B
input.register-failure             36% ( 1)      90% ( 2)       0% ( 0)   weak: reader B
input.free-unregister-usage        20% ( 2)      63% ( 1)      29% ( 1)   weak: reader B
input.refcount-lifetime            39% ( 1)      81% ( 5)      26% ( 2)   weak: reader B
input.unregister-sequence          42% ( 3)      87% ( 4)      37% ( 3)   weak: reader A, reader B
input.after-unregister-calls       55% ( 4)      82% ( 2)       8% ( 2)   weak: reader A, reader B
input.async-teardown-usage         55% ( 1)      66% ( 1)      18% ( 1)   weak: reader A, reader B
input.devm-alloc                    2% ( 3)      65% ( 4)       0% ( 0)   weak: reader B
input.devm-two-step                25% ( 1)      78% ( 1)       2% ( 1)   weak: reader B
input.devm-manual-calls             0% ( 0)      87% ( 1)      52% ( 1)   weak: reader B, reader C
input.devm-ordering-usage          19% ( 1)      82% ( 1)      15% ( 1)   weak: reader B
input.devm-parent                  33% ( 1)      88% ( 1)      36% ( 1)   weak: reader B
input.open-close                   28% ( 5)      72% ( 2)      14% ( 4)   weak: reader B
input.ready-state                  56% ( 1)      89% ( 2)      54% ( 1)   all weak
input.inhibit                      46% ( 1)      84% ( 2)      48% ( 3)   all weak
input.device-enabled-usage         16% ( 1)      73% ( 1)       0% ( 0)   weak: reader B
input.mutex-scope                  28% ( 1)      77% ( 1)      23% ( 1)   weak: reader B
input.pm-core                      56% ( 1)      92% ( 2)      19% ( 1)   weak: reader A, reader B
input.event-path                   13% ( 4)      88% ( 5)      42% ( 3)   weak: reader B, reader C
input.event-filtering              31% ( 3)      70% ( 3)      36% ( 1)   weak: reader B
input.sync-frames                   0% ( 0)      77% ( 3)      21% ( 1)   weak: reader B
input.event-context                19% ( 1)      76% ( 1)      42% ( 1)   weak: reader B, reader C
input.pre-register-events          27% ( 1)      87% ( 1)      43% ( 1)   weak: reader B, reader C
input.report-helpers               10% ( 1)      82% ( 2)      62% ( 1)   weak: reader B, reader C
input.timestamps                   30% ( 5)      85% ( 7)       0% ( 2)   weak: reader B
input.events-per-packet            55% ( 3)      80% ( 2)      14% ( 1)   weak: reader A, reader B
input.autorepeat                    8% ( 1)      83% ( 3)      24% ( 1)   weak: reader B
input.output-event-context         56% ( 3)      79% ( 1)      45% ( 4)   all weak
input.inject                       36% ( 2)      93% ( 2)      24% ( 1)   weak: reader B
input.keymap-default               35% ( 2)      91% ( 4)      32% ( 1)   weak: reader B
input.keymap-callback-context       0% ( 0)      83% ( 1)       0% ( 0)   weak: reader B
input.sparse-keymap                41% ( 2)      79% ( 2)       8% ( 1)   weak: reader A, reader B
input.matrix-keymap                26% ( 1)      77% ( 2)      11% ( 1)   weak: reader B
input.mt-init                      33% ( 3)      62% ( 4)      29% ( 3)   weak: reader B
input.mt-frame                     21% ( 2)      79% ( 5)      22% ( 2)   weak: reader B
input.mt-slot-index-usage           0% ( 0)      78% ( 2)      18% ( 1)   weak: reader B
input.mt-tracking                  37% ( 1)      85% ( 2)      32% ( 1)   weak: reader B
input.mt-release                   37% ( 1)      88% ( 4)      38% ( 2)   weak: reader B
input.touchscreen-props            48% ( 1)      79% ( 4)      47% ( 3)   all weak
input.polling                      40% ( 6)      81% ( 7)      41% ( 3)   all weak
input.ff-create                    18% ( 1)      75% ( 6)      12% ( 4)   weak: reader B
input.ff-callback-context           7% ( 2)      42% ( 1)      11% ( 1)   weak: reader B
input.ff-memless-ownership         13% ( 1)      78% ( 1)       1% ( 1)   weak: reader B
input.ff-memless-timer             29% ( 1)      81% ( 2)      41% ( 1)   weak: reader B, reader C
input.ff-play-effect-usage         40% ( 1)      34% ( 1)       3% ( 1)   weak: reader A
input.ff-effect-range              18% ( 1)      35% ( 1)      24% ( 1)   middling
input.handler-methods              13% ( 2)      81% ( 6)       0% ( 0)   weak: reader B
input.handler-connect               9% ( 0)      77% ( 2)       1% ( 1)   weak: reader B
input.handler-match                14% ( 1)      66% ( 2)      48% ( 1)   weak: reader B, reader C
input.handler-start                56% ( 1)      82% ( 2)      58% ( 1)   all weak
input.grab                         23% ( 1)      80% ( 3)       0% ( 0)   weak: reader B
input.passive-observer             21% ( 1)      84% ( 1)      33% ( 1)   weak: reader B
input.evdev-client                 31% ( 1)      72% ( 4)      39% ( 1)   weak: reader B
input.evdev-dead                   41% ( 2)      80% ( 2)      10% ( 0)   weak: reader A, reader B
input.uinput-lifecycle             38% ( 4)      88% ( 6)      44% ( 4)   weak: reader B, reader C
input.serio-ports                  22% ( 1)      89% ( 4)      34% ( 1)   weak: reader B
input.serio-driver                 38% ( 5)      73% ( 4)      13% ( 1)   weak: reader B
input.serio-teardown-usage         68% ( 3)      74% ( 1)      18% ( 1)   weak: reader A, reader B
input.libps2                       35% ( 4)      80% ( 4)      23% ( 1)   weak: reader B
input.lock-order                   59% ( 2)      72% ( 5)       0% ( 0)   weak: reader A, reader B
input.core-change-checklist        42% ( 4)      81% ( 5)      21% ( 4)   weak: reader A, reader B
input.uapi-codes                   38% ( 2)      80% ( 2)      49% ( 2)   weak: reader B, reader C
input.style                        49% ( 5)      60% ( 5)      12% ( 1)   weak: reader A, reader B
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `input.dev-struct`, `input.output-event-context`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `input.handler-handle`, `input.absinfo`, `input.alloc-register`, `input.register-failure`, `input.refcount-lifetime`, `input.devm-alloc`, `input.open-close`, `input.mutex-scope`, `input.event-path`, `input.mt-frame`, `input.ff-create`, `input.handler-methods`, `input.handler-connect`, `input.evdev-dead`.

## Questions reorganised

- Subjects now: open, close, inhibit and readiness; registering and unregistering; managed devices;
  reporting events; multitouch; force feedback; handlers; core locking and other users; maintainer
  conventions. 48 questions became 43.
- Merged: `input.alloc-register` + `input.registration-bitmaps` to `input.register-setup`;
  `input.after-unregister-calls` + `input.evdev-dead` to `input.unregister-callbacks`;
  `input.devm-alloc` + `input.devm-two-step` to `input.devm-lifecycle`.
- Dropped: `input.dev-struct` (field groups; its one surprise, the ready flag, is `input.ready-state`)
  and `input.handler-handle` (the overview again; the outside handlers go to the core checklist).

# What the leds measurement found

Three models were asked the 88 questions in `leds-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc5). The readers are labelled A, B and C; which
models they were does not matter here. Reader A needed the least rewriting and
reader C the most. In 58 of reader C's 88 answers, the checker rewrote 40% or
more of the answer. All three assumed a kernel near 6.12, and reader A
sometimes assumed one as late as 6.17. The hand-written guide was never checked
against current sources, so differences between it and the built guide are
expected. The differences are noted below.

## What all three readers got wrong

Names and layouts that changed:

- **Getting an LED from firmware.** All three named of_led_get(), with
  `of_parse_phandle()` and `class_find_device_by_of_node()`. The tree has no
  of_led_get(). The static `fwnode_led_get()` in `drivers/leds/led-class.c`
  uses `fwnode_find_reference()` and `class_find_device_by_fwnode()`.
  `led_get()` calls `fwnode_led_get()` first, and searches `leds_lookup_list`
  only when that call returns `-ENOENT`.
- **Driver directories.** All three listed drivers/leds/simple/. The directory
  is `drivers/leds/simatic/`.
- **Allocation.** All three wrote `kzalloc()` for the trigger and for the data
  of a trigger. `led_trigger_register_simple()` and the triggers under
  `drivers/leds/trigger/` use `kzalloc_obj()`.
- **Multicolor limits.** None listed the `multi_max_intensity` attribute.
  Readers A and B said that `struct mc_subled` has no `max_intensity` member.
  They also said that a written intensity is not limited.
  `multi_intensity_store()` limits each value to what
  `led_mc_get_max_intensity()` returns, and calls `led_set_brightness()` only
  while `LED_BLINK_SW` is clear.
- **Flash duration.** None knew the `duration` setting of
  `struct led_classdev_flash`, the `duration_set` operation or
  `led_set_flash_duration()`.
- **Name composition.** None knew the fifth source of a name in
  `led_compose_name()`, the name of a software node.
- **Multicolor node name.** All three gave the pattern without the form that
  ends in a number. `leds-class-multicolor.yaml` has
  `^multi-led(@[0-9a-f]|-[0-9]+)?$`. That file accepts two `color` values and
  describes no sub-LED nodes.
- **Common properties.** All three listed `retain-state-suspended` among the
  properties of `Documentation/devicetree/bindings/leds/common.yaml`. That
  file does not define it. The bindings of single controllers do.

Facts that would change what a review concludes:

- **Building without the class.** Each reader described stubs that
  `include/linux/leds.h` does not have. The header has no test of
  `CONFIG_LEDS_CLASS`, so the class functions have no stub. With
  `CONFIG_LEDS_TRIGGERS` off, `led_trigger_register()` and
  `led_trigger_unregister()` have no stub, and `led_trigger_set()`,
  `led_trigger_event()` and `led_trigger_register_simple()` have one. Readers B
  and C gave a Kconfig line that no Kconfig file in the tree has. In-tree
  callers use `IS_REACHABLE(CONFIG_LEDS_CLASS)`, or a dependency of the form
  that `PHYLIB_LEDS` has.
- **Blinking from a hard interrupt.** All three said that
  `led_trigger_event()`, `led_trigger_blink()` and
  `led_trigger_blink_oneshot()` may all be called from any context.
  `led_trigger_blink()` reaches `led_blink_set_nosleep()`, which calls
  `led_blink_set()` directly unless the driver has both `blink_set` and
  `brightness_set_blocking`. `led_blink_set()` calls `timer_delete_sync()`,
  which warns in a hard interrupt.
- **Reading brightness under a private trigger.** All three said that
  `brightness_show()` has no special case. It returns `-ENODATA` when
  `led_trigger_is_hw_controlled()` is true, before it calls
  `led_update_brightness()`.
- **A driver with no brightness callback.** Readers A and B said that the work
  logs an error, and reader C said that the sysfs write fails.
  `set_brightness_delayed_set_brightness()` returns with no message when both
  helpers return `-ENOTSUPP`, and `brightness_store()` returns the size.
- **`led_set_brightness_sync()` and blinking.** Readers B and C said that it
  tests `LED_BLINK_SW`, and reader A said so in one answer of two. It tests
  `blink_delay_on` and `blink_delay_off`.
- **`led_set_brightness()` during a software blink.** None gave all three
  branches. A non-zero value with `LED_SET_BRIGHTNESS` or `LED_BLINK_DISABLE`
  pending goes to `delayed_set_value` and the work. Otherwise a non-zero value
  goes to `new_blink_brightness`. A zero value sets `LED_BLINK_DISABLE` and
  queues the work. The function never calls `led_stop_software_blink()`.
- **Order of registration.** All three had the order of
  `led_classdev_register_ext()` wrong. The function does these steps in this
  order:
  1. defaults `max_brightness`
  2. calls `led_update_brightness()` and `led_init_core()`
  3. adds the LED to `leds_list`
  4. calls `led_trigger_set_default()`

  The function holds `led_access` from before the device is created until
  after the default trigger is set.
- **Order of detaching a trigger.** All three put `deactivate` before the
  removal of the sysfs groups of the trigger. `led_trigger_set()` calls
  `device_remove_groups()` first. On attach it calls `activate` and then
  `device_add_groups()`.
- **Sysfs attributes of a driver.** All three wrote a rule against adding
  files to the class device after registration. The multicolor and flash
  registration functions overwrite `groups`, so the drivers of such LEDs add
  their group after registration, as `drivers/hid/hid-oxp.c` does.
- **Hardware control.** All three said that a driver must set the field and
  every callback together. `supports_hw_control()` returns false when one of
  three callbacks is NULL, so a partial setting without them is harmless. The
  code has no NULL test for `hw_control_trigger` or for
  `hw_control_get_device` once the three are set. Readers B and C also missed
  that `netdev_trig_activate()` sets `hw_control` without calling
  `can_hw_control()`.
- **Netdev trigger locks.** None listed the lock that `netdev_lock_ops()`
  takes. `set_device_name()` takes it between the RTNL lock and the lock of
  the trigger data. Readers A and B named `__ethtool_get_link_ksettings()`.
  The trigger calls `netif_get_link_ksettings()`.
- **Multicolor component calculation.** All three said that a multicolor
  driver has to call `led_mc_calc_color_components()`. Drivers whose hardware
  scales the colors, such as `drivers/leds/leds-lp50xx.c`, never call it. The
  function rounds with `DIV_ROUND_CLOSEST()`.
- **Flash strobe helpers.** All three said that a caller must hold
  `led_access`. Neither `led_set_flash_strobe()` nor `led_get_flash_strobe()`
  takes or asserts a lock. The registration function checks `strobe_set` and
  `brightness_set_blocking` only when `LED_DEV_CAP_FLASH` is set.

Things the readers said they did not recognise or were unsure of:

- A function that `Documentation/leds/leds-class.rst` names and the tree does
  not define (all three). The document names led_brightness_set(). The tree
  has that name only as a member of `struct phy_driver`.
- Whether `uleds_write()` checks that the name ends (readers A and B; reader C
  described a check that the code does not have). It rejects a name with no
  NUL byte. `Documentation/leds/uleds.rst` still describes a read of a single
  byte, and the code copies an `int`.
- An in-tree caller of the camera activity hooks (readers A and B). The tree
  has none.
- Which code reads `trigger-sources` (readers A and B). The code that reads
  it is `gpio_trig_activate()` in `drivers/leds/trigger/ledtrig-gpio.c` and
  `drivers/usb/core/ledtrig-usbport.c`.
- Whether `pattern_set` can get a repeat count of 0 (readers A and C). It gets
  0 until user space writes `repeat`, although a write of 0 to `repeat` fails.

## What only some readers got wrong

Reader C, in addition:

- **Label against color and function.** Reader C said that `color` and
  `function` take precedence and that `label` is the fallback. The code does
  the reverse: `led_parse_fwnode_props()` returns after it reads `label`.
  Reader C also said that the name always starts with the device name. The
  device name is prepended to a name made of color and function only when
  `devname_mandatory` is set.
- **Halves of `flags`.** Reader C had them reversed, and put the blink bits in
  `flags`. `LED_SUSPENDED` is bit 0, and the settings of a driver start at
  bit 16. The blink bits are in `work_flags`.
- **Order of unregistration.** `led_classdev_unregister()` does these steps in
  this order:
  1. detaches the trigger
  2. sets `LED_UNREGISTERING`
  3. stops a software blink
  4. writes off unless `LED_RETAIN_AT_SHUTDOWN` is set
  5. calls `flush_work()`

  Reader C had the trigger last, the blink stop under the flag, and
  `cancel_work_sync()`.
- **Lock order.** Reader C put `trigger_lock` outside `triggers_list_lock`.
  `led_trigger_write()` takes `led_access`, then `triggers_list_lock`, then
  `trigger_lock`.
- **Properties the core reads.** Reader C said that drivers parse
  `max-brightness` and `retain-state-shutdown`. `led_classdev_register_ext()`
  reads both.
- **`led_set_brightness_sync()` while suspended.** It stores the value and
  returns 0, not `-EBUSY`.
- **Names that are defined nowhere in the tree:** gpio_led_register(),
  gpio_led_get_default(), led_trigger_show(), led_trigger_store(),
  led_trigger_panic(), netdev_led_work(), hw_control_start(),
  phy_leds_register(), led_free_default_trigger(), uleds_device_release() and
  devm_fwnode_led_get().
- **uleds.** Reader C said that the driver sets `brightness_set_blocking` and
  `LED_CORE_SUSPENDRESUME` and registers with `led_classdev_register()`. The
  driver sets `brightness_set` and sets no flag. The driver calls
  `devm_led_classdev_register()`.
- **Return types.** `led_trigger_register_simple()`, `led_mc_set_brightness()`
  and `led_mc_trigger_event()` return nothing. Reader C gave each an error
  return.

Reader B, in addition. Each bullet gives what reader B said, then what the
tree has:

- Said that registration points `led_cdev->name` at the final name. Nothing in
  the core writes that member, so only `dev_name()` of the class device gives
  the final name.
- Said that `led_compose_name()` returns the length of the name and cuts a
  long name. It returns 0, and `-E2BIG` for a name that does not fit.
- Said that the worker tries the blocking callback first. The worker calls
  `brightness_set` first.
- Said that `LED_UNREGISTERING` stops new brightness work. The core tests the
  flag only to leave out one error message.
- Said that `triggers_list_lock` nests outside `leds_list_lock`. No code holds
  both.
- Gave a rule to unregister LEDs in the reverse of the order of registration,
  and named a callback .remove_new. The tree has neither.
- Said that `of_phy_led()` uses the managed registration. It calls
  `led_classdev_register_ext()`.

Reader A, in addition, in the same form:

- Said that `brightness_store()` ends with `flush_work()`, so that the
  callback has run when the write returns. The function has no such call.
- Said that the class has a `color` attribute, as reader C did. The class has
  `brightness`, `max_brightness`, `trigger` and, for some LEDs,
  `brightness_hw_changed`.
- Said that `led_blink_set_oneshot()` is documented as a function that may
  sleep. Its kerneldoc says that it does not sleep, and the body agrees.
- Said that no driver under `drivers/leds/` sets `hw_control_trigger`.
  `drivers/leds/leds-cros_ec.c` sets it.

Readers B and C, and not reader A, in the same form:

- Named drivers/leds/trigger/ledtrig-audio.c. That file does not exist, and
  `sound/core/control_led.c` registers the two audio triggers itself.
- Named del_timer_sync(). The tree has `timer_delete_sync()`.
- Said that every trigger symbol is tristate. `LEDS_TRIGGER_DISK`,
  `LEDS_TRIGGER_MTD`, `LEDS_TRIGGER_CPU` and `LEDS_TRIGGER_PANIC` are bool.

Readers A and B, and not reader C, in the same form:

- Said that `led_colors` is declared in `drivers/leds/leds.h`. The array is
  static in `drivers/leds/led-core.c`.
- Said that `panic()` calls the blink function. The calls are in `vpanic()`.

## What the readers already knew

- All three: that one function does every registration, how a name collision
  is handled, how a trigger is registered and attached to the LEDs that
  exist, where the attributes of a trigger appear, that one ordered workqueue
  serves every LED, and which uevent a change of trigger sends.
- Readers A and B: the precedence of `label`, the steps of `led_trigger_set()`
  on attach, the software blink timer and its state, the one-shot blink, the
  flash setting helpers and the checks of flash registration.
- Reader A: the layout of `flags`, the type of the brightness functions, the
  name after registration, and the lock order of the trigger core.

## Where the hand-written guide is stale

Every name in the hand-written guide, `leds.md`, exists in the tree. What is
stale is two rules that lack a condition, and what the guide leaves out.

- **Managed registration.** The guide says that managed registration "handles
  both error paths and driver removal safely". The devres release runs after
  `remove()` returns, and `led_classdev_unregister()` calls the callbacks of
  the driver while it runs. So a `remove()` that destroys what a callback uses
  is unsafe with a managed LED too. `asus_wireless_remove()` shows the safe
  form: it calls `devm_led_classdev_unregister()` before it destroys its
  workqueue.
- **Unmanaged registration.** The guide describes a missing managed call as a
  hazard. Unmanaged registration that is unregistered in the right order is
  correct, and `of_phy_led()` uses it.
- **Trigger teardown.** The guide says to call `led_trigger_unregister()` "on
  exit or probe failure". The function returns early only when the list node
  of the trigger is initialised and empty, as it is after an earlier
  unregistration. For a zeroed trigger that was never registered, or whose
  registration returned `-EEXIST`, it goes on to `list_del_init()`.
- **Label.** The guide says to prefer `color` and `function`. The guide does
  not say what the code does when a node also has `label`:
  `led_parse_fwnode_props()` reads `label` and ignores the other two.
  `common.yaml` marks `label` as deprecated only in the text of its
  description.
- **Conventions.** The commit subject, the names of private data, the three
  preferences and the two rules on logging are what the maintainers ask for.
  No code states them, so no question can supply them. They are kept by hand
  in `kernel/subsystem/verbatim/leds-conventions.md`, and the build inserts
  that file.
- **Instructions to a reviewer.** The "Quick Checks" tell a reviewer what to
  verify. A built guide says how the tree is, so the two checks are kept as
  conventions, without the instruction.
- **What it leaves out.** The guide has no map of the files. It has nothing on
  the context of the brightness and blink callbacks, the deferred work, the
  locks of the trigger core, hardware control, patterns, the multicolor and
  flash classes, consumers of an LED, suspend and shutdown, or building with
  the class configured out.

## What was left out of the build set

Of the 88 questions 78 are kept. With the overview and the question on model
gaps the build set has 80 questions, and one item that inserts the
conventions. Reader C is wrong on most questions, so few could be dropped.
Left out:

- Every reader answered them, and what the check changed would not change a
  review: `leds.register-variants`, `leds.name-collision`,
  `leds.trigger-register`, `leds.trigger-uevent`, `leds.workqueue`.
- They asked what a structure holds, which the overview covers:
  `leds.classdev-struct`, `leds.trigger-struct`. The one mistake in them that
  matters, which fields registration overwrites from firmware, is asked by
  `leds.register-firmware-props` and `leds.max-brightness`.
- Another question, which is kept, asks for the same facts:
  - `leds.software-blink`: `leds.work-flags` asks for the blink bits, and
    `leds.blink-variants` and `leds.blink-set-callback` ask when the core
    blinks in software.
  - `leds.trigger-attributes`: `leds.trigger-set` asks for the order of the
    groups against `activate` and `deactivate`. The readers disagreed with
    themselves on that order: reader C had it right here and wrong in two
    other answers.
  - `leds.sysfs-disable`: the readers knew the lock rule. The handler that
    does not test the flag is in the multicolor class, and `leds.mc-sysfs`
    asks about that handler.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          343        17%     43      6   6.12 to 6.17
reader B          330        24%     25     11   6.12 to 6.12
reader C          386        46%      2     58   6.12 to 6.12

question                          reader A      reader B      reader C   verdict
leds.core-files                   13% ( 6)      13% ( 4)      28% (10)   middling
leds.driver-directories           19% ( 4)      26% ( 4)      43% ( 2)   weak: reader C
leds.outside-code                 15% ( 3)      33% ( 5)      54% ( 4)   weak: reader C
leds.docs                         33% ( 4)      26% ( 2)      53% ( 2)   weak: reader C
leds.tests                         7% ( 4)      31% ( 5)      51% ( 3)   weak: reader C
leds.kconfig                      18% ( 5)      20% ( 3)      37% ( 3)   middling
leds.header-stubs                 42% ( 8)      46% ( 7)      61% ( 4)   all weak
leds.classdev-struct               6% ( 7)      15% ( 6)      23% (13)   middling
leds.classdev-flags                8% ( 5)      32% ( 8)      73% ( 7)   weak: reader C
leds.work-flags                   18% ( 4)      38% ( 3)      49% ( 3)   weak: reader C
leds.name-fields                   0% ( 0)      12% ( 2)      31% ( 1)   middling
leds.brightness-callbacks         22% ( 4)      39% ( 4)      57% ( 4)   weak: reader C
leds.brightness-get                9% ( 3)      27% ( 3)      45% ( 2)   weak: reader C
leds.max-brightness                9% ( 2)      37% ( 2)      47% ( 2)   weak: reader C
leds.brightness-type               0% ( 0)      33% ( 2)      81% ( 1)   weak: reader C
leds.sysfs-attributes             20% ( 5)      16% ( 3)      82% ( 2)   weak: reader C
leds.driver-attributes            30% ( 2)      23% ( 2)      49% ( 2)   weak: reader C
leds.sysfs-disable                10% ( 2)      19% ( 1)      38% ( 1)   middling
leds.hw-changed                   41% ( 4)       8% ( 1)      45% ( 2)   weak: reader A, reader C
leds.register-variants             7% ( 7)      21% ( 5)       2% ( 1)   middling
leds.register-steps               18% ( 3)      29% ( 3)      76% ( 9)   weak: reader C
leds.probe-order                  27% ( 3)      33% ( 3)      37% ( 3)   middling
leds.register-firmware-props       6% ( 1)      13% ( 1)      59% ( 5)   weak: reader C
leds.compose-name                  6% ( 1)      18% ( 1)      78% ( 4)   weak: reader C
leds.name-collision                9% ( 1)       4% ( 1)      24% ( 1)   middling
leds.naming-rules                 29% ( 1)      38% ( 1)      80% ( 3)   weak: reader C
leds.child-node-refs              40% ( 5)      38% ( 2)      33% ( 2)   weak: reader A
leds.driver-shape                  7% ( 1)      26% ( 2)      58% ( 4)   weak: reader C
leds.unregister-steps             14% (11)      10% ( 4)      61% (11)   weak: reader C
leds.remove-ordering              17% ( 2)      26% ( 4)      39% ( 4)   middling
leds.devm-unregister              26% ( 3)       7% ( 2)      25% ( 4)   middling
leds.hot-unplug-errors            12% ( 3)      13% ( 4)      59% ( 5)   weak: reader C
leds.set-brightness-variants      22% ( 7)      10% ( 6)      28% ( 7)   middling
leds.set-brightness-blinking      19% ( 3)      14% ( 2)      57% ( 5)   weak: reader C
leds.brightness-work               4% ( 3)      18% ( 6)      26% ( 5)   middling
leds.workqueue                    22% ( 4)      25% ( 1)      34% ( 2)   middling
leds.set-brightness-sync           5% ( 1)       0% ( 0)      62% ( 4)   weak: reader C
leds.brightness-field             22% ( 9)      30% ( 5)      43% ( 5)   weak: reader C
leds.blink-variants                5% ( 3)      12% ( 7)      76% ( 6)   weak: reader C
leds.blink-set-callback           11% ( 3)      22% ( 3)      38% ( 4)   middling
leds.software-blink                2% ( 2)       7% ( 1)      37% ( 3)   middling
leds.blink-stop                   17% ( 5)      28% ( 4)      64% ( 7)   weak: reader C
leds.oneshot-blink                 4% ( 1)       2% ( 1)      46% ( 2)   weak: reader C
leds.own-timer-triggers           14% ( 5)      60% ( 6)      52% ( 3)   weak: reader B, reader C
leds.trigger-struct                8% ( 4)      13% ( 3)      32% ( 4)   middling
leds.trigger-register              1% ( 1)      21% ( 3)      18% ( 2)   middling
leds.trigger-unregister           28% ( 3)      41% ( 4)      45% ( 4)   weak: reader B, reader C
leds.simple-trigger                7% ( 2)      16% ( 2)      43% ( 4)   weak: reader C
leds.trigger-event-context        41% ( 4)      43% ( 3)      36% ( 3)   weak: reader A, reader B
leds.trigger-set                   0% ( 0)       7% ( 2)      46% ( 6)   weak: reader C
leds.trigger-file                  7% ( 2)      11% ( 2)      51% ( 5)   weak: reader C
leds.default-trigger               8% ( 1)      15% ( 2)      40% ( 2)   weak: reader C
leds.trigger-locks                 5% ( 1)      15% ( 3)      42% ( 4)   weak: reader C
leds.trigger-uevent               10% ( 1)      20% ( 2)      16% ( 1)   middling
leds.trigger-callbacks            21% ( 6)      21% ( 6)      54% ( 6)   weak: reader C
leds.trigger-data                 15% ( 3)       2% ( 1)      28% ( 2)   middling
leds.trigger-attributes            9% ( 1)      20% ( 1)       3% ( 2)   middling
leds.default-pattern-init         16% ( 4)      26% ( 4)      51% ( 4)   weak: reader C
leds.private-trigger              12% ( 3)      20% ( 2)      30% ( 2)   middling
leds.panic-trigger                13% ( 4)      24% ( 3)      50% ( 4)   weak: reader C
leds.activity-hooks               19% ( 6)      17% ( 4)      51% ( 2)   weak: reader C
leds.hw-control-callbacks         27% ( 5)      50% (10)      70% ( 9)   weak: reader B, reader C
leds.hw-control-netdev            11% ( 7)      37% ( 7)      60% ( 5)   weak: reader C
leds.netdev-locking               26% ( 6)      39% ( 8)      50% ( 4)   weak: reader C
leds.hw-control-providers         28% ( 7)      43% ( 7)      56% ( 6)   weak: reader B, reader C
leds.pattern-callbacks            14% ( 6)      26% ( 6)      58% ( 9)   weak: reader C
leds.pattern-trigger               9% ( 4)      20% ( 7)      73% ( 6)   weak: reader C
leds.mc-struct                    36% ( 2)      40% ( 4)      21% ( 8)   weak: reader B
leds.mc-register                  29% ( 6)      30% ( 4)      60% ( 5)   weak: reader C
leds.mc-calc                      19% ( 3)      33% ( 3)      41% ( 2)   weak: reader C
leds.mc-sysfs                     31% ( 5)      28% ( 6)      31% ( 4)   middling
leds.mc-kernel-set                20% ( 2)       8% ( 1)      45% ( 4)   weak: reader C
leds.color-ids                    27% ( 6)      48% ( 4)      20% ( 3)   weak: reader B
leds.flash-struct                 17% ( 4)      19% ( 7)      55% ( 4)   weak: reader C
leds.flash-register                6% ( 2)       6% ( 1)      70% ( 4)   weak: reader C
leds.flash-settings                5% ( 2)       0% ( 0)      56% ( 4)   weak: reader C
leds.flash-strobe                 45% ( 4)      40% ( 4)      84% ( 4)   all weak
leds.flash-v4l2                    7% ( 3)      17% ( 4)      42% ( 4)   weak: reader C
leds.consumer-get                 17% ( 6)      14% ( 5)      46% ( 7)   weak: reader C
leds.consumer-refs                22% ( 4)      20% ( 5)      19% ( 4)   middling
leds.consumer-lookup              21% ( 3)      27% ( 3)      23% ( 4)   middling
leds.suspend-resume               22% ( 9)      34% (10)      46% (13)   weak: reader C
leds.shutdown-state               36% ( 6)      39% ( 8)      50% ( 7)   weak: reader C
leds.dt-common                    28% (13)      49% ( 5)      59% ( 7)   weak: reader B, reader C
leds.dt-constants                  9% ( 1)      36% ( 6)      36% ( 1)   middling
leds.dt-multicolor                27% ( 4)      33% ( 4)      46% ( 4)   weak: reader C
leds.dt-links                     45% ( 6)      41% ( 4)      62% ( 4)   all weak
leds.uleds                        19% (11)      18% ( 8)      38% (16)   middling
```

A correction that the checker lists can be about another answer of the same
reader, so the count for a question can be higher than the number of mistakes
in that answer.

## Questions reorganised

- **Parts.** The build set has one part and one `- section:` for each
  subject: Kconfig and header stubs; class device state; the sysfs interface;
  registering an LED; removing an LED; setting brightness; blinking; the
  trigger core; writing a trigger; hardware control; patterns; the multicolor
  class; the flash class; LED consumers; suspend and shutdown; device tree
  bindings; user-space LEDs. Inside a part the questions about requirements
  come last.
- **Moved.**
  - `leds.kconfig` and `leds.header-stubs` have a part of their own, since
    they ask what a caller needs and not where a file is.
  - `leds.brightness-field` is in the part on the state of the class device.
  - `leds.brightness-callbacks` and `leds.brightness-get` are in the part on
    setting brightness.
  - `leds.set-brightness-blinking` is in the part on blinking, beside
    `leds.blink-stop`, so that one answer says what `led_set_brightness()`
    does during a blink.
  - `leds.name-fields` is in the part on registration.
  - `leds.private-trigger` is in the part on the trigger core.
  - `leds.color-ids` is in the part on the device tree bindings, beside
    `leds.dt-constants`, since both ask where the color identifiers are
    defined.
- **Reworded, same id.**
  - `leds.dt-common` asked "which of those properties does it mark as
    deprecated". The hand-written guide says that `label` is deprecated, so
    the question now asks "does it mark any of those properties as
    deprecated".
  - `leds.mc-struct` and `leds.flash-struct` asked what two structures hold.
    The first now asks what they represent. The second asks which settings of
    a flash LED they carry and in which unit each setting is expressed, since
    no reader knew the third setting.
- **Kept as they are.** Every other question has the id, the title, the
  relevance and the text that it has in the measurement set.
- **Added.** `leds.overview` and `leds.model-gaps`, copied from
  `mm-pagetable.md`, and `leds.conventions`, which inserts the conventions.

## Wording after the measurement

After the measurement, the wording of some questions was made clearer in both
sets: a sentence that asked three things became two sentences, and a pronoun
became the name it stood for. What each question asks did not change, so the
numbers above still describe the questions.

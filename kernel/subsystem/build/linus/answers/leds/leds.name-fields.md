- Registered name: lives only in the class device
  (`dev_name(led_cdev->dev)`); `led_cdev->name` is just the proposed name
  when no `struct led_init_data` is passed.
- `led_cdev->name`: never written by the core; the composed and final names
  are stack buffers in `led_classdev_register_ext()`.
- `led_classdev_next_name()`: returns `-ENOMEM` when the suffixed name does
  not fit `LED_MAX_NAME_SIZE`, and registration fails with it.
- `led_cdev->name` of `LED_MAX_NAME_SIZE` characters or more, registered
  without `init_data`: the sysfs name is silently truncated by the
  `strscpy()` in `led_classdev_next_name()`, so it differs from
  `led_cdev->name`.

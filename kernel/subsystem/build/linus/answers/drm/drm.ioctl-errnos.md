- `ENOSPC`: out of VRAM or another limited GPU resource used for rendering, as
  opposed to `ENOMEM` for kernel memory; the error-code list in
  `Documentation/gpu/drm-uapi.rst` names no modeset or bandwidth use.
- `EDEADLK`: sometimes used for resource allocation or reservation failures in
  command submission ioctls.
- `ENXIO`: remote failure, either a hardware transaction such as i2c, or a
  dma-buf or fence exporter that lacks a needed feature.
- `EIO`: the GPU died and reset could not recover it; modeset hardware failure
  goes through the "link status" connector property instead.
- `ENOTTY`: "this IOCTL does not exist"; the list says nothing about feature
  probing.
- `ETIME`, `EFAULT`, `EBUSY`, `ENOTTY`: named as keeping their common meaning.
- `ERANGE` and `EAGAIN`: not on the list.
- Interrupted call: the list names `EINTR` only; any ioctl can return it and
  user space restarts with the parameters unchanged.

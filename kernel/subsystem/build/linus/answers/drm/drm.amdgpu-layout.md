| Job | Under `drivers/gpu/drm/amd/` |
|---|---|
| Core driver | `amdgpu/` |
| Display core | `display/dc/` |
| Display manager | `display/amdgpu_dm/`, a directory; `amdgpu_dm.c` is one file of many. Connector and scaling code is in `amdgpu_dm_connector.c`, interrupt handlers and their registration in `amdgpu_dm_irq.c` |
| Power management | `pm/` (`pm/swsmu/`, `pm/powerplay/`, `pm/legacy-dpm/`) |
| KFD | `amdkfd/` |
| RAS | two places: `amdgpu/amdgpu_ras.c`, and the top-level `ras/` with `ras/core/` and `ras/ras_mgr/`, which `amdgpu/Makefile` includes |
| Hardware sequencer functions | `display/dc/hwss/`, one subdirectory per generation; the hook table is `struct hw_sequencer_funcs` in `display/dc/hwss/hw_sequencer.h` |

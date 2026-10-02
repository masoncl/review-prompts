| Job | In this tree |
|---|---|
| bio submission | `block/error-injection.c` (`CONFIG_BLK_ERROR_INJECTION`) is also on this path: `blk_error_inject()` is the first call in `submit_bio_noacct_nocheck()` in `block/blk-core.c` |
| splitting | `__bio_split_to_limits()` is `static inline` in `block/blk.h`, not in `block/blk-merge.c`; `bio_split_rw_at()` is `static inline` in `include/linux/blkdev.h`; `bio_split()` is in `block/bio.c` |
| request to scatterlist / DMA | `block/blk-mq-dma.c` (always built): `__blk_rq_map_sg()` and, under `CONFIG_BLK_DEV_INTEGRITY`, `blk_rq_map_integrity_sg()`; `blk_rq_map_sg()` is an inline wrapper in `include/linux/blk-mq.h`; none of these is in `block/blk-merge.c` |
| blk-mq CPU-to-queue mapping | `block/blk-mq-cpumap.c`; block/blk-mq-pci.c, block/blk-mq-virtio.c, block/blk-mq-rdma.c and block/blk-mq-map.c do not exist; `blk_mq_map_hw_queues()` takes a `struct device` and serves PCI and virtio drivers alike |
| tags | no block/blk-mq-tag.h: `struct blk_mq_tags` is in `include/linux/blk-mq.h`, prototypes in `block/blk-mq.h`; scheduler tag sets are allocated by `blk_mq_alloc_sched_tags()` in `block/blk-mq-sched.c` into `struct elevator_tags` (`block/elevator.h`) |
| scheduler glue | header is `block/elevator.h`; include/linux/elevator.h does not exist; `block/kyber-iosched.c` is present |
| flush machinery | `struct blk_flush_queue` is in `block/blk.h`; there is no fq_flush_rq identifier |
| zoned support | no block/blk-mq-debugfs-zoned.c; the debugfs `zone_wplugs` handler `queue_zone_wplugs_show()` is in `block/blk-zoned.c` |
| integrity | five files under `CONFIG_BLK_DEV_INTEGRITY`; the two easily missed are `block/bio-integrity-auto.c` (`bio_integrity_prep()`, block-layer automatic generate/verify) and `block/bio-integrity-fs.c` (`fs_bio_integrity_generate()`, `fs_bio_integrity_verify()`); `bio_integrity_generate()` and `bio_integrity_verify()` themselves are in `block/t10-pi.c` |
| rq_qos policies | exactly the three in `enum rq_qos_id` in `block/blk-rq-qos.h`; `block/blk-ioprio.c` has no rq_qos hook, it is entered through `blkcg_set_ioprio()` from `bio_set_ioprio()` in `block/blk-core.c` |
| cgroup support | also `block/blk-cgroup-fc-appid.c` (`CONFIG_BLK_CGROUP_FC_APPID`) |
| disk object | `struct gendisk` is in `include/linux/blkdev.h`; include/linux/genhd.h does not exist; `bd_link_disk_holder()` is in `block/holder.c`, built only with `CONFIG_BLOCK_HOLDER_DEPRECATED`, not in `block/bdev.c` |
| block device object | no blkdev_get_by_dev() or blkdev_get_by_path() is defined (blkdev_get_by_dev survives only in comments); the openers are `bdev_file_open_by_dev()`, `bdev_file_open_by_path()` and `bdev_open()` in `block/bdev.c` |
| SCSI ioctls | no scsi_ioctl.c in `block/`; it is `drivers/scsi/scsi_ioctl.c` |

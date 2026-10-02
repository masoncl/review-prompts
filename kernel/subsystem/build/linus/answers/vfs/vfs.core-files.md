| Job | File in this tree |
|---|---|
| `struct super_block`, `struct super_operations` | `include/linux/fs/super_types.h`, not `include/linux/fs.h` |
| Superblock inline helpers, for example `sb_rdonly()`, `sb_start_write()` | `include/linux/fs/super.h`; `include/linux/fs.h` includes it, and it includes `include/linux/fs/super_types.h` |
| `struct inode`, `struct file`, `struct file_operations`, `struct inode_operations` | still `include/linux/fs.h` |
| `struct dentry` | `include/linux/dcache.h` |
| Every other core job (lookup, caches, superblocks, mounts, open, file and descriptor tables, attributes, readdir, pseudo-filesystem library, mount context) | Models have these right; all under `fs/`, starting from `fs/namei.c` |

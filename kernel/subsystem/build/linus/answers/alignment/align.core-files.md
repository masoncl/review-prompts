| Job | Header | Easy to miss |
|---|---|---|
| Generic round-up, round-down, test and pointer macros | `include/vdso/align.h` | `include/linux/align.h` defines nothing; it only includes `include/vdso/align.h`. |
| Pointer test macro | none | No generic `PTR_IS_ALIGNED()`; the tree's only definition is private to `drivers/net/ethernet/freescale/dpaa/dpaa_eth.c`. |
| Mask forms | `include/vdso/align.h` | `__ALIGN_MASK()` is the only mask form in that header; there is no ALIGN_UP_MASK in the tree. |
| `ALIGN` in assembly files | `include/linux/linkage.h` | A different macro with no arguments: expands to `__ALIGN`, under `__ASSEMBLY__` and not `LINKER_SCRIPT`. |
| Page size and page mask | `include/vdso/page.h` | Every directory under `arch/` includes it from a page header; for example x86 from `arch/x86/include/asm/page_types.h`, arm64 from `arch/arm64/include/asm/page-def.h`. |
| Page size, own definitions | `arch/powerpc/boot/page.h`, `arch/arc/include/uapi/asm/page.h` | The only other `PAGE_SHIFT` definitions outside `tools/`: the powerpc boot wrapper, and the arc branch for non-`__KERNEL__` builds. |
| Page size, generic fallback | none | There is no include/asm-generic/page.h in this tree. |
| Pageblock forms | `include/linux/pageblock-flags.h` | `PAGE_BLOCK_MAX_ORDER`, which the constant forms of `pageblock_order` use, is in `include/linux/mmzone.h`; `include/linux/pageblock-flags.h` includes only `linux/types.h`. |
| Byte address to page frame number, second spelling | `include/asm-generic/memory_model.h` | `__phys_to_pfn()` and `__pfn_to_phys()` expand to `PHYS_PFN()` and `PFN_PHYS()` from `include/linux/pfn.h`. |
| Primitives, page-sized forms, PFN conversions, power-of-two rounding, rounding to a multiple | `include/uapi/linux/const.h`, `include/linux/mm.h`, `include/linux/pfn.h`, `include/linux/log2.h`, `include/linux/math.h` | Headers are listed in the order of the jobs. |

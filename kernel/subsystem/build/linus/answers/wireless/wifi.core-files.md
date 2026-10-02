| Job | File in this tree |
|---|---|
| Simulated radio driver | `drivers/net/wireless/virtual/mac80211_hwsim_main.c`; there is no mac80211_hwsim.c. The module is still `mac80211_hwsim.o`, linked from that file and `drivers/net/wireless/virtual/mac80211_hwsim_nan.c` |
| Simulated radio driver, private state | `drivers/net/wireless/virtual/mac80211_hwsim_i.h` (`struct mac80211_hwsim_data`); `drivers/net/wireless/virtual/mac80211_hwsim.h` holds only the netlink and virtio enums, structs and macros |
| Element parser | `net/mac80211/parse.c`; the entry point is spelled `ieee802_11_parse_elems_full()` |
| Macro that splits change flags | `BSS_CHANGED_VIF_CFG_FLAGS`, defined in `net/mac80211/main.c`, not in a header; nothing outside `net/mac80211/main.c` uses it |
| Capability element layouts | one header per generation: `include/linux/ieee80211-ht.h`, `include/linux/ieee80211-vht.h`, `include/linux/ieee80211-he.h`, `include/linux/ieee80211-eht.h`, `include/linux/ieee80211-uhr.h`, `include/linux/ieee80211-s1g.h`. `include/linux/ieee80211.h` defines none of these capability structs itself; it includes the headers |

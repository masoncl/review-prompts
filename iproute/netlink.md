# Netlink Protocol Patterns

## Request Structure Initialization

Use designated initializers for netlink request structures:

```c
struct {
	struct nlmsghdr  n;
	struct ifaddrmsg ifa;
	char             buf[256];
} req = {
	.n.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifaddrmsg)),
	.n.nlmsg_flags = NLM_F_REQUEST | flags,
	.n.nlmsg_type = cmd,
	.ifa.ifa_family = preferred_family,
};
```

### Common Request Types

```c
/* RTM_NEWLINK / RTM_SETLINK */
struct {
	struct nlmsghdr n;
	struct ifinfomsg i;
	char buf[1024];
} req = {
	.n.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifinfomsg)),
	.n.nlmsg_flags = NLM_F_REQUEST,
	.n.nlmsg_type = RTM_SETLINK,
	.i.ifi_family = AF_UNSPEC,
};

/* RTM_NEWADDR / RTM_DELADDR */
struct {
	struct nlmsghdr n;
	struct ifaddrmsg ifa;
	char buf[256];
} req = {
	.n.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifaddrmsg)),
	.n.nlmsg_flags = NLM_F_REQUEST,
	.n.nlmsg_type = RTM_NEWADDR,
	.ifa.ifa_family = preferred_family,
};

/* RTM_NEWROUTE / RTM_DELROUTE */
struct {
	struct nlmsghdr n;
	struct rtmsg r;
	char buf[1024];
} req = {
	.n.nlmsg_len = NLMSG_LENGTH(sizeof(struct rtmsg)),
	.n.nlmsg_flags = NLM_F_REQUEST,
	.n.nlmsg_type = RTM_NEWROUTE,
	.r.rtm_family = preferred_family,
	.r.rtm_table = RT_TABLE_MAIN,
	.r.rtm_scope = RT_SCOPE_UNIVERSE,
	.r.rtm_protocol = RTPROT_BOOT,
	.r.rtm_type = RTN_UNICAST,
};
```

## Adding Attributes

### Simple Attributes

```c
/* Add raw data */
addattr_l(&req.n, sizeof(req), IFA_LOCAL, &addr.data, addr.bytelen);

/* Add 32-bit value */
addattr32(&req.n, sizeof(req), IFA_RT_PRIORITY, metric);

/* Add 16-bit value */
addattr16(&req.n, sizeof(req), IFLA_VLAN_ID, vlan_id);

/* Add 8-bit value */
addattr8(&req.n, sizeof(req), IFLA_OPERSTATE, state);

/* Add string */
addattr_l(&req.n, sizeof(req), IFLA_IFNAME, name, strlen(name) + 1);
```

### Nested Attributes

**Critical**: Every `addattr_nest()` must be paired with `addattr_nest_end()`.

```c
struct rtattr *nest;

nest = addattr_nest(&req.n, sizeof(req), IFLA_LINKINFO);
addattr_l(&req.n, sizeof(req), IFLA_INFO_KIND, "vlan", 5);

struct rtattr *data = addattr_nest(&req.n, sizeof(req), IFLA_INFO_DATA);
addattr16(&req.n, sizeof(req), IFLA_VLAN_ID, vlan_id);
addattr_nest_end(&req.n, data);

addattr_nest_end(&req.n, nest);
```

### Nested with NLA_F_NESTED Flag

Some attributes require the `NLA_F_NESTED` flag:

```c
struct rtattr *proplist;

proplist = addattr_nest(&req.n, sizeof(req), IFLA_PROP_LIST | NLA_F_NESTED);
addattr_l(&req.n, sizeof(req), IFLA_ALT_IFNAME, name, strlen(name) + 1);
addattr_nest_end(&req.n, proplist);
```

## Sending and Receiving

### Basic Request

```c
if (rtnl_talk(&rth, &req.n, NULL) < 0)
	return -1;
```

### Request with Response

```c
struct nlmsghdr *answer = NULL;

if (rtnl_talk(&rth, &req.n, &answer) < 0) {
	free(answer);
	return -1;
}

/* Process answer */
parse_rtattr(tb, MAX, RTM_RTA(r), len);

free(answer);
```

### Dump Requests

```c
if (rtnl_dump_request(&rth, RTM_GETLINK, &req, sizeof(req)) < 0) {
	perror("Cannot send dump request");
	return -1;
}

if (rtnl_dump_filter(&rth, print_linkinfo, stdout) < 0) {
	fprintf(stderr, "Dump terminated\n");
	return -1;
}
```

## Parsing Responses

### Using parse_rtattr

```c
struct rtattr *tb[IFLA_MAX + 1];

parse_rtattr(tb, IFLA_MAX, IFLA_RTA(ifi), len);

if (tb[IFLA_IFNAME])
	name = rta_getattr_str(tb[IFLA_IFNAME]);

if (tb[IFLA_MTU])
	mtu = rta_getattr_u32(tb[IFLA_MTU]);
```

### Nested Attributes

```c
struct rtattr *linkinfo[IFLA_INFO_MAX + 1];

if (tb[IFLA_LINKINFO]) {
	parse_rtattr_nested(linkinfo, IFLA_INFO_MAX, tb[IFLA_LINKINFO]);
	
	if (linkinfo[IFLA_INFO_KIND])
		kind = rta_getattr_str(linkinfo[IFLA_INFO_KIND]);
}
```

## Error Handling

### Check All Return Values

```c
/* WRONG - ignoring errors */
rtnl_talk(&rth, &req.n, NULL);

/* CORRECT - checking return value */
if (rtnl_talk(&rth, &req.n, NULL) < 0)
	return -1;
```

### Handle Specific Errors

```c
if (rtnl_talk(&rth, &req.n, NULL) < 0) {
	if (errno == EOPNOTSUPP) {
		fprintf(stderr, "Kernel does not support this feature\n");
		return -1;
	}
	if (errno == EEXIST) {
		fprintf(stderr, "Object already exists\n");
		return -1;
	}
	perror("rtnl_talk");
	return -1;
}
```

## Common Patterns

### Device Lookup

```c
req.i.ifi_index = ll_name_to_index(dev);
if (!req.i.ifi_index) {
	nodev(dev);
	return -1;
}
```

### Family-Specific Handling

```c
if (family == AF_INET) {
	addattr_l(&req.n, sizeof(req), IFA_LOCAL, &addr, 4);
} else if (family == AF_INET6) {
	addattr_l(&req.n, sizeof(req), IFA_LOCAL, &addr, 16);
}
```

## Kernel Compatibility

### uapi Header Rules

1. **Separate patches** - uapi updates separate from functionality
2. **Upstream first** - Only after kernel patch merged
3. **Reference commits** - Cite upstream kernel commit hash

### Runtime Feature Detection

Don't assume features exist - check return values:

```c
if (rtnl_talk(&rth, &req.n, NULL) < 0) {
	if (errno == EOPNOTSUPP) {
		fprintf(stderr, "Kernel does not support this feature\n");
		return -1;
	}
	perror("rtnl_talk");
	return -1;
}
```

### Never Use Kernel Version Checks

```c
/* WRONG - do not use */
#ifdef KERNEL_VERSION
#if LINUX_VERSION_CODE >= KERNEL_VERSION(5,10,0)
	/* new feature */
#endif
#endif
```

Instead, rely on runtime detection via return values.

## Common Bugs

### Missing nest_end()

```c
/* WRONG */
struct rtattr *nest;
nest = addattr_nest(&req.n, sizeof(req), IFLA_LINKINFO);
addattr_l(&req.n, sizeof(req), IFLA_INFO_KIND, "vlan", 5);
/* Missing: addattr_nest_end(&req.n, nest); */
```

### Ignoring Return Values

```c
/* WRONG */
rtnl_talk(&rth, &req.n, NULL);

/* CORRECT */
if (rtnl_talk(&rth, &req.n, NULL) < 0)
	return -1;
```

### Wrong Attribute Size

```c
/* WRONG - sizeof(pointer) */
addattr_l(&req.n, sizeof(req), IFA_LOCAL, &addr, sizeof(&addr));

/* CORRECT - actual data size */
addattr_l(&req.n, sizeof(req), IFA_LOCAL, &addr, addr.bytelen);
```

### Memory Leak with Answer

```c
/* WRONG - not freeing answer */
struct nlmsghdr *answer;
if (rtnl_talk(&rth, &req.n, &answer) < 0)
	return -1;
/* answer leaked here */

/* CORRECT */
struct nlmsghdr *answer = NULL;
if (rtnl_talk(&rth, &req.n, &answer) < 0) {
	free(answer);
	return -1;
}
/* process answer */
free(answer);
```

## Complete Example

```c
static int iplink_modify(int cmd, unsigned int flags, int argc, char **argv)
{
	struct {
		struct nlmsghdr n;
		struct ifinfomsg i;
		char buf[1024];
	} req = {
		.n.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifinfomsg)),
		.n.nlmsg_flags = NLM_F_REQUEST | flags,
		.n.nlmsg_type = cmd,
		.i.ifi_family = AF_UNSPEC,
	};
	char *dev = NULL;
	char *type = NULL;
	int mtu = -1;

	while (argc > 0) {
		if (strcmp(*argv, "dev") == 0) {
			NEXT_ARG();
			dev = *argv;
		} else if (strcmp(*argv, "type") == 0) {
			NEXT_ARG();
			type = *argv;
		} else if (strcmp(*argv, "mtu") == 0) {
			NEXT_ARG();
			if (get_unsigned(&mtu, *argv, 0))
				invarg("Invalid MTU\n", *argv);
		}
		argc--; argv++;
	}

	if (!dev) {
		fprintf(stderr, "Error: device not specified\n");
		return -1;
	}

	req.i.ifi_index = ll_name_to_index(dev);
	if (!req.i.ifi_index) {
		nodev(dev);
		return -1;
	}

	if (type) {
		struct rtattr *linkinfo = addattr_nest(&req.n, sizeof(req), IFLA_LINKINFO);
		addattr_l(&req.n, sizeof(req), IFLA_INFO_KIND, type, strlen(type));
		addattr_nest_end(&req.n, linkinfo);
	}

	if (mtu != -1)
		addattr32(&req.n, sizeof(req), IFLA_MTU, mtu);

	if (rtnl_talk(&rth, &req.n, NULL) < 0)
		return -1;

	return 0;
}
```

This demonstrates:
- Designated initializers
- Proper error checking
- Nested attributes with nest_end()
- Device lookup
- Return value checking

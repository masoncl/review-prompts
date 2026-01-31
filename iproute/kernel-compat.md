# Kernel Compatibility

iproute2 aims to be compatible across a wide range of kernel versions. A newer
version of iproute2 will work with older kernels (though new features may not
be available), and older iproute2 versions work with newer kernels (but cannot
access new features).

## Sanitized Kernel Headers (uapi)

The `include/uapi/` directory contains sanitized kernel headers that define
the userspace API for networking. These headers are specific to iproute2 and
allow the tools to be built with support for features that may not yet be
present in the build system's kernel headers.

These headers are generated from the kernel source tree using:

```
make headers_install
```

## Important Rules for uapi Updates

1. **Separate patches** - Updates to `include/uapi/` must be in a separate patch
   from the new functionality that uses them

2. **Upstream first** - Changes to uapi headers will only be accepted once the
   corresponding kernel patch has been merged upstream. Do not submit iproute2
   patches that depend on unmerged (or potentially rejected) kernel changes

3. **Reference kernel commits** - When updating uapi headers, reference the
   upstream kernel commit in your patch description

## Adding Support for New Kernel Features

1. Wait for the kernel patch to be merged upstream
2. Submit a patch updating the relevant headers in `include/uapi/`
3. Submit a separate patch adding the iproute2 functionality
4. The code should handle older kernels gracefully - new attributes sent to
   older kernels may be silently ignored or return an error
5. Test with both old and new kernel versions when possible

## Runtime Feature Detection

Since iproute2 may run on kernels older than what it was built against:

- Check return values from netlink requests - `EOPNOTSUPP` or similar errors
  indicate the kernel doesn't support a feature
- Don't assume features exist - the kernel may silently ignore unknown attributes
- Provide helpful error messages when features aren't available

## Files and Directories

- `ip/` - ip command and subcommands
- `tc/` - traffic control utilities
- `bridge/` - bridge control utilities
- `misc/` - miscellaneous utilities
- `lib/` - shared library code
- `include/` - header files
- `include/uapi/` - sanitized kernel headers (from `make headers_install`)

## Common Patterns

### Netlink Request Structure

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

### Adding Netlink Attributes

```c
addattr_l(&req.n, sizeof(req), IFA_LOCAL, &addr.data, addr.bytelen);
addattr32(&req.n, sizeof(req), IFA_RT_PRIORITY, metric);
addattr_nest(&req.n, sizeof(req), IFLA_PROP_LIST | NLA_F_NESTED);
addattr_nest_end(&req.n, proplist);
```

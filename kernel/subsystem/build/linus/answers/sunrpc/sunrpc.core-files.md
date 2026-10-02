| Job | File | Easy to miss |
|---|---|---|
| Netlink family, policies, ops table | `net/sunrpc/netlink.c` | generated from `Documentation/netlink/specs/sunrpc_cache.yaml`; covers only the `ip_map` and `unix_gid` caches and a cache flush |
| Netlink `doit` and `dumpit` handlers | `net/sunrpc/svcauth_unix.c` | all five handlers named in `sunrpc_nl_ops[]` are defined here |
| Netlink notify and family registration | `net/sunrpc/cache.c`, `net/sunrpc/sunrpc_syms.c` | `sunrpc_cache_notify()` is the multicast sender; `init_sunrpc()` registers `sunrpc_nl_family` |
| Backchannel, callback receiver | `net/sunrpc/backchannel_rqst.c` | calls are processed by `svc_process_bc()` in `net/sunrpc/svc.c`, called from `svc_recv()`; there is no bc_svc_process() |
| Backchannel, callback sender on sockets | `net/sunrpc/xprtsock.c` | `bc_tcp_ops`; replies arrive in `receive_cb_reply()` in `net/sunrpc/svcsock.c` |
| GSS server side, gss-proxy upcall | `net/sunrpc/auth_gss/gss_rpc_upcall.c`, `net/sunrpc/auth_gss/gss_rpc_xdr.c` | the upcall is `gssp_accept_sec_context_upcall()`, called from `net/sunrpc/auth_gss/svcauth_gss.c` |
| GSS Kerberos mechanism | `net/sunrpc/auth_gss/gss_krb5_mech.c` | module is the five `rpcsec_gss_krb5-y` objects in `net/sunrpc/auth_gss/Makefile`; there is no gss_krb5_keys.c |
| Kerberos enctypes and key derivation | `crypto/krb5/` | `RPCSEC_GSS_KRB5` selects `CRYPTO_KRB5`; `net/sunrpc/auth_gss/gss_krb5_mech.c` calls `crypto_krb5_prepare_encryption()` |
| RDMA module init | `net/sunrpc/xprtrdma/module.c` | `rpc_rdma_init()` only calls `rpcrdma_ib_client_register()`, `svc_rdma_init()`, `xprt_rdma_init()`, and on failure their cleanups |
| RDMA client transport class registration | `net/sunrpc/xprtrdma/transport.c` | `xprt_rdma_init()` registers `xprt_rdma` and `xprt_rdma_bc` |
| RDMA server transport class registration | `net/sunrpc/xprtrdma/svc_rdma.c` | `svc_rdma_init()` registers `svc_rdma_class`, which is defined in `net/sunrpc/xprtrdma/svc_rdma_transport.c`; the file also holds the server sysctls |
| RDMA device registration and removal | `net/sunrpc/xprtrdma/ib_client.c` | `struct ib_client`; `rpcrdma_rn_register()` gives removal notification |
| RDMA client memory registration | `net/sunrpc/xprtrdma/frwr_ops.c` | |
| RDMA backchannel, callback receiver | `net/sunrpc/xprtrdma/backchannel.c` | built only with `CONFIG_SUNRPC_BACKCHANNEL` |
| RDMA backchannel, callback sender | `net/sunrpc/xprtrdma/svc_rdma_backchannel.c` | in `rpcrdma-y`, so built without `CONFIG_SUNRPC_BACKCHANNEL` too; defines the client-type `struct xprt_class xprt_rdma_bc` |

- Crypto location: no encryption, checksum or key-derivation step is under
  `net/sunrpc/auth_gss/`; they are in `crypto/krb5/` and the crypto API
  algorithms it allocates (for example `crypto/krb5enc.c`); encryption and
  checksums are reached through `crypto_krb5_encrypt()`,
  `crypto_krb5_decrypt()`, `crypto_krb5_get_mic()` and
  `crypto_krb5_verify_mic()` in `crypto/krb5/krb5_api.c`
  (`include/crypto/krb5.h`).
- `net/sunrpc/auth_gss/`: there is no gss_krb5_keys.c and no gss_krb5_test.c;
  the Kerberos files are the five objects listed in
  `net/sunrpc/auth_gss/Makefile` plus `gss_krb5_internal.h`.
- `net/sunrpc/auth_gss/gss_krb5_crypto.c`: holds only glue from
  `struct xdr_buf` to scatterlists: `xdr_extend_head()`,
  `gss_krb5_aead_encrypt()`, `gss_krb5_aead_decrypt()`,
  `gss_krb5_mic_build_sg()`.
- Absent names: krb5_encrypt, krb5_decrypt, gss_krb5_checksum,
  krb5_etm_checksum, gss_krb5_aes_encrypt, gss_krb5_aes_decrypt,
  krb5_etm_encrypt, krb5_etm_decrypt, krb5_derive_key_v2, krb5_kdf_hmac_sha2
  and krb5_kdf_feedback_cmac are defined nowhere in this tree.
- Enctype table: there is no struct gss_krb5_enctype and no per-enctype method
  table under `net/sunrpc/auth_gss/`; `struct krb5_ctx` carries `krb5e`, a
  `const struct krb5_enctype *` from `crypto_krb5_find_enctype()`, and
  `gss_krb5_get_mic()`, `gss_krb5_verify_mic()`, `gss_krb5_wrap()`,
  `gss_krb5_unwrap()` call the `_v2` functions directly.
- Key setup: `gss_krb5_import_ctx_v2()` is the one path for all enctypes; it
  keys two `struct crypto_aead` and two `struct crypto_shash` with
  `crypto_krb5_prepare_encryption()` and `crypto_krb5_prepare_checksum()`,
  which do the derivation.
- Build-time selection: there are no CONFIG_RPCSEC_GSS_KRB5_ENCTYPES_AES_SHA1,
  CONFIG_RPCSEC_GSS_KRB5_ENCTYPES_AES_SHA2 or
  CONFIG_RPCSEC_GSS_KRB5_ENCTYPES_CAMELLIA symbols;
  `CONFIG_RPCSEC_GSS_KRB5` selects `CONFIG_CRYPTO_KRB5`.
- Offered list: `gss_krb5_prepare_enctype_priority_list()` walks the fixed
  array `gss_krb5_enctypes` in `gss_krb5_mech.c` and keeps each entry that
  `crypto_krb5_find_enctype()` knows.
- Order of the list: 20, 19, 26, 25, 18, 17 (AES-SHA2, then Camellia, then
  AES-SHA1); all six are unconditionally in `krb5_supported_enctypes` in
  `crypto/krb5/krb5_api.c`.
- `crypto_krb5_find_enctype()`: only searches that table; it does not test
  that the underlying algorithms can be allocated, which is found out in
  `gss_krb5_import_ctx_v2()`.
- Consumers of the list: the client sends it as `enctypes=` in
  `gss_encode_v1_msg()`; the server exposes the same string through
  `read_gss_krb5_enctypes()` in `net/sunrpc/auth_gss/svcauth_gss.c`.
- Tests: `crypto/krb5/selftest.c` under `CONFIG_CRYPTO_KRB5_SELFTESTS`; there
  is no KUnit suite for the SunRPC Kerberos code.

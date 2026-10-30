# First full-firmware build target

The official OpenWrt 25.12.6 checkout is NOT yet board-ready for S10:
critical DTS NAND/UBI, NSS DTS includes, wireless boarddata and upgrade
safeguards remain unvalidated. It is misleading to use the official target
without porting these board features.

To test a real firmware compilation path meanwhile, the manually-dispatched
workflow `.github/workflows/experimental-s10.yml` checks out pinned
third-party reference tree `Jim78778/openwrt-ipq@cb047be72907...`,
installs feeds, imports the independently developed eproxy from pinned GitHub
commit, applies `config/s10-experimental.seed`, demands NSS driver/DP/SSDK/
ECM and MHI packages, downloads dependencies and invokes `make -j2 V=s`.

Success proves only that a **third-party reference tree with eproxy** can
compile into an artifact. It does NOT prove correctness on your CPE-S10-SKY,
NSS actually accelerating data, eproxy encrypted-protocol functionality,
or compatibility with the current router. Every artifact carries an explicit
UNFLASHABLE experimental name. Do not use on a live router.

The official-baseline migration remains a separate porting task and
requires serial recovery and 5G/Wi-Fi/NAND/hardware testing.

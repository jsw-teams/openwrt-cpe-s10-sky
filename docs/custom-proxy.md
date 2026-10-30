# eproxy replaces the planned s10-proxy controller

The earlier `s10-proxy` proof of concept is superseded by the independent
[**eproxy** repository](https://github.com/jsw-teams/eproxy). Its two real
OpenWrt packages are `eproxy-core` and `luci-app-eproxy`.

The eproxy core currently implements local HTTP CONNECT and SOCKS5 CONNECT;
these are **not** encrypted remote protocols or full Clash replacements.
VLESS, Shadowsocks, Trojan, Hysteria2 are planned and must be implemented
and tested before their capabilities can be claimed.

The S10 experiment workflow downloads a *pinned commit* from the eproxy repo
and uses the standard OpenWrt build system to cross-compile the packages
into the third-party S10 image. This is a compatibility experiment, not
the final official OpenWrt port. Hardware flashing is not authorized.

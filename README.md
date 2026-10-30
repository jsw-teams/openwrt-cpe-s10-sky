# OpenWrt CPE-S10-SKY — firmware port and experimental builds

**Status: experiments only. The generated firmware must NOT be flashed.**

这是 Swaiot CPE-S10-SKY（IPQ8071A + RM502Q-AE PCIe 5G）专用的公开固件实验工程。该设备的官方 OpenWrt 板级移植、NAND/UBI、ART/BDF、NSS 与安全恢复仍需要进一步核实。

## 两个分离的项目

- **独立代理项目 [eproxy](https://github.com/jsw-teams/eproxy)**：使用 Go 开发新的可扩展代理核心；目前实现 HTTP CONNECT 与 SOCKS5 CONNECT（本机监听），并提供标准 OpenWrt 包 `eproxy-core` 和 LuCI 包 `luci-app-eproxy`。更多加密代理协议、DNS 分流、TUN/nftables 尚未完成。
- **此项目**：OpenWrt 固件源码适配与 GitHub Actions 实验编译。eproxy 通过固定 Git 提交引用，不在此存放私有配置。

## 固件硬性目标

- 以官方 OpenWrt 25.12.6 为最终基线，设备树和板级镜像配方需要审计和移植。
- RM502Q-AE PCIe/MHI 蜂窝上网、LuCI 以及 IPv4/IPv6。
- **NSS 必需**：NSS firmware、driver、DP、SSDK 和 ECM，必须有实际加速的测量证据。
- **eproxy 必需**：最终要有安全的多协议出站代理、可用的 WebUI，能与 NSS、nftables、IPv6 和蜂窝网络共同工作。
- 管理页面最终以 LAN HTTPS 的 `/router/` 访问，`/` 不重定向管理页。此项尚在设计测试阶段。
- 禁止公开设备独有 ART、NOR 分区、原系统配置、密码、代理订阅、私钥、原始镜像。

## 已有的真正构建任务

- `.github/workflows/preflight.yml`：策略检查、回归测试。
- **`.github/workflows/experimental-s10.yml`**：手动运行的完整实验固件编译，固定第三方 S10 专用参考分支 + eproxy Git 提交，检查 NSS/ECM 与 MHI 选择后执行 `make download`、`make -j2 V=s`。
- 实验任务不是官方 OpenWrt S10 移植完成的证明。任何产物标记为 **UNFLASHABLE**，不保证能启动、保留 5G、无线或升级安全。

### 本地验证

```sh
python3 -m unittest discover -s tests -v
python3 tools/preflight.py --mode policy
# Hardware source references need sibling ../upstream, ../source, ../eproxy:
python3 tools/preflight.py --mode hardware --root ..
```

详见 `docs/implementation-plan.md`、`docs/firmware-build-status.md`、`docs/management-path.md` 和 `profiles/firmware-packages.json`。硬件检查未全过之前，正式发布被阻止。

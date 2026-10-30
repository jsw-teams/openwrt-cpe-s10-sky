# S10 固件落地路线与阻塞项

## 第一条路线：立即验证可以编译的代码

GitHub Actions `experimental-s10.yml` 通过固定参考提交 `Jim78778/openwrt-ipq@cb047be72907...` 启动真实 OpenWrt 构建，加入独立 `jsw-teams/eproxy` 里的 `eproxy-core`、`luci-app-eproxy`，并强制选 NSS 驱动、DP、SSDK、ECM 与 MHI。该动作只是验证工具链、软件包和镜像目标能否一起交叉编译，不表示已经取得可安全刷机固件。

## 第二条路线：官方基线板级移植（正式目标）

官方 OpenWrt 25.12.6 本地提交 `64900e756efa667774214f9c6b17c113222e01f7`，现无已验证 CPE-S10-SKY image 定义。第三方 DTS 引用了官方树缺少的 NSS DTS，并把 NAND 控制器标成 disabled。必须与设备运行 DT、MTD/UBI、QSDK 引导方式、ART MAC/无线 BDF、PCIe 电源脚位和网络端口标识进行对照。不能为通过编译就盲目复制设备树或移除升级检查。串口与回退方案必须先完成。

## 第三条路线：eproxy 新核心

`eproxy` 是完全独立项目，复用 Go 标准库实现第一个可测试的本机 HTTP CONNECT/SOCKS5 核心，并基于标准 OpenWrt `golang-package.mk` 构建 `eproxy-core`，提供 LuCI UCI 设置页面。下一阶段按公开协议规范分别实现并验证 Shadowsocks 2022、Trojan、VLESS、Hysteria2，不会把列表当作已实现能力。安全需求包含认证、加密、密钥管理、UDP、TUN、DNS、nftables、IPv6 泄露保护、故障回滚和资源限额。

## 第四条路线：NSS 与代理共存

正式固件 **必须**包含 `nss-firmware-ipq807x`、`kmod-qca-nss-drv`、`kmod-qca-nss-dp`、`kmod-qca-ssdk`、`kmod-qca-nss-ecm`。需验证驱动与官方内核 ABI、NSS 固件版本及实际加速计数。eproxy 用户态数据流不一定走 NSS，5G/以太网/Wi-Fi 的直接转发要与 TUN/proxy 分开测量。Core 无 NSS 只能用于诊断恢复，不作为正式固件。

## 第五条路线：服务、安全和 WebUI

5G RM502Q-AE 的 PCIe 枚举、MHI 通道、拨号协议、重拨、NAT、移动 /64 IPv6 必须实测。Wi-Fi 的 ath11k boarddata、ART、2.4/5 GHz 和冷启动、网关可达性也要覆盖。管理界面目标为 `/router/`，须逐项验证登录、cookie、静态文件、RPC/ubus、备份与上传，不以隐藏路径代替 TLS/ACL。CA 更新及证书撤信任测试需要集成到构建。暂不让任何 Actions 任务刷写设备或向路由器发指令。

## 发版门槛

完成官方板级移植、NSS 与 eproxy 安全多协议功能、蜂窝+Wi-Fi+IPv6、管理入口、证书与恢复流程的真实验收后，才可以称为正式固件。实验构建成功 **不等于**设备可安全刷写。没有真实数据的功能不能标记为通过。

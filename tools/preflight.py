#!/usr/bin/env python3
"""Fail-closed, read-only public policy and local hardware source preflight."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
REQUIRED = {"dropbear", "firewall4", "dnsmasq-full", "odhcp6c",
            "ca-bundle", "ca-certificates", "luci-base", "kmod-mhi-bus"}
FORBIDDEN = {"luci-app-ttyd", "luci-app-upnp", "luci-app-passwall", "luci-app-samba4"}


def load_manifest(path=PROJECT / "profiles" / "firmware-packages.json"):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def policy_checks(manifest):
    result = []
    def add(name, ok):
        result.append({"check": name, "passed": bool(ok)})
    m = manifest["management"]
    add("management path is a prefixed route", m["path"] == "/router/")
    add("root is not a LuCI redirect", m["root_behavior"] == 404)
    add("management is LAN and HTTPS only",
        m["lan_only"] is True and m["wan_exposed"] is False and m["https_only"] is True)
    core = manifest["profiles"]["core"]["required"]
    add("base profile has no duplicates", len(core) == len(set(core)))
    add("basic security and management packages present", REQUIRED.issubset(set(core)))
    add("forbidden optional services absent from base", set(core).isdisjoint(FORBIDDEN))
    add("diagnostic-only Core does not masquerade as NSS release",
        not any("nss" in name.lower() for name in core))
    nss = manifest["profiles"].get("nss_required", {})
    daily = manifest["profiles"]["daily"]
    nss_required = {"nss-firmware-ipq807x", "kmod-qca-nss-drv",
                    "kmod-qca-nss-dp", "kmod-qca-ssdk", "kmod-qca-nss-ecm"}
    eproxy_required = {"eproxy-core", "luci-app-eproxy"}
    add("NSS firmware, DP, SSDK and ECM mandatory for release",
        nss_required.issubset(set(nss.get("required", []))))
    add("eproxy-core and LuCI mandatory",
        eproxy_required.issubset(set(daily.get("additional", []))))
    add("eproxy core required in runtime manifest",
        any(x.get("name") == "eproxy-core" and x.get("required_for_release") is True
            for x in daily.get("required_runtime", [])))
    add("encrypted protocols still explicitly blocked",
        any(x.get("name") == "encrypted outbound proxy protocols"
            and x.get("status", "").startswith("BLOCKED")
            for x in daily.get("required_runtime", [])))
    add("Both daily and NSS profiles are mandatory for release",
        set(manifest["release"]["required_profiles"]) == {"daily", "nss_required"})
    all_names = []
    for entry in manifest["profiles"].values():
        all_names.extend(entry.get("required", []))
        all_names.extend(entry.get("additional", []))
        for variants in entry.get("conditional", {}).values():
            all_names.extend(variants)
    add("package identifiers have valid syntax",
        all(bool(re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9+_.-]*", name)) for name in all_names))
    add("release needs verified hardware, NSS and eproxy together",
        manifest["policy"]["nss_must_be_required_for_release"] is True
        and manifest["policy"]["eproxy_must_be_required_for_release"] is True
        and manifest["policy"]["software_forwarding_is_debug_only"] is True
        and manifest["release"]["status"].startswith("BLOCKED")
        and bool(manifest["policy"]["flash_gate"]))
    return result


def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def revision(path):
    try:
        result = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                                capture_output=True, text=True, timeout=8, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def hardware_checks(root):
    root = Path(root)
    official = root / "upstream"
    reference = root / "source"
    img = read(official / "target/linux/qualcommax/image/ipq807x.mk")
    ref_img = read(reference / "target/linux/qualcommax/image/ipq807x.mk")
    ref_dts = read(reference /
                   "target/linux/qualcommax/files/arch/arm64/boot/dts/qcom/ipq8074-s10.dts")
    bdf = read(reference / "package/firmware/ipq-wifi/Makefile")
    feed = read(reference / "feeds.conf.default")
    checks = []
    def add(name, ok, detail):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
    add("official source checkout", revision(official) is not None, "offline git revision")
    add("reference board DTS available",
        'compatible = "swaiot,cpe-s10-sky"' in ref_dts,
        "third-party source, reference only")
    add("official S10 image profile",
        "TARGET_DEVICES += swaiot_cpe_s10" in img, "must be ported and reviewed")
    add("explicit supported_devices and upgrade safeguards",
        "SUPPORTED_DEVICES := swaiot,cpe-s10-sky" in img,
        "device name alone is not sufficient")
    add("NAND/UBI DTS independently reconciled", False,
        "requires cross-check with running FDT/MTD and recovery; never auto-pass by regex")
    add("S10 board-specific radio data mapping",
        "swaiot_cpe_s10" in bdf,
        "reference ipq-wifi registration is only a starting point")
    add("QModem feed declared in reference",
        bool(re.search(r"^src-git(?:-full)?\s+qmodem\s+", feed, re.MULTILINE)),
        "third-party feed must be independently pinned and audited")
    nss_dir = reference / "feeds/nss_packages"
    nss_config = read(reference / ".config")
    add("NSS firmware/driver/DP/ECM source packages available in reference",
        (nss_dir / "qca-nss-drv/Makefile").is_file()
        and (nss_dir / "qca-nss-ecm/Makefile").is_file()
        and (reference / "package/kernel/qca-nss-dp/Makefile").is_file()
        and (reference / "package/kernel/qca-ssdk/Makefile").is_file(),
        "reference packages exist; not verified for official kernel")
    add("NSS ECM selected in reference config",
        "CONFIG_PACKAGE_kmod-qca-nss-ecm=y" in nss_config,
        "NSS ECM not selected in downloaded config")
    add("NSS successfully built for official kernel", False,
        "required for release; source visibility is not ABI compatibility")
    eproxy = root / "eproxy"
    add("independent eproxy OpenWrt packages exist",
        (eproxy / "package/eproxy-core/Makefile").is_file()
        and (eproxy / "package/luci-app-eproxy/Makefile").is_file(),
        "GitHub source presence not proof of device compatibility")
    add("encrypted protocols and eproxy transparent routing validated", False,
        "not yet implemented or tested")
    add("MHI/RM502Q-AE on new kernel verified", False, "requires actual modem and PCIe tests")
    add("LuCI /router/ asset/login/ubus flows verified", False, "requires integration tests")
    add("official CA trust integrated and verified", False, "requires build-time and negative-chain tests")
    add("serial recovery and safe device test", False, "requires physical hardware")
    return checks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("policy", "hardware"), default="policy")
    parser.add_argument("--root", type=Path, default=PROJECT.parent,
                        help="parent with source/, upstream/, nss-upstream/")
    args = parser.parse_args(argv)
    checks = policy_checks(load_manifest())
    if args.mode == "hardware":
        checks.extend(hardware_checks(args.root))
    failed = [x for x in checks if not x["passed"]]
    print(json.dumps({"mode": args.mode, "passed": len(checks)-len(failed),
                      "total": len(checks), "failed": failed,
                      "safe_to_flash": False}, indent=2, ensure_ascii=False))
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

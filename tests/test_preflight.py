import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import preflight  # noqa: E402


class ManifestPolicyTests(unittest.TestCase):
    def test_policy_passes(self):
        manifest = preflight.load_manifest()
        checks = preflight.policy_checks(manifest)
        self.assertTrue(all(x["passed"] for x in checks), checks)

    def test_wan_exposure_cannot_pass(self):
        m = json.loads(json.dumps(preflight.load_manifest()))
        m["management"]["wan_exposed"] = True
        self.assertFalse(all(x["passed"] for x in preflight.policy_checks(m)))

    def test_luci_at_root_cannot_pass(self):
        m = json.loads(json.dumps(preflight.load_manifest()))
        m["management"]["path"] = "/"
        self.assertFalse(all(x["passed"] for x in preflight.policy_checks(m)))

    def test_high_risk_optional_package_cannot_enter_core(self):
        m = json.loads(json.dumps(preflight.load_manifest()))
        m["profiles"]["core"]["required"].append("luci-app-ttyd")
        self.assertFalse(all(x["passed"] for x in preflight.policy_checks(m)))

    def test_missing_source_fails_closed(self):
        with self.subTest("missing source must not pass"):
            checks = preflight.hardware_checks(ROOT / "nonexistent-hardware")
            self.assertTrue(any(not x["passed"] for x in checks))


    def test_required_nss_cannot_be_removed(self):
        m = json.loads(json.dumps(preflight.load_manifest()))
        m["profiles"]["nss_required"]["required"].remove("kmod-qca-nss-ecm")
        self.assertFalse(all(x["passed"] for x in preflight.policy_checks(m)))

    def test_required_eproxy_cannot_be_removed(self):
        m = json.loads(json.dumps(preflight.load_manifest()))
        m["profiles"]["daily"]["additional"].remove("eproxy-core")
        self.assertFalse(all(x["passed"] for x in preflight.policy_checks(m)))

    def test_eproxy_cannot_be_omitted(self):
        m = json.loads(json.dumps(preflight.load_manifest()))
        m["profiles"]["daily"]["required_runtime"] = []
        self.assertFalse(all(x["passed"] for x in preflight.policy_checks(m)))

    def test_release_cannot_be_without_nss(self):
        m = json.loads(json.dumps(preflight.load_manifest()))
        m["release"]["required_profiles"] = ["daily"]
        self.assertFalse(all(x["passed"] for x in preflight.policy_checks(m)))


if __name__ == "__main__":
    unittest.main()

# Route LuCI under /router/ — design contract

**Design status: NOT DEPLOYABLE. Never apply directly to the running router.**

## Requested public LAN URLs

| Request | Expected |
| --- | --- |
| `https://192.168.1.1/` | HTTP 404 / no LuCI redirect |
| `https://192.168.1.1/router/` | LuCI login |
| `https://192.168.1.1/router/admin/network/` | LuCI network section |
| `https://192.168.1.1/cgi-bin/luci/` | Not publicly served |
| any WAN/guest request | blocked by firewall and web ACL |

Target: **Nginx**, with its maintained OpenWrt LuCI/CGI/uWSGI integrations and TLS. OpenResty is not required simply to provide a path-based entry point. Enable OpenResty/Lua modules only if a concrete, tested feature needs them.

## Why an untested proxy_pass is unacceptable

LuCI generates application URLs, redirects, static references, ubus calls and upload/download/backup CGI endpoints. An Nginx `location /router/ { proxy_pass ... }` alone often leaves absolute routes such as `/cgi-bin/luci/` and `/luci-static/` escaping the prefix. A URL redirect from `/router/` back to `/cgi-bin/luci` also violates the requested public path.

Use the supported Nginx LuCI integration (candidate components: nginx-ssl, nginx-mod-luci, uwsgi, uwsgi-luci-support, nginx-mod-ubus). First prototype a CGI SCRIPT_NAME/PATH_INFO prefix adaptation, and verify the public URL always retains `/router/`. Do not blindly add HTML/JS substitution rules for arbitrary responses.

## Security gates

1. Bind management listener to trusted LAN addresses only; WAN firewall must reject traffic. Do not open port-forwarding or UPnP to management.
2. HTTPS only; test certificate trust and hostname. Do not embed private keys in Git.
3. Preserve LuCI/rpcd authentication, per-method ACLs, CSRF protection, session-cookie scope, and session expiration.
4. Restrict access to `/router/` and required prefixed assets/APIs only; root and unexpected paths return 404. Test encoded-path traversal and double-slash variants.
5. Upload, download, sysupgrade, ubus (XHR/JSON), system logs, session renewal and browser back/forward must pass.
6. Ensure WebSocket upgrade works *if* any chosen application requires it.
7. Test after login with fresh browser and cache cleared; every response must remain under the intended URL prefix.
8. Preserve isolated emergency recovery access (serial, and separately controlled SSH). Do not remove working management access before the new route is fully tested.

## Acceptance matrix

- GET / -> 404 (no redirect)
- GET /router/ -> login (no unexpected redirect outside /router/)
- GET /router/admin/network/ -> authenticated route
- CSS, JS, AJAX, ubus requests and CSRF all functional, **without public root-level assets**
- Login/logout and refresh do not change prefix or create redirect loops
- Missing or malformed credentials reject requests
- WAN and untrusted VLAN cannot connect
- Restore/upgrade flows tested on a safe, disposable environment before moving to real hardware

No Nginx live configuration is provided here because SCRIPT_NAME, uWSGI CGI mount and LuCI version-specific path behavior must be validated against the final firmware. A root 404 is **not a security boundary**.

# claude-usage-yasb

YASB widget showing Claude.ai session and weekly usage limits.

**Preview:** ⚡ 42% 3h 29m 📅 39% 2d 5h

Percentages turn yellow when above 85%.

> **Security notice:** This widget reads `sessionKey` from your browser's local cookie storage (`cookies.sqlite`) to authenticate with claude.ai. The key is only sent to `claude.ai` — no third parties. It is stored in plaintext in `~/.claude_usage_yasb.json` on your local machine. Do not use on shared or untrusted computers.

---

## Installation

```
pip install claude-usage-yasb
```

For Chrome/Edge/Brave support (Windows only):

```
pip install "claude-usage-yasb[chrome]"
```

---

## YASB Setup

### 1. Add widget to config.yaml

```yaml
widgets:
  claude-usage:
    type: "yasb.custom.CustomWidget"
    options:
      label: "{data}"
      label_alt: "{data}"
      class_name: "claude-usage-widget"
      exec_options:
        run_cmd: "claude-usage-yasb"
        run_interval: 60000
        return_format: "string"
```

### 2. Add to bar layout

```yaml
center: ["claude-usage"]
```

### 3. Open claude.ai in your browser

That's it — the widget reads cookies automatically from Firefox or Chrome.
No manual configuration needed.

---

## How it works

1. Reads `sessionKey` and `org_id` from Firefox/Chrome cookies
2. Calls `claude.ai/api/organizations/{org_id}/usage`
3. Displays session % with reset timer and weekly %

**Supported browsers:** Firefox, Chrome, Edge, Brave

Cookie refresh is automatic — as long as you're logged in to claude.ai in your browser.

---

## Troubleshooting

| Message | Fix |
|---|---|
| `Claude: открой claude.ai в браузере` | Open claude.ai and log in |
| `Claude: auth expired` | Refresh claude.ai tab in browser |
| `Claude: err` | Run `pip install curl_cffi` |

---

## Optional CSS

```css
.claude-usage-widget {
    padding: 0 6px;
}
```

---

## Publishing to PyPI

```
pip install build twine
python -m build
twine upload dist/*
```
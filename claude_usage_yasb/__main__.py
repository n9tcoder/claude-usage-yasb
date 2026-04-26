# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os
import time
from datetime import datetime, timezone

from . import firefox, chrome

CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.claude_usage_yasb.json')


def load_cookies():
    cookies = firefox.read_cookies()
    if not cookies.get('sessionKey'):
        cookies = chrome.read_cookies()
    return cookies


def load_config():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            cfg = json.load(f)

    cookies = load_cookies()
    if cookies.get('sessionKey'):
        cfg['sessionKey'] = cookies['sessionKey']
    if cookies.get('anthropic-device-id'):
        cfg['anthropic_device_id'] = cookies['anthropic-device-id']
    if cookies.get('lastActiveOrg'):
        cfg['org_id'] = cookies['lastActiveOrg']

    if cfg:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(cfg, f, indent=2)

    return cfg


def main():
    cfg = load_config()

    org_id = cfg.get('org_id', '')
    session_key = cfg.get('sessionKey', '')
    device_id = cfg.get('anthropic_device_id', '')

    if not org_id or not session_key:
        print('Claude: open claude.ai in browser')
        return

    try:
        from curl_cffi import requests as cf_requests

        resp = None
        for attempt in range(3):
            try:
                resp = cf_requests.get(
                    f'https://claude.ai/api/organizations/{org_id}/usage',
                    impersonate='firefox',
                    timeout=8,
                    headers={
                        'Accept': 'application/json',
                        'anthropic-client-platform': 'web_claude_ai',
                        'anthropic-client-version': '1.0.0',
                        'anthropic-device-id': device_id,
                        'Referer': 'https://claude.ai/settings/usage',
                    },
                    cookies={
                        'sessionKey': session_key,
                        'anthropic-device-id': device_id,
                    }
                )
                break
            except Exception:
                if attempt < 2:
                    time.sleep(5)
                else:
                    raise

        if resp.status_code != 200:
            print('Claude: auth expired')
            return

        data = resp.json()
        five_hour = data.get('five_hour', {})
        session_pct = five_hour.get('utilization', 0)
        seven_day   = data.get('seven_day', {})
        week_pct    = seven_day.get('utilization', 0)

        week_reset = ''
        week_resets_str = seven_day.get('resets_at', '')
        if week_resets_str:
            week_resets_at = datetime.fromisoformat(week_resets_str).replace(tzinfo=timezone.utc)
            diff_w = int((week_resets_at - datetime.now(timezone.utc)).total_seconds())
            if diff_w > 86400:
                d = diff_w // 86400
                h = (diff_w % 86400) // 3600
                week_reset = f'{d}d {h}h'
            elif diff_w > 3600:
                h = diff_w // 3600
                m = (diff_w % 3600) // 60
                week_reset = f'{h}h {m}m'
            elif diff_w > 0:
                week_reset = f'{diff_w // 60}m'

        resets_str = five_hour.get('resets_at', '')
        time_left = ''
        if resets_str:
            resets_at = datetime.fromisoformat(resets_str)
            diff = int((resets_at - datetime.now(timezone.utc)).total_seconds())
            if diff > 0:
                h, m = divmod(diff // 60, 60)
                time_left = f'{h}h {m:02d}m' if h else f'{m}m'

        WARN = '#FFD700'
        OK   = '#ffffff'
        s_color = WARN if session_pct > 85 else OK
        w_color = WARN if week_pct    > 85 else OK

        s_span     = f'<span style="color:{s_color};">{session_pct:.0f}%</span>'
        w_span     = f'<span style="color:{w_color};">{week_pct:.0f}%</span>'
        timer_part = f' {time_left}' if time_left else ''
        reset_part = f' {week_reset}' if week_reset else ''

        print(f'<span>\uf0e7</span> {s_span}{timer_part} <span>\uf073</span> {w_span}{reset_part}')

    except Exception:
        print('Claude: err')


if __name__ == '__main__':
    main()
'''
Cron-safe URL health checker that notifies a Discord webhook on failures only.
Reads URLs from environment or a file. See README section in the Dockerfile comment.
'''
import datetime as _dt
import discord
import dotenv
import os
import platform
import requests
import socket
import urllib.parse

dotenv.load_dotenv(override=True)

_HEALTHCHECK_URLS_RAW = os.getenv('HEALTHCHECK_URLS', '')
URLS_FILE = os.getenv('URLS_FILE', 'urls.txt').strip()
ENV_NAME = os.getenv('ENV_NAME', 'unknown')
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '').strip()


def _parse_urls_blob(blob: str):
    if not blob:
        return []
    # split by comma, space, or newline
    parts = [p.strip() for chunk in blob.split('\n') for p in chunk.replace(',', ' ').split()]
    return [p for p in parts if p and not p.startswith('#')]


def _load_urls():
    # Prefer env list if provided; else fall back to file
    urls = _parse_urls_blob(_HEALTHCHECK_URLS_RAW)
    if urls:
        return urls

    urls = []
    try:
        with open(URLS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                urls.append(line)
    except FileNotFoundError:
        pass
    return urls


def check_urls(urls):
    '''Check each URL and return a list of failure dicts with details.'''
    failures = []
    for url in urls:
        started = _dt.datetime.now()
        try:
            response = requests.get(url, timeout=10)
            elapsed_ms = int(response.elapsed.total_seconds() * 1000)
            if response.status_code >= 400:
                failures.append({
                    'url': url,
                    'status_code': response.status_code,
                    'error': None,
                    'elapsed_ms': elapsed_ms,
                    'checked_at': started,
                    'host': urllib.parse.urlparse(url).netloc,
                })
        except requests.RequestException as exc:
            elapsed_ms = int(((_dt.datetime.now() - started).total_seconds()) * 1000)
            failures.append({
                'url': url,
                'status_code': None,
                'error': f'{type(exc).__name__}: {exc}',
                'elapsed_ms': elapsed_ms,
                'checked_at': started,
                'host': urllib.parse.urlparse(url).netloc if '://' in url else url,
            })
    return failures


def _as_reason(item):
    '''Human-readable reason string for a failure item.'''
    if item.get('error'):
        return item['error']
    if item.get('status_code') is not None:
        return f"HTTP {item['status_code']}"
    return 'Unknown error'


def notify_discord_on_failures(failures, total_urls):
    '''Send an emergency notification to Discord only when there are failures.'''
    if not failures:
        return  # Stay silent when everything is healthy

    hook = discord.SyncWebhook.from_url(WEBHOOK_URL)
    hostname = platform.node() or socket.gethostname()
    now_utc = _dt.datetime.now()

    embed = discord.Embed(
        title='🚨 URL Health Check: FAIL',
        description=(
            f'**{len(failures)}/{total_urls}** endpoints failing in **{ENV_NAME}**.\n'
            f"Host: `{hostname}` · {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        ),
        color=0xE74C3C,  # red
        timestamp=now_utc
    )

    # Show up to 20 detailed entries to avoid hitting Discord limits.
    max_items = 20
    for item in failures[:max_items]:
        reason = _as_reason(item)
        rt = f"{item['elapsed_ms']} ms" if item.get('elapsed_ms') is not None else 'n/a'
        name = f"❌ {item['host']}"
        value = f"{item['url']}\n• **Reason:** {reason}\n• **Latency:** {rt}"
        embed.add_field(name=name, value=value, inline=False)

    remaining = len(failures) - max_items
    if remaining > 0:
        embed.add_field(
            name='…and more',
            value=f'{remaining} additional failures not shown.',
            inline=False
        )

    embed.set_footer(text='Immediate attention required')

    # Ping responders (use @here by default; replace with a role mention if desired)
    # Example for role ping: content='<@&ROLE_ID>'
    allowed = discord.AllowedMentions(everyone=True)
    hook.send(content='@here', embed=embed, allowed_mentions=allowed)


if __name__ == '__main__':
    urls = _load_urls()
    errors = check_urls(urls)
    notify_discord_on_failures(errors, total_urls=len(urls))

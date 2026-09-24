"""Declare image input for deepseek-flash in DSH settings, with a backup.

The plugin patch makes `inputModalities` a per-model catalog field; this opts the one
model that needs it in. Only `deepseek-flash` (DeepSeek-V4.1-Flash) is declared
multimodal. DeepSeek-V4-Flash and V4-Pro are left text-only deliberately: the harness
should refuse an image locally for a route that cannot read one, rather than forward it
and fail with a provider error that says nothing about the real cause.

Backs up the previous settings.yaml so the change is reversible, and preserves the
existing entries and key order.
"""
import io
import os
import re
import shutil

SETTINGS = os.path.join(os.path.expanduser('~'), '.dsh', 'settings.yaml')
BACKUP = SETTINGS + '.vision-backup'


def main():
    if not os.path.exists(SETTINGS):
        print('not found: %s' % SETTINGS)
        return 1
    text = io.open(SETTINGS, encoding='utf-8').read()

    if 'inputModalities' in text:
        print('settings.yaml already declares inputModalities; nothing to do')
        return 0

    # insert the field after the deepseek-flash entry's contextWindow line
    pat = re.compile(
        r'(?P<indent>[ \t]*)- id: deepseek-flash\n'
        r'(?P<body>(?:[ \t]+[^\n]*\n)*?)'
        r'(?P<cw>[ \t]+contextWindow:\s*\d+\n)')
    m = pat.search(text)
    if not m:
        print('could not locate the deepseek-flash entry; settings.yaml unchanged')
        print('--- current content ---')
        print(text)
        return 1

    field = '%s  inputModalities: ["text", "image"]\n' % m.group('indent')
    patched = text[:m.end('cw')] + field + text[m.end('cw'):]

    shutil.copy2(SETTINGS, BACKUP)
    print('backup written: %s' % BACKUP)
    io.open(SETTINGS, 'w', encoding='utf-8', newline='\n').write(patched)
    print()
    print('--- settings.yaml now ---')
    print(patched)
    print('restart DSH for the plugin and this config to take effect')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

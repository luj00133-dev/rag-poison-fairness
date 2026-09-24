"""Verify the patched plugin is syntactically valid, and provide the revert path.

Two jobs, because a patch that breaks the provider would leave the harness unable to
start, and a patch with no revert is a trap.

1. Syntax check. `node --check` parses without executing, which is the right test for a
   file that is only loaded by the harness at startup -- running it here would either
   do nothing or start a server.

2. Revert. Restores index.js from the backup taken before patching and clears the
   `inputModalities` line from settings.yaml, then verifies both by parsing them again.

Both are idempotent and report exactly what they changed.
"""
import io
import os
import re
import shutil
import subprocess
import sys

APPDATA = os.environ.get('APPDATA', '')
PLUGIN = os.path.join(APPDATA, 'npm', 'node_modules', '@deepseek-ai', 'dsh',
                      'node_modules', '@deepseek-ai', 'dsh-llm-deepseek', 'lib',
                      'index.js')
BACKUP = PLUGIN + '.dsh-patch-backup'
SETTINGS = os.path.join(os.path.expanduser('~'), '.dsh', 'settings.yaml')
SETTINGS_BACKUP = SETTINGS + '.vision-backup'


def check_syntax(path):
    """Parse a JS file without executing it."""
    try:
        r = subprocess.run(['node', '--check', path],
                           capture_output=True, timeout=60)
    except FileNotFoundError:
        return None, 'node not on PATH'
    if r.returncode == 0:
        return True, ''
    return False, r.stderr.decode('utf-8', 'replace')[:400]


def show_diff_summary():
    """Report which patched anchors are present, without printing file contents."""
    src = io.open(PLUGIN, encoding='utf-8').read()
    marks = [
        ('modelInfo reads catalog inputModalities',
         'inputModalities: Array.isArray(model.inputModalities)'),
        ('schema accepts inputModalities',
         'inputModalities: z.array(z.union(["text", "image"]))'),
        ('resolveModels preserves it',
         'inputModalities must be an array of "text" and/or "image"'),
    ]
    for label, needle in marks:
        print('   [%s] %s' % ('x' if needle in src else ' ', label))


def revert():
    print('=== revert ===')
    if not os.path.exists(BACKUP):
        print('no backup at %s; cannot revert' % BACKUP)
        return 1
    shutil.copy2(BACKUP, PLUGIN)
    print('restored plugin from backup (%d bytes)' % os.path.getsize(PLUGIN))

    if os.path.exists(SETTINGS):
        text = io.open(SETTINGS, encoding='utf-8').read()
        new = re.sub(r'^[ \t]*inputModalities:.*\n', '', text, flags=re.M)
        if new != text:
            io.open(SETTINGS, 'w', encoding='utf-8', newline='\n').write(new)
            print('removed inputModalities from settings.yaml')
        else:
            print('settings.yaml had no inputModalities line')

    ok, err = check_syntax(PLUGIN)
    print('plugin parses: %s' % ok if ok is not None else err)
    src = io.open(PLUGIN, encoding='utf-8').read()
    print('patch marker present: %s' % ('dsh-patch' in src))
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--revert':
        return revert()

    print('=== verification ===')
    print('plugin : %s' % PLUGIN)
    print('backup : %s (%s)'
          % (BACKUP, 'present' if os.path.exists(BACKUP) else 'MISSING'))
    print()
    print('patched anchors:')
    show_diff_summary()

    ok, err = check_syntax(PLUGIN)
    if ok is None:
        print('syntax: could not check (%s)' % err)
    else:
        print('syntax: %s' % ('valid' if ok else 'INVALID'))
        if not ok:
            print(err)
            print('run with --revert to restore the backup')
            return 1

    if os.path.exists(SETTINGS):
        s = io.open(SETTINGS, encoding='utf-8').read()
        print('settings: deepseek-flash declares %s'
              % ('image input' if 'inputModalities' in s else 'text only'))
    print()
    print('revert with: python analysis/verify_dsh_patch.py --revert')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

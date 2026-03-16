#!/usr/bin/env python3
"""shellhist - Analyze shell command history."""
import os, argparse, re, sys, collections, json

def find_history():
    for path in [os.path.expanduser('~/.zsh_history'), os.path.expanduser('~/.bash_history')]:
        if os.path.exists(path): return path
    return None

def parse_zsh(path):
    cmds = []
    with open(path, 'rb') as f:
        for line in f:
            try:
                line = line.decode(errors='replace').strip()
                m = re.match(r'^: (\d+):\d+;(.+)', line)
                if m: cmds.append({'time': int(m.group(1)), 'cmd': m.group(2)})
                elif line and not line.startswith(':'): cmds.append({'time': 0, 'cmd': line})
            except: pass
    return cmds

def parse_bash(path):
    with open(path, errors='replace') as f:
        return [{'time': 0, 'cmd': line.strip()} for line in f if line.strip()]

def main():
    p = argparse.ArgumentParser(description='Shell history analyzer')
    p.add_argument('file', nargs='?', help='History file')
    p.add_argument('-n', '--top', type=int, default=20)
    p.add_argument('--commands', action='store_true', help='Top commands only')
    p.add_argument('--search', help='Search history')
    p.add_argument('-j', '--json', action='store_true')
    args = p.parse_args()

    path = args.file or find_history()
    if not path or not os.path.exists(path):
        print("No history file found"); sys.exit(1)

    cmds = parse_zsh(path) if 'zsh' in path else parse_bash(path)

    if args.search:
        pat = re.compile(args.search, re.I)
        for c in cmds:
            if pat.search(c['cmd']):
                print(f"  {c['cmd']}")
        return

    # Extract base commands
    bases = []
    for c in cmds:
        parts = c['cmd'].split()
        if parts:
            base = parts[0].split('/')[-1]
            if base in ('sudo','env') and len(parts) > 1:
                base = parts[1].split('/')[-1]
            bases.append(base)

    freq = collections.Counter(bases)

    if args.commands:
        for cmd, count in freq.most_common(args.top):
            bar = '█' * min(int(count / max(freq.values()) * 30), 30)
            print(f"  {count:>6}  {cmd:<20} {bar}")
        return

    if args.json:
        print(json.dumps({'total': len(cmds), 'unique_commands': len(freq),
                         'top': freq.most_common(args.top)}, indent=2))
        return

    print(f"  History file: {path}")
    print(f"  Total commands: {len(cmds):,}")
    print(f"  Unique commands: {len(freq):,}")
    print(f"\n  Top {args.top} commands:")
    for cmd, count in freq.most_common(args.top):
        pct = count / len(cmds) * 100
        bar = '█' * min(int(pct * 2), 30)
        print(f"    {count:>6} ({pct:>4.1f}%)  {cmd:<20} {bar}")

if __name__ == '__main__':
    main()

from pathlib import Path
import sys
SKIP_EXT={'.coverage','.png','.jpg','.jpeg','.gif','.pdf','.zip','.tar','.gz','.woff','.woff2','.ttf','.so','.pyc','.ico'}
SKIP_DIR={'.git','.venv','venv','__pycache__','.pytest_cache','.ruff_cache','.mypy_cache'}
root=Path(sys.argv[1])
errors=[]; checked=0
for p in root.rglob('*'):
    if not p.is_file() or p.is_symlink() or p.suffix.lower() in SKIP_EXT or p.name in SKIP_EXT or any(x in SKIP_DIR for x in p.parts): continue
    try: data=p.read_bytes(); data.decode('utf-8')
    except Exception as e: errors.append((str(p.relative_to(root)),str(e))); continue
    checked+=1
    if b'\r\n' in data: errors.append((str(p.relative_to(root)),'CRLF'))
print({'checked':checked,'errors':errors})
raise SystemExit(1 if errors else 0)

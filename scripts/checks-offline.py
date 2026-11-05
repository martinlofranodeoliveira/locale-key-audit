"""Run public or independently supplied tests in a read-only offline namespace."""
import argparse,errno,hashlib,os,shutil,socket,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OMIT={'.git','.venv','__pycache__','build','dist','.pytest_cache'}
def files(root):
 for directory,names,filenames in os.walk(root,followlinks=False):
  names[:]=[n for n in names if n not in OMIT]
  for n in names:
   if (Path(directory)/n).is_symlink():raise ValueError('Source symlinks refused')
  for n in filenames:
   if n=='.env' or n.startswith('.env.') or n.endswith(('.jsonl','.log')):continue
   p=Path(directory)/n
   if p.is_symlink():raise ValueError('Source symlinks refused')
   yield p
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files(root)}
def copy(source,target):
 for p in files(source):
  d=target/p.relative_to(source);d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d)
def inner(oracle):
 status=dict(x.split(':',1) for x in Path('/proc/self/status').read_text().splitlines() if ':' in x)
 assert int(status['CapEff'],16)==0 and status['NoNewPrivs'].strip()=='1'
 assert not Path('/home').exists() and not Path('/root').exists() and not Path('/work/.git').exists() and not Path('/work/.env').exists()
 for p in ['/work/README.md']+(['/oracle/test_independent.py'] if oracle else []):
  try:os.open(p,os.O_WRONLY)
  except OSError as e:assert e.errno==errno.EROFS
  else:raise AssertionError('Source or oracle writable')
 with socket.socket() as s:
  try:s.connect(('1.1.1.1',443))
  except OSError as e:assert e.errno==errno.ENETUNREACH
  else:raise AssertionError('Network egress')
 print('PROOF source/oracleRO emptyhome noenv CapEff0 NoNewPrivs1 ENETUNREACH',flush=True)
 subprocess.run(['/usr/bin/python3','-m','unittest','discover','-s','/oracle' if oracle else 'tests','-v'],check=True,timeout=90,stdin=subprocess.DEVNULL)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--oracle-dir');p.add_argument('--inner',action='store_true');a=p.parse_args()
 if a.inner:inner(bool(a.oracle_dir));return
 before=hashes(ROOT)
 with tempfile.TemporaryDirectory(prefix='locale-check-') as temporary:
  scratch=Path(temporary);source=scratch/'source';copy(ROOT,source);assert hashes(source)==before
  if a.oracle_dir:
   original=Path(a.oracle_dir).resolve(strict=True);frozen=hashes(original);oracle=scratch/'oracle';copy(original,oracle);assert hashes(oracle)==frozen
  command=['bwrap','--unshare-all','--unshare-user','--disable-userns','--cap-drop','ALL','--die-with-parent','--new-session','--clearenv']
  for n in ['usr','bin','sbin','lib','lib64']:
   path=Path('/')/n
   if path.is_symlink():command+=['--symlink',os.readlink(path),'/'+n]
   elif path.exists():command+=['--ro-bind',str(path),str(path)]
  if Path('/etc/ld.so.cache').exists():command+=['--ro-bind','/etc/ld.so.cache','/etc/ld.so.cache']
  command+=['--proc','/proc','--dev','/dev','--size','268435456','--tmpfs','/tmp','--ro-bind',str(source),'/work']
  if a.oracle_dir:command+=['--ro-bind',str(oracle),'/oracle']
  for k,v in {'PATH':'/usr/bin:/bin','HOME':'/tmp','LANG':'C.UTF-8','TMPDIR':'/tmp','PYTHONPATH':'/work/src','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}.items():command+=['--setenv',k,v]
  command+=['--chdir','/work','--','/usr/bin/setpriv','--no-new-privs','/usr/bin/python3','/work/scripts/checks-offline.py','--inner']
  if a.oracle_dir:command+=['--oracle-dir','/oracle']
  result=subprocess.run(command,env={'PATH':'/usr/bin:/bin'},timeout=120,stdin=subprocess.DEVNULL)
  assert hashes(source)==before and hashes(ROOT)==before,'Source changed'
  if a.oracle_dir:assert hashes(oracle)==frozen and hashes(original)==frozen,'Oracle changed'
  if result.returncode:raise SystemExit(result.returncode)
 print('Checks passed; source/oracle hashes preserved.')
if __name__=='__main__':main()

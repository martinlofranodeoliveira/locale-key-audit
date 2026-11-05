"""Protected synthetic CLI regressions, independent of engine-author tests."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
MODULE='locale_key_audit'
VALID={'reference': {'hello': 'Hello'}, 'locales': {'pt': {'hello': 'Olá'}}}
INVALID_REPORT={'reference': {'hello': 'Hello'}, 'locales': {'pt': {}}}
class CliTests(unittest.TestCase):
    def cli(self,data=b'',args=()):
        return subprocess.run([sys.executable,'-m',MODULE,*args],input=data,capture_output=True,timeout=10)
    def test_stdin_success_and_findings(self):
        a=self.cli(json.dumps(VALID).encode());self.assertEqual(a.returncode,0);self.assertTrue(json.loads(a.stdout)['valid'])
        a=self.cli(json.dumps(INVALID_REPORT).encode());self.assertEqual(a.returncode,1);self.assertFalse(json.loads(a.stdout)['valid'])
    def test_fixed_invalid_encoding_duplicate_keys_and_arguments(self):
        for data in (b'\xff',b'{',b'NaN',b'{"x":1,"x":2}',b'{}'):
            a=self.cli(data);self.assertEqual(a.returncode,2);self.assertEqual(json.loads(a.stderr),{'error':'INPUT_INVALID'})
        a=self.cli(b'',('--unknown-synthetic-marker',));self.assertEqual(a.returncode,2);self.assertEqual(json.loads(a.stderr),{'error':'ARGUMENTS_INVALID'})
        self.assertNotIn(b'synthetic-marker',a.stderr)
    def test_file_readonly_and_special_files_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);source=p/'synthetic-private-filename.json';raw=json.dumps(VALID).encode();source.write_bytes(raw)
            a=self.cli(args=(str(source),));self.assertEqual(a.returncode,0);self.assertEqual(source.read_bytes(),raw)
            link=p/'link';link.symlink_to(source);fifo=p/'fifo';os.mkfifo(fifo)
            for path in (link,fifo,p,p/'missing'):
                a=self.cli(args=(str(path),));self.assertEqual(a.returncode,2);self.assertEqual(json.loads(a.stderr),{'error':'INPUT_INVALID'});self.assertNotIn(str(path).encode(),a.stderr+a.stdout)
    def test_input_budget(self):
        a=self.cli(b' '*(1048576+1));self.assertEqual(a.returncode,2);self.assertEqual(json.loads(a.stderr),{'error':'INPUT_INVALID'})
if __name__=='__main__':unittest.main()

"""Bounded offline JSON CLI with fixed diagnostics and no input modification."""
import argparse,json,os,stat,sys
from .engine import analyze
MAX_INPUT_BYTES=1048576
def diagnostic(code):
    print(json.dumps({'error':code}),file=sys.stderr)
    return 2
class Parser(argparse.ArgumentParser):
    def error(self,message):
        diagnostic('ARGUMENTS_INVALID')
        raise SystemExit(2)
def pairs(items):
    result={}
    for key,value in items:
        if key in result:raise ValueError('INPUT_INVALID')
        result[key]=value
    return result
def nonfinite(value):raise ValueError('INPUT_INVALID')
def main(argv=None):
    parser=Parser(description=__doc__)
    parser.add_argument('path',nargs='?',default='-',help='One regular UTF-8 JSON file, or - for stdin')
    args=parser.parse_args(argv)
    try:
        if args.path=='-':raw=sys.stdin.buffer.read(MAX_INPUT_BYTES+1)
        else:
            descriptor=os.open(args.path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            with os.fdopen(descriptor,'rb') as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):return diagnostic('INPUT_INVALID')
                raw=stream.read(MAX_INPUT_BYTES+1)
        if len(raw)>MAX_INPUT_BYTES:return diagnostic('INPUT_INVALID')
        payload=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=nonfinite)
        report=analyze(payload)
    except (OSError,UnicodeError,ValueError,RecursionError):return diagnostic('INPUT_INVALID')
    except Exception:return diagnostic('VALIDATION_FAILED')
    print(json.dumps(report,ensure_ascii=True,separators=(',',':')))
    return 0 if report['valid'] else 1
if __name__=='__main__':raise SystemExit(main())

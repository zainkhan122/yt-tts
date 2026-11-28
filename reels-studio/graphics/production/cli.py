"""Opt-in CLI for an aligned smartphone battery proof of concept."""
import argparse, json
from pathlib import Path
from .blueprint import bind,battery_specs,validate
from .render import render,frame

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('plan');a.add_argument('--audio',required=True);a.add_argument('--alignment',required=True);a.add_argument('--groups',required=True,help='comma-separated counts of aligned words');a.add_argument('--out',required=True)
    r=sub.add_parser('render');r.add_argument('--audio',required=True);r.add_argument('--blueprint',required=True);r.add_argument('--work',required=True);r.add_argument('--out',required=True);r.add_argument('--cover');r.add_argument('--force-beat',action='append',default=[])
    args=p.parse_args()
    if args.cmd=='plan':
        j=json.loads(Path(args.alignment).read_text());words=j['words'];groups=[int(x) for x in args.groups.split(',')];bp=bind(args.audio,words,groups,battery_specs(words,groups),method=j['method']);Path(args.out).write_text(json.dumps(bp,indent=2)+'\n');print(args.out)
    else:
        bp=json.loads(Path(args.blueprint).read_text());render(bp,args.audio,args.work,args.out,args.cover,args.force_beat);print(args.out)
if __name__=='__main__':main()

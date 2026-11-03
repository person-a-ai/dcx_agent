"""python -m app.importer <zip|csv> [--sid ID]"""
import argparse
import sys

from app.importer import read, steps


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='dcxctl import-labels', description='외부 라벨 결과를 새 프로젝트로 가져옵니다')
    parser.add_argument('path', help='결과 CSV 또는 그것을 담은 zip')
    parser.add_argument('--sid', help='프로젝트 id (기본: imp-<파일 해시>)')
    args = parser.parse_args(argv)
    try:
        steps.run_import(args.path, sid=args.sid, log=lambda line: print(line, flush=True))
    except read.ImportError_ as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('중단했습니다. 같은 명령을 다시 실행하면 이어서 합니다.', file=sys.stderr)
        return 130
    return 0


if __name__ == '__main__':
    sys.exit(main())

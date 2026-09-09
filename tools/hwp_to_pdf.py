# -*- coding: utf-8 -*-
"""Source/ 안의 .hwp 를 같은 자리에 .pdf 로 변환한다.

한컴오피스가 깔려 있어야 한다 (COM 자동화 — 한컴오피스 2020에서 확인).
한글이 직접 PDF로 내보내므로 글자가 벡터로 남고 레이아웃이 그대로다.
LibreOffice 변환처럼 표가 깨지지 않는다.

한글 창을 띄우므로 변환 중에는 한글을 직접 쓰지 않는 게 좋다.

  python tools/hwp_to_pdf.py                       # 미리보기 (변환 안 함)
  python tools/hwp_to_pdf.py --apply
  python tools/hwp_to_pdf.py --apply --path "Source/중1 비상황종배/6과"
  python tools/hwp_to_pdf.py --apply --overwrite   # 이미 있는 pdf도 다시 만듦
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "Source"


def find_targets(base: Path, overwrite: bool):
    todo, done = [], []
    for hwp in sorted(base.rglob("*.hwp")):
        if hwp.name.startswith("~"):  # 한글 임시 파일
            continue
        pdf = hwp.with_suffix(".pdf")
        (todo if overwrite or not pdf.exists() else done).append((hwp, pdf))
    return todo, done


def convert(todo):
    import win32com.client as win32

    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
    # 스크립트가 파일을 열 때 뜨는 보안 확인 창을 막는다. 이게 없으면
    # 파일마다 팝업이 떠서 자동화가 멈춘다.
    hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    try:
        hwp.XHwpWindows.Item(0).Visible = False
    except Exception:
        pass

    ok, failed = [], []
    try:
        for i, (src, dst) in enumerate(todo, 1):
            t0 = time.time()
            print(f"  [{i}/{len(todo)}] {src.name[:60]} ... ", end="", flush=True)
            try:
                if not hwp.Open(str(src), "HWP", "forceopen:true"):
                    raise RuntimeError("열기 실패")
                hwp.SaveAs(str(dst), "PDF")
                size = dst.stat().st_size / 1024
                print(f"{time.time() - t0:.1f}s  {size:.0f}KB")
                ok.append(dst)
            except Exception as e:
                print(f"실패: {e}")
                failed.append((src, e))
            finally:
                try:
                    hwp.Clear(1)  # 1 = 저장하지 않고 문서 닫기
                except Exception:
                    pass
    finally:
        try:
            hwp.Quit()
        except Exception:
            pass
    return ok, failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제로 변환한다")
    ap.add_argument("--path", default=str(SOURCE), help="대상 폴더 (기본: Source/)")
    ap.add_argument("--overwrite", action="store_true", help="이미 있는 pdf도 다시 만듦")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    base = Path(args.path)
    if not base.is_absolute():
        base = ROOT / base
    todo, done = find_targets(base, args.overwrite)

    print(f"■ {base.relative_to(ROOT)}")
    print(f"   변환 대상 {len(todo)}개, 이미 pdf 있음 {len(done)}개")
    if not todo:
        return
    for hwp, _ in todo:
        print("   ·", hwp.relative_to(base))
    if not args.apply:
        print("\n   --apply 를 붙이면 실제로 변환합니다.")
        return

    print("\n한글을 띄웁니다. 변환이 끝날 때까지 한글을 직접 쓰지 마세요.\n")
    ok, failed = convert(todo)
    print(f"\n완료: {len(ok)}개 성공, {len(failed)}개 실패")
    for src, e in failed:
        print("   실패:", src.name, "—", e)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
전자책 PDF 생성기 (CLI)

사용법:
    python make_ebook.py                         # 대화형 입력
    python make_ebook.py -f input.txt            # 파일에서 읽기
    python make_ebook.py -f input.txt -t "제목" -a "저자"
"""

import argparse
import sys
from generator.pdf_maker import generate_ebook


def main():
    parser = argparse.ArgumentParser(description="텍스트를 30페이지 전자책 PDF로 변환")
    parser.add_argument("-f", "--file", help="입력 텍스트 파일 (.txt)")
    parser.add_argument("-t", "--title", default="나의 전자책", help="책 제목")
    parser.add_argument("-a", "--author", default="저자 미상", help="저자 이름")
    parser.add_argument("-o", "--output", default=None, help="출력 PDF 파일명")
    args = parser.parse_args()

    # 텍스트 가져오기
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
        print(f"파일 읽기 완료: {args.file}")
    else:
        print("=" * 50)
        print("  전자책 PDF 생성기")
        print("=" * 50)
        if not args.title or args.title == "나의 전자책":
            args.title = input("\n책 제목: ").strip() or "나의 전자책"
        if not args.author or args.author == "저자 미상":
            args.author = input("저자 이름: ").strip() or "저자 미상"
        print("\n내용을 입력하세요 (입력 끝: 빈 줄에서 Ctrl+D 또는 Ctrl+Z):\n")
        text = sys.stdin.read()

    if not text.strip():
        print("오류: 텍스트가 비어있습니다.")
        sys.exit(1)

    output = args.output or f"{args.title}.pdf"
    print(f"\nPDF 생성 중...")
    generate_ebook(args.title, args.author, text, output)
    print(f"완료! → {output} (30페이지)")


if __name__ == "__main__":
    main()

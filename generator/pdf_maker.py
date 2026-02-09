"""
전자책 PDF 생성 엔진
텍스트를 입력받아 30페이지 분량의 eBook PDF를 생성한다.
"""

import math
import textwrap
from fpdf import FPDF

FONT_DIR = "/usr/share/fonts/opentype/noto"
TARGET_PAGES = 30


class EbookPDF(FPDF):
    """한국어를 지원하는 eBook 전용 PDF 클래스."""

    def __init__(self, title="", author=""):
        super().__init__(format="A5")
        self.book_title = title
        self.book_author = author
        self._setup_fonts()

    def _setup_fonts(self):
        self.add_font("NotoSans", "", f"{FONT_DIR}/NotoSansCJK-Regular.ttc", uni=True)
        self.add_font("NotoSans", "B", f"{FONT_DIR}/NotoSansCJK-Bold.ttc", uni=True)
        self.add_font("NotoSerif", "", f"{FONT_DIR}/NotoSerifCJK-Regular.ttc", uni=True)
        self.add_font("NotoSerif", "B", f"{FONT_DIR}/NotoSerifCJK-Bold.ttc", uni=True)

    # ── header / footer ──────────────────────────────────────────────
    def header(self):
        if self.page_no() <= 2:
            return
        self.set_font("NotoSans", "", 7)
        self.set_text_color(140, 140, 140)
        self.cell(0, 6, self.book_title, align="C")
        self.ln(8)

    def footer(self):
        if self.page_no() <= 2:
            return
        self.set_y(-15)
        self.set_font("NotoSans", "", 7)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, str(self.page_no()), align="C")


def _split_into_chapters(text: str) -> list[dict]:
    """텍스트를 장(chapter) 단위로 분리한다.

    빈 줄 두 개 이상(\n\n\n) 또는 '제N장', '챕터', 'Chapter' 등의
    패턴이 있으면 해당 지점에서 분리한다.  그렇지 않으면 단락 수를
    기준으로 균등 분할한다.
    """
    import re

    # 명시적 챕터 구분이 있으면 사용
    chapter_pattern = re.compile(
        r"\n{2,}(?=제\s*\d+\s*장|챕터\s*\d+|Chapter\s*\d+|CHAPTER\s*\d+|Part\s*\d+)",
        re.IGNORECASE,
    )
    parts = chapter_pattern.split(text.strip())
    if len(parts) >= 3:
        chapters = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            lines = p.split("\n", 1)
            title = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else ""
            chapters.append({"title": title, "body": body})
        return chapters

    # 명시적 구분이 없으면 단락 기준 균등 분할
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text.strip()) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    num_chapters = min(max(3, len(paragraphs) // 3), 10)
    chunk_size = math.ceil(len(paragraphs) / num_chapters)

    chapters = []
    for i in range(num_chapters):
        chunk = paragraphs[i * chunk_size : (i + 1) * chunk_size]
        if not chunk:
            continue
        chapters.append(
            {
                "title": f"제 {i + 1} 장",
                "body": "\n\n".join(chunk),
            }
        )
    return chapters


def _estimate_body_lines(pdf: EbookPDF, text: str, font_size: float) -> int:
    """본문 텍스트가 차지할 대략적 줄 수를 계산한다."""
    pdf.set_font("NotoSerif", "", font_size)
    usable_w = pdf.w - pdf.l_margin - pdf.r_margin
    char_w = pdf.get_string_width("가") or 3.0
    chars_per_line = max(int(usable_w / char_w), 1)

    total_lines = 0
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            total_lines += 1
            continue
        total_lines += max(1, math.ceil(len(para) / chars_per_line))
        total_lines += 1  # paragraph spacing
    return total_lines


def _calc_font_size_and_spacing(
    pdf: EbookPDF, chapters: list[dict], target_pages: int
) -> tuple[float, float]:
    """목표 페이지에 맞도록 폰트 크기와 줄간격을 계산한다."""
    # A5 usable height ≈ 170mm, header ≈ 8mm, footer ≈ 15mm → ~147mm
    usable_h = 147.0
    # 표지(1) + 저작권(1) + 목차(1) + 마무리(1) = 4페이지
    content_pages = target_pages - 4
    # 각 장 시작에 1/3 페이지 정도 타이틀 공간
    chapter_overhead_pages = len(chapters) * 0.35
    text_pages = content_pages - chapter_overhead_pages

    if text_pages < 3:
        text_pages = 3

    # 폰트 크기 후보별로 줄 수를 계산해 가장 가까운 것을 선택
    best_size = 10.0
    best_leading = 6.5
    best_diff = float("inf")

    for fsize in [8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0]:
        for leading in [5.5, 6.0, 6.5, 7.0, 7.5, 8.0]:
            line_h = fsize * 0.3528 + leading  # pt → mm + leading
            lines_per_page = int(usable_h / line_h)
            total_lines = sum(
                _estimate_body_lines(pdf, ch["body"], fsize) for ch in chapters
            )
            estimated_pages = total_lines / max(lines_per_page, 1)
            diff = abs(estimated_pages - text_pages)
            if diff < best_diff:
                best_diff = diff
                best_size = fsize
                best_leading = leading

    return best_size, best_leading


def generate_ebook(
    title: str,
    author: str,
    text: str,
    output_path: str,
    target_pages: int = TARGET_PAGES,
) -> str:
    """전자책 PDF를 생성하고 파일 경로를 반환한다."""
    pdf = EbookPDF(title=title, author=author)
    pdf.set_auto_page_break(auto=True, margin=20)

    chapters = _split_into_chapters(text)
    font_size, leading = _calc_font_size_and_spacing(pdf, chapters, target_pages)
    line_h = font_size * 0.3528 + leading

    # ── 1. 표지 ──────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("NotoSans", "B", 22)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 12, title, align="C")
    pdf.ln(15)
    pdf.set_font("NotoSans", "", 13)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, author, align="C")
    pdf.ln(30)
    pdf.set_draw_color(200, 200, 200)
    x_center = pdf.w / 2
    pdf.line(x_center - 25, pdf.get_y(), x_center + 25, pdf.get_y())

    # ── 2. 저작권 페이지 ─────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(60)
    pdf.set_font("NotoSans", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 6, f"{title}\n\n저자: {author}\n\n이 책의 저작권은 저자에게 있습니다.", align="C")

    # ── 3. 목차 ──────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(10)
    pdf.set_font("NotoSans", "B", 16)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, "목  차", align="C")
    pdf.ln(15)
    pdf.set_font("NotoSans", "", 10)
    for i, ch in enumerate(chapters):
        label = ch["title"] if len(ch["title"]) < 40 else ch["title"][:37] + "..."
        pdf.cell(0, 8, f"  {label}", ln=True)

    # ── 4. 본문 ──────────────────────────────────────────────────────
    pdf.set_text_color(30, 30, 30)
    for ch in chapters:
        pdf.add_page()
        pdf.ln(8)
        # 장 제목
        pdf.set_font("NotoSans", "B", 15)
        pdf.multi_cell(0, 9, ch["title"], align="L")
        pdf.ln(6)
        # 구분선
        pdf.set_draw_color(200, 200, 200)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(6)
        # 본문
        pdf.set_font("NotoSerif", "", font_size)
        for para in ch["body"].split("\n"):
            para = para.strip()
            if not para:
                pdf.ln(line_h * 0.5)
                continue
            pdf.multi_cell(0, line_h, para)
            pdf.ln(line_h * 0.3)

    # ── 5. 현재 페이지 확인 후 빈 페이지 채우기 ─────────────────────
    while pdf.page_no() < target_pages - 1:
        pdf.add_page()
        pdf.ln(40)
        pdf.set_font("NotoSans", "", 9)
        pdf.set_text_color(180, 180, 180)
        pdf.cell(0, 10, "", align="C")

    # ── 6. 마무리 페이지 ─────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font("NotoSans", "B", 14)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, title, align="C")
    pdf.ln(10)
    pdf.set_font("NotoSans", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"저자: {author}", align="C")
    pdf.ln(20)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(x_center - 25, pdf.get_y(), x_center + 25, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("NotoSans", "", 8)
    pdf.cell(0, 6, "이 전자책은 자동 생성되었습니다.", align="C")

    pdf.output(output_path)
    return output_path

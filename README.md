# ebook-pdf-generator

텍스트를 넣으면 전자책 PDF(30페이지)를 자동 생성하는 심플한 도구

## 실행 방법

```bash
pip install -r requirements.txt
python app.py
```

브라우저에서 `http://localhost:5000` 접속

## 사용법

1. 책 제목과 저자 이름을 입력
2. 텍스트를 직접 입력하거나 파일(.txt, .docx)을 업로드
3. "PDF 전자책 생성" 버튼 클릭
4. 30페이지 PDF가 자동 다운로드

## 기능

- 한국어 완벽 지원 (Noto Sans/Serif CJK)
- 텍스트 직접 입력 또는 파일 업로드 (.txt, .docx)
- 자동 챕터 분리 (빈 줄 또는 "제N장" 패턴 감지)
- 표지, 목차, 본문, 마무리 페이지 자동 구성
- 30페이지에 맞춰 폰트 크기/간격 자동 조절

## 요구사항

- Python 3.10+
- Noto CJK 폰트 (`apt install fonts-noto-cjk`)

import streamlit as st
import os
import zipfile
import tempfile
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

st.set_page_title="만화 EPUB 변환기", page_icon="📚")

st.title("📚 만화/이미지 HTML -> EPUB 변환기")
st.markdown("정리된 `.png.html` 파일들을 업로드하면 오닉스 북스 등에서 읽기 좋은 EPUB 파일로 변환해 줍니다.")

# 파일 업로드 (다중 선택 가능)
uploaded_files = st.file_uploader(
    "변환할 HTML 파일들을 선택하세요 (여러 개 선택 가능)", 
    type=["html", "htm"], 
    accept_multiple_files=True
)

book_title = st.text_input("책 제목 (Title)", value="나의 만화 책")
book_author = st.text_input("저자 (Author)", value="알 수 없음")

if st.button("EPUB 파일 생성하기", type="primary"):
    if not uploaded_files:
        st.warning("변환할 HTML 파일을 하나 이상 업로드해 주세요!")
    else:
        with st.spinner("EPUB 파일을 생성 중입니다... 잠시만 기다려주세요!"):
            # 임시 작업 디렉토리 생성
            with tempfile.TemporaryDirectory() as tmpdirname:
                book = epub.EpubBook()
                
                # 메타데이터 설정
                book.set_identifier('id123456')
                book.set_title(book_title)
                book.set_language('ko')
                book.add_author(book_author)
                
                chapters = []
                
                # 업로드된 파일 정렬 (이름 순)
                sorted_files = sorted(uploaded_files, key=lambda x: x.name)
                
                for idx, uploaded_file in enumerate(sorted_files):
                    # 파일 내용 읽기
                    html_content = uploaded_file.read().decode('utf-8', errors='ignore')
                    
                    # 챕터 생성
                    c = epub.EpubHtml(
                        title=f'Chapter {idx+1}', 
                        file_name=f'chap_{idx+1}.xhtml', 
                        lang='ko'
                    )
                    c.content = html_content
                    book.add_item(c)
                    chapters.append(c)
                
                # 목차 및 내비게이션 설정
                book.toc = chapters
                book.add_item(epub.EpubNcx())
                book.add_item(epub.EpubNav())
                
                # CSS 추가 (필요시 스타일 조정)
                style = 'BODY { margin: 0; padding: 0; background-color: black; text-align: center; } img { max-width: 100%; height: auto; }'
                nav_css = epub.EpubItem(
                    uid="style_nav", 
                    file_name="style/nav.css", 
                    media_type="text/css", 
                    content=style
                )
                book.add_item(nav_css)
                
                # 책 순서 정의
                book.spine = ['nav'] + chapters
                
                # EPUB 파일로 저장
                output_epub_path = os.path.join(tmpdirname, "output.epub")
                epub.write_epub(output_epub_path, book, {})
                
                # 파일 읽어서 다운로드 버튼 제공
                with open(output_epub_path, "rb") as f:
                    epub_bytes = f.read()
                
                st.success("EPUB 파일이 성공적으로 생성되었습니다! 🎉")
                st.download_button(
                    label="📥 완성된 EPUB 파일 다운로드",
                    data=epub_bytes,
                    file_name=f"{book_title}.epub",
                    mime="application/epub+zip"
                )

import streamlit as st
import os
import tempfile
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

st.set_page_config(page_title="만화 2단 비교 EPUB 변환기", page_icon="📚")

st.title("📚 만화 2단 비교 HTML -> EPUB 변환기")
st.markdown("PC처럼 **[왼쪽: 만화 이미지 | 오른쪽: 번역 텍스트]** 2단 구조를 오닉스 북스(가로 모드 추천)에서도 그대로 볼 수 있게 변환해 줍니다.")

# 파일 업로드 (다중 선택 가능)
uploaded_files = st.file_uploader(
    "변환할 HTML 파일들을 선택하세요 (여러 개 선택 가능)", 
    type=["html", "htm"], 
    accept_multiple_files=True
)

book_title = st.text_input("책 제목 (Title)", value="Manga_Comparison_Book")
book_author = st.text_input("저자 (Author)", value="Private Lab")

if st.button("2단 레이아웃 EPUB 파일 생성하기", type="primary"):
    if not uploaded_files:
        st.warning("변환할 HTML 파일을 하나 이상 업로드해 주세요!")
    else:
        with st.spinner("2단 구조의 EPUB 전자책을 패키징 중입니다... 잠시만 기다려주세요!"):
            with tempfile.TemporaryDirectory() as tmpdirname:
                book = epub.EpubBook()
                
                # 메타데이터 설정
                book.set_identifier('id_manga_2col')
                book.set_title(book_title)
                book.set_language('ko')
                book.add_author(book_author)
                
                chapters = []
                
                # 업로드된 파일 정렬 (이름 순)
                sorted_files = sorted(uploaded_files, key=lambda x: x.name)
                
                for idx, uploaded_file in enumerate(sorted_files):
                    html_content = uploaded_file.read().decode('utf-8', errors='ignore')
                    
                    # BeautifulSoup으로 기존 HTML 파싱하여 이미지와 텍스트 분리 추출 시도
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    img_tag = soup.find('img')
                    text_div = soup.find('div', class_='text-content') or soup.find('div', class_='translation')
                    
                    # 만약 특정 클래스가 없으면 본문 내용 전체나 body 내용을 텍스트 영역으로 활용
                    if not text_div:
                        # body 내부에서 img를 제외한 나머지 내용을 가져오기
                        body_tag = soup.find('body')
                        if body_tag:
                            for im in body_tag.find_all('img'):
                                im.decompose()
                            extracted_text_html = body_tag.decode_contents()
                        else:
                            extracted_text_html = html_content
                    else:
                        extracted_text_html = text_div.decode_contents()
                        
                    img_src = img_tag['src'] if img_tag else ""
                    
                    # 각 페이지별 XHTML 챕터 생성 (좌우 2단 Flexbox 구조 적용)
                    c = epub.EpubHtml(
                        title=f'Page {idx+1}: {uploaded_file.name}', 
                        file_name=f'page_{idx+1}.xhtml', 
                        lang='ko'
                    )
                    
                    c.content = f"""
                    <html>
                    <head>
                        <title>{uploaded_file.name}</title>
                        <style>
                            body {{
                                margin: 0;
                                padding: 5px;
                                background-color: #ffffff;
                                color: #000000;
                                font-family: 'Malgun Gothic', sans-serif;
                            }}
                            .spread-container {{
                                display: flex;
                                flex-direction: row;
                                width: 100%;
                                height: 100vh;
                                box-sizing: border-box;
                                align-items: stretch;
                            }}
                            .image-pane {{
                                flex: 1;
                                text-align: center;
                                padding-right: 10px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                            }}
                            .image-pane img {{
                                max-width: 100%;
                                max-height: 95vh;
                                object-fit: contain;
                                border: 1px solid #ddd;
                            }}
                            .text-pane {{
                                flex: 1;
                                padding-left: 10px;
                                overflow-y: auto;
                                font-size: 13px;
                                line-height: 1.5;
                                text-align: left;
                                white-space: pre-wrap;
                                background: #fcfcfc;
                                border-left: 1px solid #ccc;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="spread-container">
                            <div class="image-pane">
                                <img src="{img_src}" alt="Manga Image"/>
                            </div>
                            <div class="text-pane">
                                {extracted_text_html}
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    book.add_item(c)
                    chapters.append(c)
                
                # 목차 및 내비게이션 설정
                book.toc = chapters
                book.add_item(epub.EpubNcx())
                book.add_item(epub.EpubNav())
                
                # 기본 내비게이션 스타일시트 추가
                style = 'BODY { font-family: sans-serif; }'
                nav_css = epub.EpubItem(
                    uid="style_nav", 
                    file_name="style/nav.css", 
                    media_type="text/css", 
                    content=style
                )
                book.add_item(nav_css)
                
                # 책 순서 정의
                book.spine = ['nav'] + chapters
                
                # EPUB 저장
                output_epub_path = os.path.join(tmpdirname, "output.epub")
                epub.write_epub(output_epub_path, book, {})
                
                with open(output_epub_path, "rb") as f:
                    epub_bytes = f.read()
                
                st.success("✨ 2단 레이아웃 EPUB 파일 변환 완료!")
                st.download_button(
                    label="📥 2단 비교 EPUB 파일 다운로드",
                    data=epub_bytes,
                    file_name=f"{book_title}.epub",
                    mime="application/epub+zip"
                )

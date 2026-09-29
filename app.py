import streamlit as st
import os
import re
import tempfile
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

st.set_page_config(page_title="만화 2단 비교 EPUB 변환기", page_icon="📚")

st.title("📚 만화 2단 비교 HTML -> EPUB 변환기 (1:1 비율 및 스크롤 고정형)")
st.markdown("오닉스 북스에서도 **왼쪽 이미지와 오른쪽 텍스트를 정확히 1:1 비율**로 맞추고, 긴 텍스트는 **오른쪽 내부 스크롤**을 통해 원본 HTML처럼 쾌적하게 비교 분석할 수 있도록 개선되었습니다.")

# 파일 업로드 (다중 선택 가능)
uploaded_files = st.file_uploader(
    "변환할 HTML 파일들을 선택하세요 (여러 개 선택 가능)", 
    type=["html", "htm"], 
    accept_multiple_files=True
)

book_title = st.text_input("책 제목 (Title)", value="Manga_Comparison_Book")
book_author = st.text_input("저자 (Author)", value="Private Lab")

def natural_sort_key(file):
    """파일 이름 속 숫자를 정확히 인식하여 1, 2, ..., 10 순으로 정렬하는 함수"""
    filename = file.name
    numbers = re.findall(r'\d+', filename)
    return [int(n) for n in numbers] if numbers else [filename]

if st.button("1:1 스크롤 고정형 EPUB 생성하기", type="primary"):
    if not uploaded_files:
        st.warning("변환할 HTML 파일을 하나 이상 업로드해 주세요!")
    else:
        with st.spinner("1:1 비율 및 스크롤 구조로 패키징 중입니다... 잠시만 기다려주세요!"):
            with tempfile.TemporaryDirectory() as tmpdirname:
                book = epub.EpubBook()
                
                # 메타데이터 설정
                book.set_identifier('id_manga_scroll_1to1')
                book.set_title(book_title)
                book.set_language('ko')
                book.add_author(book_author)
                
                chapters = []
                
                # 자연스러운 정렬 적용 (1, 2, ..., 10순)
                sorted_files = sorted(uploaded_files, key=natural_sort_key)
                
                for idx, uploaded_file in enumerate(sorted_files):
                    html_content = uploaded_file.read().decode('utf-8', errors='ignore')
                    
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    img_tag = soup.find('img')
                    text_div = soup.find('div', class_='text-content') or soup.find('div', class_='translation')
                    
                    if not text_div:
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
                    
                    c = epub.EpubHtml(
                        title=f'Page {idx+1}: {uploaded_file.name}', 
                        file_name=f'page_{idx+1}.xhtml', 
                        lang='ko'
                    )
                    
                    # 💡 핵심 개선: 1:1 비율 강제 및 오른쪽 영역 스크롤바 부여 CSS 디자인
                    c.content = f"""
                    <html>
                    <head>
                        <title>{uploaded_file.name}</title>
                        <style>
                            html, body {{
                                margin: 0;
                                padding: 0;
                                width: 100%;
                                height: 100%;
                                background-color: #ffffff;
                                color: #000000;
                                font-family: 'Malgun Gothic', sans-serif;
                                overflow: hidden;
                            }}
                            .spread-table {{
                                width: 100%;
                                height: 100%;
                                border-collapse: collapse;
                                table-layout: fixed;
                            }}
                            td.image-cell {{
                                width: 50%;
                                height: 100%;
                                text-align: center;
                                vertical-align: middle;
                                padding: 10px;
                                box-sizing: border-box;
                            }}
                            td.image-cell img {{
                                max-width: 100%;
                                max-height: 98vh;
                                width: auto;
                                height: auto;
                                object-fit: contain;
                                border: 1px solid #ddd;
                                display: block;
                                margin: 0 auto;
                            }}
                            td.text-cell {{
                                width: 50%;
                                height: 100%;
                                vertical-align: top;
                                padding: 15px;
                                box-sizing: border-box;
                                overflow-y: auto; /* 💡 핵심: 텍스트가 길면 오른쪽 영역 안에서만 스크롤바 작동 */
                                font-size: 13px;
                                line-height: 1.5;
                                text-align: left;
                                white-space: pre-wrap;
                                background: #fdfdfd;
                                border-left: 1px solid #ccc;
                            }}
                        </style>
                    </head>
                    <body>
                        <table class="spread-table">
                            <tr>
                                <td class="image-cell">
                                    <img src="{img_src}" alt="Manga Image"/>
                                </td>
                                <td class="text-cell">
                                    {extracted_text_html}
                                </td>
                            </tr>
                        </table>
                    </body>
                    </html>
                    """
                    
                    book.add_item(c)
                    chapters.append(c)
                
                # 목차 및 내비게이션 설정
                book.toc = chapters
                book.add_item(epub.EpubNcx())
                book.add_item(epub.EpubNav())
                
                style = 'BODY { font-family: sans-serif; }'
                nav_css = epub.EpubItem(
                    uid="style_nav", 
                    file_name="style/nav.css", 
                    media_type="text/css", 
                    content=style
                )
                book.add_item(nav_css)
                
                book.spine = ['nav'] + chapters
                
                output_epub_path = os.path.join(tmpdirname, "output.epub")
                epub.write_epub(output_epub_path, book, {})
                
                with open(output_epub_path, "rb") as f:
                    epub_bytes = f.read()
                
                st.success("✨ 1:1 비율 및 스크롤 고정형 EPUB 변환 완료!")
                st.download_button(
                    label="📥 1:1 스크롤 고정형 EPUB 다운로드",
                    data=epub_bytes,
                    file_name=f"{book_title}.epub",
                    mime="application/epub+zip"
                )

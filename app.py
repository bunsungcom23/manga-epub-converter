import streamlit as st
import os
import re
import tempfile
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

st.set_page_config(page_title="만화 가로모드 2단 비교 EPUB 변환기", page_icon="📚")

st.title("📚 만화 가로모드 2단 비교 HTML -> EPUB 변환기")
st.markdown("오닉스 북스 **가로모드**에 최적화하여 **[왼쪽: 만화 이미지 | 오른쪽: 번역 텍스트]**가 1:1 비율로 깔끔하게 배치되도록 만든 버전입니다.")

# 파일 업로드 (다중 선택 가능)
uploaded_files = st.file_uploader(
    "변환할 HTML 파일들을 선택하세요 (여러 개 선택 가능)", 
    type=["html", "htm"], 
    accept_multiple_files=True
)

book_title = st.text_input("책 제목 (Title)", value="Manga_Landscape_Comparison")
book_author = st.text_input("저자 (Author)", value="Private Lab")

def natural_sort_key(file):
    """파일 이름 속 숫자를 정확히 인식하여 1, 2, ..., 10 순으로 정렬하는 함수"""
    filename = file.name
    numbers = re.findall(r'\d+', filename)
    return [int(n) for n in numbers] if numbers else [filename]

if st.button("가로모드 2단 EPUB 생성하기", type="primary"):
    if not uploaded_files:
        st.warning("변환할 HTML 파일을 하나 이상 업로드해 주세요!")
    else:
        with st.spinner("가로모드 최적화 및 2단 구조로 패키징 중입니다... 잠시만 기다려주세요!"):
            with tempfile.TemporaryDirectory() as tmpdirname:
                book = epub.EpubBook()
                
                # 메타데이터 설정
                book.set_identifier('id_manga_landscape_2col')
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
                    
                    # 💡 가로모드 전용 최적화 CSS (이미지 찌그러짐 방지 및 가독성 좋은 폰트 크기 고정)
                    c.content = f"""
                    <html>
                    <head>
                        <title>{uploaded_file.name}</title>
                        <style>
                            @page {{
                                size: landscape;
                                margin: 5pt;
                            }}
                            body {{
                                margin: 0;
                                padding: 0;
                                background-color: #ffffff;
                                color: #000000;
                                font-family: 'Malgun Gothic', sans-serif;
                            }}
                            .landscape-table {{
                                width: 100%;
                                border-collapse: collapse;
                                table-layout: fixed;
                            }}
                            td.img-col {{
                                width: 50%;
                                text-align: center;
                                vertical-align: middle;
                                padding: 5px;
                            }}
                            td.img-col img {{
                                max-width: 100%;
                                max-height: 88vh;
                                width: auto;
                                height: auto;
                                object-fit: contain;
                                border: 1px solid #e0e0e0;
                                display: block;
                                margin: 0 auto;
                            }}
                            td.text-col {{
                                width: 50%;
                                text-align: left;
                                vertical-align: top;
                                padding: 10px;
                                font-size: 12px;
                                line-height: 1.4;
                                white-space: pre-wrap;
                                background: #fafafa;
                                border-left: 1px solid #d0d0d0;
                            }}
                        </style>
                    </head>
                    <body>
                        <table class="landscape-table">
                            <tr>
                                <td class="img-col">
                                    <img src="{img_src}" alt="Manga Image"/>
                                </td>
                                <td class="text-col">
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
                
                st.success("✨ 가로모드 최적화 EPUB 변환 완료!")
                st.download_button(
                    label="📥 가로모드용 EPUB 파일 다운로드",
                    data=epub_bytes,
                    file_name=f"{book_title}.epub",
                    mime="application/epub+zip"
                )

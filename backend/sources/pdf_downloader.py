"""
PDF Downloader & Text Extraction Engine
Downloads open access PDFs and extracts clean text for deep reading analysis.
"""
import io
import httpx
from PyPDF2 import PdfReader
from typing import Optional


class PDFDownloader:
    def __init__(self):
        self.headers = {
            "User-Agent": "QORA Research AI (research@qora.ai)"
        }

    async def download_and_extract_text(self, pdf_url: str, max_pages: int = 15) -> Optional[str]:
        """Downloads a PDF from a URL and extracts up to max_pages of plain text."""
        if not pdf_url or not pdf_url.startswith("http"):
            return None

        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=self.headers) as client:
                response = await client.get(pdf_url)
                if response.status_code != 200:
                    print(f"[PDFDownloader] HTTP error {response.status_code} for {pdf_url}")
                    return None

                pdf_bytes = io.BytesIO(response.content)
                reader = PdfReader(pdf_bytes)

                extracted_text = []
                num_pages = min(len(reader.pages), max_pages)

                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        extracted_text.append(text)

                full_text = "\n\n".join(extracted_text).strip()
                return full_text if full_text else None

        except Exception as e:
            print(f"[PDFDownloader] Failed to process {pdf_url}: {e}")
            return None

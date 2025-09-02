import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader

class PDFToTextConverter:
    def __init__(self, api_key:str):
        self.api_key = api_key
        self.parser = LlamaParse(
            api_key = api_key,
            result_type="text",
            verbose=True,
            language='ko'
        )

    async def convert_pdf_to_text(self, pdf_path: str, output_path: str = None) -> str:
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다.")
            
            print("PDF Parsing")

            documents = await self.parser.aload_data(pdf_path)

            extracted_text = ""
            for doc in documents:
                extracted_text += doc.text + "\n\n"
            
            if output_path is None:
                pdf_name = Path(pdf_path).stem
                output_path = f"{pdf_name}_extracted.txt"

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)

            return extracted_text
        
        except Exception as e:
            print("오류 발생")
            raise e
        
    async def convert_multiple_pdfs(self, pdf_directory: str, output_directory: str = None):
        try:
            pdf_dir = Path(pdf_directory)
            if not pdf_dir.exists():
                raise FileNotFoundError(f"폴더를 찾을 수 없습니다")
            
            if output_directory is None:
                output_directory = pdf_dir / "extracted_texts"
            
            output_dir = Path(output_directory)
            output_dir.mkdir(exist_ok=True)

            pdf_files = list(pdf_dir.glob("*.pdf"))
            if not pdf_files:
                print("PDF 파일이 없습니다.")
                return
            
            for pdf_file in pdf_files:
                output_file = output_dir / f"{pdf_file.stem}_extracted.txt"
                await self.convert_pdf_to_text(str(pdf_file), str(output_file))

            print(f"모든 PDF 변환 완료. 출력 폴더: {output_directory}")
        except Exception as e:
            raise e
        
    def convert_pdf_sync(self, pdf_path: str, output_path: str = None) -> str:
        """
        동기 방식으로 PDF를 텍스트로 변환 (간편 사용)
        
        Args:
            pdf_path (str): PDF 파일 경로
            output_path (str, optional): 출력 텍스트 파일 경로
            
        Returns:
            str: 추출된 텍스트
        """
        return asyncio.run(self.convert_pdf_to_text(pdf_path, output_path))
    
    def convert_multiple_pdfs_sync(self, pdf_directory: str, output_directory: str = None):
        """
        동기 방식으로 여러 PDF를 텍스트로 변환 (간편 사용)
        
        Args:
            pdf_directory (str): PDF 파일들이 있는 폴더 경로
            output_directory (str, optional): 출력 폴더 경로
        """
        asyncio.run(self.convert_multiple_pdfs(pdf_directory, output_directory))

async def main(pdf_path:str):
    load_dotenv()
    api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    converter = PDFToTextConverter(api_key)
    
    # 예제 1: 단일 PDF 파일 변환
    if os.path.exists(pdf_path):
        print("=== 단일 PDF 파일 변환 ===")
        text = await converter.convert_pdf_to_text(pdf_path)
        
        print(f"추출된 텍스트 미리보기:\n{text[:500]}...")
    
if __name__ == "__main__":
    pdf_path = "/Users/hansol/llm/LLM/data/pdf/대학생을 위한 실용금융(제3판 교재)_책갈피F.pdf"
    asyncio.run(main(pdf_path=pdf_path))
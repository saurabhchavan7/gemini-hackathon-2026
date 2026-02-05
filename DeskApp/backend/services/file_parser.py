

import os
from typing import List, Dict, Optional
from datetime import datetime
from llama_index.readers.file import PDFReader, DocxReader
from llama_index.core.text_splitter import SentenceSplitter


from google import genai
from core.config import settings
from services.cache_service import CacheService

cache = CacheService()

class FileParser:

    @staticmethod
    def extract_text(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            reader = PDFReader()
            docs = reader.load_data(file_path)
        elif ext == '.docx':
            reader = DocxReader()
            docs = reader.load_data(file_path)
        else:
            raise ValueError('Unsupported file type')
        text = '\n'.join([doc.text for doc in docs])
        return text



    @staticmethod
    def semantic_chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return splitter.split_text(text)


    @staticmethod

    def extract_title_llm(text: str) -> str:
        """
        Use Gemini to generate a document title from context.
        """
        prompt = (
            "You are a document assistant. Given the following text, generate a concise, informative title for the document. "
            "Return only the title, no extra commentary.\n\nText:\n" + text
        )
        cache_key = ("title:" + text).encode('utf-8')
        cached = cache.get(cache_key)
        if cached:
            return cached
        import google.generativeai as genai
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel(settings.COGNITION_MODEL)
        response = model.generate_content(prompt)
        title = response.text.strip().splitlines()[0]
        cache.set(cache_key, title)
        return title

    @staticmethod

    def extract_summary_llm(text: str) -> str:
        """
        Use Gemini to summarize the document or context.
        """
        prompt = (
            "You are a document assistant. Given the following text, write a concise summary (2-3 sentences) of the document. "
            "Return only the summary, no extra commentary.\n\nText:\n" + text
        )
        cache_key = ("summary:" + text).encode('utf-8')
        cached = cache.get(cache_key)
        if cached:
            return cached
        import google.generativeai as genai
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel(settings.COGNITION_MODEL)
        response = model.generate_content(prompt)
        summary = response.text.strip()
        cache.set(cache_key, summary)
        return summary
    
    
    @staticmethod
    def classify_domain_llm(title: str, summary: str) -> str:
        """
        Use Gemini to classify the document into one of 12 life domains.
        """
        domain_list = [
            "work_career", "education_learning", "money_finance", "home_daily_life", "health_wellbeing", "family_relationships",
            "travel_movement", "shopping_consumption", "entertainment_leisure", "social_community", "admin_documents", "ideas_thoughts"
        ]
        prompt = (
            "You are a document classifier. Given the title and summary, select ONE best-fit domain from this list: "
            f"{', '.join(domain_list)}.\n\n"
            f"Title: {title}\nSummary: {summary}\n"
            "Return ONLY the domain string, no extra commentary."
        )
        cache_key = ("domain:" + title + summary).encode('utf-8')
        cached = cache.get(cache_key)
        if cached:
            return cached
        import google.generativeai as genai
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel(settings.COGNITION_MODEL)
        response = model.generate_content(prompt)
        domain = response.text.strip().split()[0]
        if domain not in domain_list:
            domain = "Unknown"  # fallback
        cache.set(cache_key, domain)
        return domain

    @staticmethod
    def parse_and_chunk(file_path: str) -> Dict:
        text = FileParser.extract_text(file_path)
        chunks = FileParser.semantic_chunk_text(text)
        # Use first 2 chunks for title context
        title_context = ' '.join(chunks[:2])
        title = FileParser.extract_title_llm(title_context)
        # Use whole text or first 4 chunks for summary context
        summary_context = ' '.join(chunks[:4])
        summary = FileParser.extract_summary_llm(summary_context)
        domain = FileParser.classify_domain_llm(title, summary)
        file_name = os.path.basename(file_path)
        upload_date = datetime.utcnow().isoformat()
        return {
            'file_name': file_name,
            'upload_date': upload_date,
            'title': title,
            'summary': summary,
            'domain': domain,
            'chunks': chunks,
            'text': text
        }

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'  # Add this at the very top
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import logging
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
from tenacity import retry, stop_after_attempt, wait_exponential

# Langchain imports
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    UnstructuredURLLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader
)
from langchain_community.vectorstores import FAISS
from google.genai import genai


@dataclass
class DocumentProcessorConfig:
    """Configuration for document processing"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    separators: List[str] = ('\n\n', '\n', '.', ',')
    similarity_threshold: float = 0.5

class RAGProcessor:
    def __init__(self, config: Optional[DocumentProcessorConfig] = None):
        """ Initializes the RAGProcessor with  configuration."""
        self.config = config or DocumentProcessorConfig()
        self.__setup_logging()


    def __setup_logging(self):
        """Setup up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
        )

        # Suppress faise and other verbose logs
        logging.getLogger("faiss").setLevel(logging.WARNING)
        logging.getLogger("langchain").setLevel(logging.WARNING)
        logging.getLogger("google.genai").setLevel(logging.WARNING)
        logging.getLogger('pikepdf._core').setLevel(logging.WARNING)
        logging.getLogger('oauth2client').setLevel(logging.WARNING)
        logging.getLogger('googleapiclient').setLevel(logging.WARNING)
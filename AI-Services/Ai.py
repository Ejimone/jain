import os
import json
from typing import Any, Dict, List, Optional
from langchain_community.tools.load import load_tools
from langchain.agents import AgentType, initialise_agent
from langchain.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import google.generativeai as genai
import logging
from langchain.memory import ConversationBufferMemory
from datetime import datetime
import uuid
from Rag import RagProcessor
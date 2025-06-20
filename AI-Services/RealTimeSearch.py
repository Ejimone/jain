import os
import json
import logging
import requests
import asyncio
from datetime import datetime, timedelta
import  pytz
from typing import Any, Dict, List, Optional
from cachetools import TTLCache
from langchain.agents import AgentType, initialise_agent
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAI


# this is for when a user wants a realtime update on a topic, because since this is a student based app, realtime updates are crucial for studying, 
class RealTimeSearch:
    
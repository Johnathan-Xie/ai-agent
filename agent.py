import os
from mistralai import Mistral
import discord
import urllib, urllib.request
import json
import xml.etree.ElementTree as ET

MISTRAL_MODEL = "mistral-large-latest"
QUERYING_SYSTEM_PROMPT = "You are an arxiv assistant. Use the api details below to fetch information necessary for answering the user's prompt."
SEARCH_QUERY_INFORMATION = "search_query_information.txt"
MAX_MESSAGE_CHARACTERS = 2000
with open(SEARCH_QUERY_INFORMATION) as f:
    QUERYING_SYSTEM_PROMPT = QUERYING_SYSTEM_PROMPT + f.read()

EXTRACTION_PROMPT = """
You are an AI assistant that extracts key information from user queries to perform arXiv searches.
You need to extract the following details:
1. Paper ID (if the user provides a specific arXiv ID)
2. Paper Title (if the user provides a full paper title)
3. Author Name (if the user is looking for papers by a specific author)
4. Keywords (if the user is searching for papers on a general topic)
5. Latest Papers (if the user wants recent publications)

Return the output in JSON format. Example:
{
  "type": "keywords",   // "paper_id", "author", "title", "latest"
  "value": "machine learning"
}
"""

class QueryingMistralAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

        self.client = Mistral(api_key=MISTRAL_API_KEY)

    async def run(self, messages):
        # The simplest form of an agent
        # Send the message's content to Mistral's API and return Mistral's response
        messages = [{"role": "system", "content": QUERYING_SYSTEM_PROMPT},] + messages

        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )
        message_response = response.choices[0].message.content

        queries = [i.strip() for i in message_response.split("\n")]
        information = ""
        for url in queries:
            try:
                fetched_information = urllib.request.urlopen(url).read().decode("utf-8")
                information += fetched_information + "\n\n"
            except Exception as e:
                print(f"Invalid query: {e}")

        return information

LINK_FETCHING_PROMPT = """You are an arxiv assistant. Decide whether the user has asked a question that requires you to read a paper and if so output the link with no other text like: "https://arxiv.org/pdf/2409.19817" If you do not need to fetch a paper, just write "None\""""

class LinkFetchingAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

        self.client = Mistral(api_key=MISTRAL_API_KEY)

    async def run(self, messages):
        # The simplest form of an agent
        # Send the message's content to Mistral's API and return Mistral's response
        messages = [{"role": "system", "content": LINK_FETCHING_PROMPT},] + messages

        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )
        message_response = response.choices[0].message.content
        
        link = message_response.split("\n")[0].strip()
        if link.split("://")[0] == "http":
            link = link.replace("http", "https")
        if link[-1] == ".":
            link = link[:-1]
        if link.lower() == "none" or link.lower() == "none.":
            return ""
        try:
            link_fetching_response = self.client.ocr.process(model="mistral-ocr-latest", document={
                "document_url": link,
                "type": "document_url",
            })
        except Exception as e:
            print(e)
            return ""
        content = "\n\n".join([i.markdown for i in link_fetching_response.pages])
        
        return content

ANSWERING_SYSTEM_PROMPT = f"You are an arxiv assistant. Please answer the user's question or complete the specified task. Ensure your response is less than {MAX_MESSAGE_CHARACTERS} characters"

class AnsweringMistralAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

        self.client = Mistral(api_key=MISTRAL_API_KEY)

    async def run(self, messages: discord.Message):
        # The simplest form of an agent
        # Send the message's content to Mistral's API and return Mistral's response
        messages = [{"role": "system", "content": ANSWERING_SYSTEM_PROMPT},] + messages

        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )
        message_response = response.choices[0].message.content[:MAX_MESSAGE_CHARACTERS]

        return message_response

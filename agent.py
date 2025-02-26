import os
from mistralai import Mistral
import discord
import urllib, urllib.request

MISTRAL_MODEL = "mistral-large-latest"
QUERYING_SYSTEM_PROMPT = "You are an arxiv assistant. Use the api details below to fetch information necessary for answering the user's prompt."
SEARCH_QUERY_INFORMATION = "search_query_information.txt"
MAX_MESSAGE_CHARACTERS = 2000
with open(SEARCH_QUERY_INFORMATION) as f:
    QUERYING_SYSTEM_PROMPT = QUERYING_SYSTEM_PROMPT + f.read()

class QueryingMistralAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

        self.client = Mistral(api_key=MISTRAL_API_KEY)

    async def run(self, message: discord.Message):
        # The simplest form of an agent
        # Send the message's content to Mistral's API and return Mistral's response

        messages = [
            {"role": "system", "content": QUERYING_SYSTEM_PROMPT},
            {"role": "user", "content": message.content},
        ]

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
            except Exception as e:
                print(f"Invalid query: {e}")
            information += fetched_information + "\n\n"

        return information

ANSWERING_SYSTEM_PROMPT = f"You are an arxiv assistant. Please answer the user's question or complete the specified task. Ensure your response is less than {MAX_MESSAGE_CHARACTERS} characters"

class AnsweringMistralAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

        self.client = Mistral(api_key=MISTRAL_API_KEY)

    async def run(self, message: discord.Message):
        # The simplest form of an agent
        # Send the message's content to Mistral's API and return Mistral's response

        messages = [
            {"role": "system", "content": ANSWERING_SYSTEM_PROMPT},
            {"role": "user", "content": message.content},
        ]

        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )
        message_response = response.choices[0].message.content[:MAX_MESSAGE_CHARACTERS]

        return message_response

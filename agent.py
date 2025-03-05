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

"""
class QueryingMistralAgent:
    def __init__(self):
        self.base_url = "https://export.arxiv.org/api/query?"
        self.mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

    async def run(self, message):
        user_query = message.content.strip()

        # 1️⃣ 让 Mistral 解析用户输入，提取查询类型
        messages = [
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": user_query},
        ]
        response = await self.mistral_client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )
        extraction_result = response.choices[0].message.content

        # 2️⃣ 解析 Mistral 返回的 JSON 数据
        import json
        try:
            query_data = json.loads(extraction_result)
        except json.JSONDecodeError:
            return "Sorry, I couldn't understand your query. Please try a more structured input like 'Find papers by John Doe' or 'Latest papers on AI'."

        # 3️⃣ 根据查询类型构造 arXiv API URL
        query_type = query_data.get("type")
        query_value = query_data.get("value")

        if query_type == "paper_id":
            url = f"{self.base_url}id_list={query_value}"
        elif query_type == "author":
            encoded_author = urllib.parse.quote(f'au:"{query_value}"')
            url = f"{self.base_url}search_query={encoded_author}&sortBy=submittedDate&sortOrder=descending&max_results=10"
        elif query_type == "title":
            encoded_title = urllib.parse.quote(f'ti:"{query_value}"')
            url = f"{self.base_url}search_query={encoded_title}&sortBy=submittedDate&sortOrder=descending&max_results=5"
        elif query_type == "keywords" or query_type == "latest":
            encoded_keywords = urllib.parse.quote(f'all:"{query_value}"')
            url = f"{self.base_url}search_query={encoded_keywords}&sortBy=submittedDate&sortOrder=descending&max_results=10"
        else:
            return "I couldn't determine the search type. Please try again."

        # 4️⃣ 调用 arXiv API 查询
        try:
            response = urllib.request.urlopen(url).read().decode("utf-8")
        except Exception as e:
            return f"Query failed: {e}"

        return self.parse_arxiv_response(response)

    def parse_arxiv_response(self, xml_response):
        Parses XML response from arXiv and formats the output.
        root = ET.fromstring(xml_response)
        papers = []

        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title").text
            author = entry.find("{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name").text
            link = entry.find("{http://www.w3.org/2005/Atom}id").text
            summary = entry.find("{http://www.w3.org/2005/Atom}summary").text
            published_date = entry.find("{http://www.w3.org/2005/Atom}published").text

            paper_data = f"📜 **{title}**\n👤 {author}\n📅 {published_date[:10]}\n🔗 [arXiv Paper]({link})\n📄 {summary[:200]}..."
            papers.append(paper_data)

        return "\n\n".join(papers) if papers else "No relevant papers found."
"""

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

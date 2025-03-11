import os
import discord
import logging

from discord.ext import commands
from dotenv import load_dotenv
from agent import QueryingMistralAgent, AnsweringMistralAgent, LinkFetchingAgent
from copy import deepcopy

PREFIX = "!"

# Setup logging
logger = logging.getLogger("discord")

# Load the environment variables
load_dotenv()

# Create the bot with all intents
# The message content and members intent must be enabled in the Discord Developer Portal for the bot to work.
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Import the Mistral agent from the agent.py file
querying_agent = QueryingMistralAgent()
answering_agent = AnsweringMistralAgent()
link_fetching_agent = LinkFetchingAgent()

# Get the token from the environment variables
token = os.getenv("DISCORD_TOKEN")

# Store user chat history
chat_histories = {}
MAX_CHAT_HISTORY = 10

@bot.event
async def on_ready():
    """
    Called when the client is done preparing the data received from Discord.
    Prints message on terminal when bot successfully connects to discord.

    https://discordpy.readthedocs.io/en/latest/api.html#discord.on_ready
    """
    logger.info(f"{bot.user} has connected to Discord!")

@bot.event
async def on_message(message: discord.Message):
    """
    Called when a message is sent in any channel the bot can see.

    https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message
    """
    # Don't delete this line! It's necessary for the bot to process commands.
    await bot.process_commands(message)

    # Ignore messages from self or other bots to prevent infinite loops.
    if message.author.bot or message.content.startswith("!"):
        return
    user_id = message.author.id
    if chat_histories.get(user_id) is None:
        chat_histories[user_id] = []
    
    # Append new message to chat history
    chat_histories[user_id].append({"role": "user", "content": message.content})
    
    logger.info(f"Processing message from {message.author}: {message.content}")
    # Query agent for initial processing
    # full_agent_question = chat_history_template(user_chat_history)
    logger.info(f"Querying agent answering {chat_histories[user_id]}\n\n")
    querying_response = await querying_agent.run(chat_histories[user_id])
    logger.info(f"Querying agent response {querying_response}\n\n")
    
    chat_histories[user_id][-1]["content"] += "\n\n" + querying_response + f"Use the papers above the answer the question: {message.content}"
    logger.info(f"Link Fetching agent answering {chat_histories[user_id]}\n\n")
    link_fetching_response = await link_fetching_agent.run(chat_histories[user_id])
    logger.info(f"Link Fetching agent response {link_fetching_response}\n\n")
    if len(link_fetching_response) > 0:
        chat_histories[user_id][-1]["content"] += "\n\n" + querying_response + f"Use the full paper shown above to answering the question: {message.content}"
    
    logger.info(f"Answering agent answering {chat_histories[user_id]}\n\n")
    answering_response = await answering_agent.run(chat_histories[user_id])
    logger.info(f"Answering agent response {answering_response}")
    chat_histories[user_id].append({"role": "assistant", "content": answering_response})
    
    # Send response
    await message.reply(answering_response)


# Commands


# This example command is here to show you how to add commands to the bot.
# Run !ping with any number of arguments to see the command in action.
# Feel free to delete this if your project will not need commands.
@bot.command(name="ping", help="Pings the bot.")
async def ping(ctx, *, arg=None):
    if arg is None:
        await ctx.send("Pong!")
    else:
        await ctx.send(f"Pong! Your argument was {arg}")

@bot.command(name="reset", help="Resets the chat history for the user.")
async def reset(ctx):
    user_id = ctx.author.id
    if user_id in chat_histories:
        del chat_histories[user_id]
        await ctx.send("Chat history has been reset.")
    else:
        await ctx.send("No chat history found to reset.")

# Start the bot, connecting it to the gateway
bot.run(token)

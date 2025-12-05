#!/usr/bin/env python3
"""
Seattle-Simulator Discord Bot

A Discord bot that generates satirical posts in the style of Seattle-area subreddits.
Uses Groq (free tier) for LLM generation and PRAW for Reddit data.

Commands:
    !seattleaf <target>  - Generate a satirical post. Target can be:
                           - A subreddit (e.g., "Seattle", "SeattleWA")
                           - A Reddit username (e.g., "u/someone")
    !seattleaf           - Uses default subreddit (r/Seattle)
"""

import os
import random
from typing import Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv
import praw
from groq import Groq

load_dotenv()

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Reddit client (read-only, no auth needed for public data)
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT", "SeattleSimulator/1.0"),
)

# Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

DEFAULT_SUBREDDIT = os.getenv("DEFAULT_SUBREDDIT", "Seattle")


def fetch_subreddit_context(subreddit_name: str, limit: int = 25) -> str:
    """Fetch recent posts and comments from a subreddit for context."""
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = []

        for post in subreddit.hot(limit=limit):
            post_text = f"Title: {post.title}"
            if post.selftext and len(post.selftext) < 500:
                post_text += f"\nBody: {post.selftext[:500]}"

            # Get top comments
            post.comments.replace_more(limit=0)
            top_comments = [c.body for c in post.comments[:3] if len(c.body) < 300]
            if top_comments:
                post_text += f"\nTop comments: {' | '.join(top_comments[:2])}"

            posts.append(post_text)

        return "\n\n---\n\n".join(posts[:15])
    except Exception as e:
        return f"Error fetching subreddit: {e}"


def fetch_user_context(username: str, limit: int = 30) -> str:
    """Fetch recent comments/posts from a user for context."""
    try:
        user = reddit.redditor(username)
        content = []

        for comment in user.comments.new(limit=limit):
            content.append(f"[r/{comment.subreddit}] {comment.body[:300]}")

        for submission in user.submissions.new(limit=10):
            text = f"[r/{submission.subreddit}] Title: {submission.title}"
            if submission.selftext:
                text += f" - {submission.selftext[:200]}"
            content.append(text)

        return "\n\n".join(content[:20])
    except Exception as e:
        return f"Error fetching user: {e}"


def generate_satirical_post(context: str, target_type: str, target_name: str) -> str:
    """Generate a satirical post using Groq's free LLM."""

    if target_type == "subreddit":
        system_prompt = f"""You are a satirical Reddit post generator that parodies r/{target_name}.
Your job is to create a funny, exaggerated post that captures the stereotypical themes,
complaints, and vibes of this subreddit. Be creative and amusing but not mean-spirited.

Common Seattle subreddit themes to riff on:
- Housing costs / rent is too damn high
- Homeless encampments discourse
- "I saw the mountain today" posts
- Tech bro culture
- Passive-aggressive Seattle freeze
- Rain appreciation or complaints
- Traffic on I-5 / 405
- Amazon/Microsoft/tech company drama
- "Moving to Seattle, what should I know?"
- Sunset photos from Kerry Park
- Complaining about California transplants

Generate a realistic-looking Reddit post with a title and body text. Make it funny."""

    else:  # user
        system_prompt = f"""You are a satirical Reddit commenter that parodies user u/{target_name}.
Based on their posting history, create a funny exaggerated comment or post in their style.
Capture their typical topics, tone, and quirks. Be amusing but not cruel."""

    user_prompt = f"""Here's recent content from {'r/' + target_name if target_type == 'subreddit' else 'u/' + target_name}:

{context[:4000]}

Now generate a satirical Reddit post that parodies this style. Include both a title and body."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Fast, free tier friendly
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.9,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating post: {e}"


@bot.event
async def on_ready():
    print(f"Seattle-Simulator ready as {bot.user}")


@bot.command(name="seattleaf")
async def seattleaf(ctx, target: Optional[str] = None):
    """
    Generate a satirical post in the style of a subreddit or user.

    Usage:
        !seattleaf           - Simulate r/Seattle (default)
        !seattleaf SeattleWA - Simulate r/SeattleWA
        !seattleaf u/someone - Simulate user u/someone
    """
    async with ctx.typing():
        if target is None:
            target = DEFAULT_SUBREDDIT

        # Determine if targeting user or subreddit
        if target.startswith("u/"):
            username = target[2:]
            context = fetch_user_context(username)
            result = generate_satirical_post(context, "user", username)
            header = f"**Simulating u/{username}:**"
        else:
            # Treat as subreddit (strip r/ if present)
            subreddit = target.lstrip("r/")
            context = fetch_subreddit_context(subreddit)
            result = generate_satirical_post(context, "subreddit", subreddit)
            header = f"**Simulating r/{subreddit}:**"

        # Discord has 2000 char limit
        if len(result) > 1900:
            result = result[:1900] + "..."

        await ctx.send(f"{header}\n\n{result}")


@bot.command(name="seattlehelp")
async def seattlehelp(ctx):
    """Show help for Seattle-Simulator commands."""
    help_text = """**Seattle-Simulator Commands:**

`!seattleaf` - Generate satirical r/Seattle post
`!seattleaf <subreddit>` - Simulate any subreddit (e.g., `!seattleaf SeattleWA`)
`!seattleaf u/<username>` - Simulate a Reddit user's style

*Powered by Groq + Llama 3.1*"""
    await ctx.send(help_text)


if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not set in .env")
        exit(1)
    bot.run(token)

#!/usr/bin/env python3
"""
Seattle-Simulator Reddit Bot

A Reddit bot that generates satirical posts/comments in the style of Seattle-area subreddits.
Responds to !seattleaf mentions in comments.

Usage:
    !seattleaf              - Generate satirical r/Seattle content
    !seattleaf SeattleWA    - Simulate r/SeattleWA style
    !seattleaf u/someone    - Parody a user's posting style
"""

import os
import re
import time

import praw
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Reddit client (needs full auth for commenting)
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT", "SeattleSimulator/1.0"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Subreddits to monitor for !seattleaf commands
MONITOR_SUBREDDITS = os.getenv("MONITOR_SUBREDDITS", "SeattleWA+circlejerkseattle")
DEFAULT_TARGET = os.getenv("DEFAULT_SUBREDDIT", "Seattle")
BOT_USERNAME = os.getenv("REDDIT_USERNAME", "").lower()


def fetch_subreddit_context(subreddit_name: str, limit: int = 25) -> str:
    """Fetch recent posts and comments from a subreddit for context."""
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = []

        for post in subreddit.hot(limit=limit):
            post_text = f"Title: {post.title}"
            if post.selftext and len(post.selftext) < 500:
                post_text += f"\nBody: {post.selftext[:500]}"

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


def generate_satirical_content(context: str, target_type: str, target_name: str) -> str:
    """Generate satirical content using Groq's free LLM."""

    if target_type == "subreddit":
        system_prompt = f"""You are a satirical Reddit commenter that parodies r/{target_name}.
Create a funny, exaggerated comment capturing stereotypical themes of this subreddit.
Be creative and amusing but not mean-spirited. Keep it to 2-4 sentences.

Common Seattle subreddit themes:
- Housing costs / rent complaints
- Homeless encampment discourse
- "I saw the mountain today" excitement
- Tech bro culture and Amazon/Microsoft
- Passive-aggressive Seattle freeze
- Rain appreciation or complaints
- Traffic on I-5 / 405
- "Moving to Seattle, what should I know?"
- Sunset photos from Kerry Park
- California transplant complaints"""

    else:  # user
        system_prompt = f"""You are a satirical Reddit commenter parodying u/{target_name}.
Based on their posting history, create a funny exaggerated comment in their style.
Capture their typical topics, tone, and quirks. Keep it to 2-4 sentences.
Be amusing but not cruel."""

    user_prompt = f"""Recent content from {'r/' + target_name if target_type == 'subreddit' else 'u/' + target_name}:

{context[:4000]}

Generate a short satirical Reddit comment in this style."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.9,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating content: {e}"


def parse_command(text: str) -> tuple[bool, str | None]:
    """Parse !seattleaf command from comment text. Returns (found, target)."""
    match = re.search(r'!seattleaf(?:\s+(\S+))?', text, re.IGNORECASE)
    if match:
        return True, match.group(1)
    return False, None


def process_comment(comment) -> str | None:
    """Process a comment and generate a reply if it contains !seattleaf."""
    # Don't reply to ourselves
    if comment.author and comment.author.name.lower() == BOT_USERNAME:
        return None

    found, target = parse_command(comment.body)
    if not found:
        return None

    target = target or DEFAULT_TARGET

    # Determine if targeting user or subreddit
    if target.startswith("u/"):
        username = target[2:]
        context = fetch_user_context(username)
        result = generate_satirical_content(context, "user", username)
        header = f"*Simulating u/{username}:*\n\n"
    else:
        subreddit = target.lstrip("r/")
        context = fetch_subreddit_context(subreddit)
        result = generate_satirical_content(context, "subreddit", subreddit)
        header = f"*Simulating r/{subreddit}:*\n\n"

    footer = "\n\n---\n^(Seattle-Simulator | Powered by Llama 3.1)"

    return header + result + footer


def run_stream():
    """Stream comments and respond to !seattleaf commands."""
    print(f"Seattle-Simulator listening on r/{MONITOR_SUBREDDITS}...")
    print(f"Logged in as u/{reddit.user.me()}")

    subreddit = reddit.subreddit(MONITOR_SUBREDDITS)

    for comment in subreddit.stream.comments(skip_existing=True):
        try:
            reply = process_comment(comment)
            if reply:
                print(f"Replying to {comment.author} in r/{comment.subreddit}")
                comment.reply(reply)
                time.sleep(2)  # Rate limit
        except Exception as e:
            print(f"Error processing comment: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_stream()

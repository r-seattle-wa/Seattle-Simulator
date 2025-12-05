#!/usr/bin/env python3
"""
Seattle-Simulator CLI

Command-line interface for generating satirical Seattle subreddit posts.
Use this for manual weekly posts or testing without Discord.

Usage:
    python cli.py                    # Simulate r/Seattle
    python cli.py SeattleWA          # Simulate r/SeattleWA
    python cli.py u/someone          # Simulate a user
    python cli.py Seattle --post     # Generate and post to Reddit (requires auth)
"""

import argparse
import os
import sys

from dotenv import load_dotenv
import praw
from groq import Groq

load_dotenv()

# Reddit client
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT", "SeattleSimulator/1.0"),
    # For posting, these are needed:
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def fetch_subreddit_context(subreddit_name: str, limit: int = 25) -> str:
    """Fetch recent posts and comments from a subreddit."""
    subreddit = reddit.subreddit(subreddit_name)
    posts = []

    for post in subreddit.hot(limit=limit):
        post_text = f"Title: {post.title}"
        if post.selftext and len(post.selftext) < 500:
            post_text += f"\nBody: {post.selftext[:500]}"

        post.comments.replace_more(limit=0)
        top_comments = [c.body for c in post.comments[:3] if len(c.body) < 300]
        if top_comments:
            post_text += f"\nComments: {' | '.join(top_comments[:2])}"

        posts.append(post_text)

    return "\n\n---\n\n".join(posts[:15])


def fetch_user_context(username: str, limit: int = 30) -> str:
    """Fetch recent activity from a user."""
    user = reddit.redditor(username)
    content = []

    for comment in user.comments.new(limit=limit):
        content.append(f"[r/{comment.subreddit}] {comment.body[:300]}")

    for submission in user.submissions.new(limit=10):
        text = f"[r/{submission.subreddit}] {submission.title}"
        if submission.selftext:
            text += f" - {submission.selftext[:200]}"
        content.append(text)

    return "\n\n".join(content[:20])


def generate_post(context: str, target_type: str, target_name: str) -> dict:
    """Generate satirical post with title and body."""

    if target_type == "subreddit":
        system_prompt = f"""You are a satirical Reddit post generator for r/{target_name}.
Create a funny, exaggerated post capturing stereotypical themes of this subreddit.

Seattle subreddit themes: housing costs, homeless discourse, mountain sightings,
tech culture, Seattle freeze, rain, I-5 traffic, Amazon/Microsoft, transplant complaints,
sunset photos, "moving here" questions.

Return EXACTLY in this format:
TITLE: [your title here]
BODY: [your post body here]"""
    else:
        system_prompt = f"""You are a satirical Reddit commenter parodying u/{target_name}.
Based on their history, create a funny exaggerated post in their style.

Return EXACTLY in this format:
TITLE: [your title here]
BODY: [your post body here]"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Recent content:\n\n{context[:4000]}\n\nGenerate a satirical post."},
        ],
        max_tokens=500,
        temperature=0.9,
    )

    text = response.choices[0].message.content

    # Parse title and body
    lines = text.split("\n")
    title = ""
    body_lines = []
    in_body = False

    for line in lines:
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        elif line.startswith("BODY:"):
            body_lines.append(line.replace("BODY:", "").strip())
            in_body = True
        elif in_body:
            body_lines.append(line)

    return {
        "title": title or "Untitled Seattle Post",
        "body": "\n".join(body_lines) or text,
    }


def main():
    parser = argparse.ArgumentParser(description="Seattle-Simulator CLI")
    parser.add_argument("target", nargs="?", default="Seattle", help="Subreddit or u/username")
    parser.add_argument("--post", action="store_true", help="Post to Reddit (requires auth)")
    parser.add_argument("--subreddit", default="circlejerkseattle", help="Target subreddit for posting")
    args = parser.parse_args()

    target = args.target

    if target.startswith("u/"):
        username = target[2:]
        print(f"Fetching u/{username} history...")
        context = fetch_user_context(username)
        target_type = "user"
        target_name = username
    else:
        subreddit = target.lstrip("r/")
        print(f"Fetching r/{subreddit} posts...")
        context = fetch_subreddit_context(subreddit)
        target_type = "subreddit"
        target_name = subreddit

    print("Generating satirical post...")
    post = generate_post(context, target_type, target_name)

    print("\n" + "=" * 60)
    print(f"TITLE: {post['title']}")
    print("=" * 60)
    print(post["body"])
    print("=" * 60)

    if args.post:
        confirm = input(f"\nPost to r/{args.subreddit}? (y/N): ")
        if confirm.lower() == "y":
            try:
                submission = reddit.subreddit(args.subreddit).submit(
                    title=post["title"],
                    selftext=post["body"],
                )
                print(f"Posted! {submission.url}")
            except Exception as e:
                print(f"Error posting: {e}")
        else:
            print("Cancelled.")


if __name__ == "__main__":
    main()

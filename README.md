# Seattle-Simulator

A satirical Reddit post generator that parodies Seattle-area subreddits using LLM.

## Features

- **Discord Bot**: `!seattleaf` command to generate posts on demand
- **CLI**: Manual generation for weekly posts
- **Subreddit targeting**: Simulate any subreddit's style
- **User targeting**: Parody a specific Reddit user's posting style
- **Free LLM**: Uses Groq's free tier (Llama 3.1)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in:
   - **Discord token**: https://discord.com/developers/applications
   - **Reddit API**: https://www.reddit.com/prefs/apps (script type)
   - **Groq API**: https://console.groq.com/keys (free)

## Usage

### Discord Bot
```bash
python bot.py
```

Commands:
- `!seattleaf` - Generate satirical r/Seattle post
- `!seattleaf SeattleWA` - Simulate r/SeattleWA
- `!seattleaf u/someone` - Parody a user's style
- `!seattlehelp` - Show help

### CLI (for manual posts)
```bash
python cli.py                      # Simulate r/Seattle
python cli.py SeattleWA            # Simulate r/SeattleWA
python cli.py u/someone            # Simulate a user
python cli.py Seattle --post       # Generate and post to Reddit
```

## How It Works

1. Fetches recent posts/comments from target subreddit or user via Reddit API
2. Sends context to Llama 3.1 via Groq with Seattle-specific satirical prompts
3. Returns generated post to Discord or stdout

## License

MIT

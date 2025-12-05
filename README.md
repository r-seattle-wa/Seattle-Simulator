# Seattle-Simulator

A Reddit bot that generates satirical posts in the style of Seattle-area subreddits using LLM.

## Features

- **Comment trigger**: Responds to `!seattleaf` commands in monitored subreddits
- **Subreddit simulation**: Parody any subreddit's posting style
- **User simulation**: Parody a specific Reddit user's style
- **CLI mode**: Generate posts manually for weekly shitposting
- **Free LLM**: Uses Groq's free tier (Llama 3.1)

## Commands

In any monitored subreddit, comment:

```
!seattleaf              → Simulate r/Seattle (default)
!seattleaf SeattleWA    → Simulate r/SeattleWA
!seattleaf u/someone    → Parody a user's posting style
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in:
   - **Reddit API**: https://www.reddit.com/prefs/apps (script type)
   - **Groq API**: https://console.groq.com/keys (free)

3. Run the bot:
```bash
python bot.py
```

## CLI Usage

For manual posts without running the stream:

```bash
python cli.py                      # Simulate r/Seattle
python cli.py SeattleWA            # Simulate r/SeattleWA
python cli.py u/someone            # Simulate a user
python cli.py Seattle --post       # Generate and post to Reddit
```

## How It Works

1. Monitors specified subreddits for `!seattleaf` comments
2. Fetches recent posts/comments from target subreddit or user
3. Sends context to Llama 3.1 via Groq with satirical prompts
4. Replies with generated parody content

## License

MIT

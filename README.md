# Seattle-Simulator

A Reddit bot that generates satirical posts in the style of Seattle-area subreddits using LLM.

## Features

- **Comment trigger**: Responds to `!seattleaf` commands in monitored subreddits
- **Subreddit simulation**: Parody any subreddit's posting style
- **User simulation**: Parody a specific Reddit user's style
- **CLI mode**: Generate posts manually
- **Free LLM**: Uses Groq's free tier (Llama 3.1)

## Commands

```
!seattleaf              → Simulate r/Seattle (default)
!seattleaf SeattleWA    → Simulate r/SeattleWA
!seattleaf u/someone    → Parody a user's posting style
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Reddit and Groq API keys
python bot.py
```

## CLI Usage

```bash
python cli.py                   # Simulate r/Seattle
python cli.py SeattleWA         # Simulate r/SeattleWA
python cli.py u/someone         # Simulate a user
python cli.py Seattle --post    # Generate and post to Reddit
```

## License

MIT

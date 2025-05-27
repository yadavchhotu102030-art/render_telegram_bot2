# Telegram Bot Deployment on Render

This repository contains a simple Telegram echo bot that can be deployed to [Render](https://render.com/). The bot will echo back any message sent to it.

## Project Structure

- `bot.py` - The main bot code
- `render.yaml` - Render deployment configuration
- `requirements.txt` - Python dependencies

## Prerequisites

1. A Telegram bot token (created via [@BotFather](https://t.me/BotFather))
2. A [Render](https://render.com/) account
3. Git repository hosting service account (GitHub, GitLab, etc.)

## Deployment Steps

### 1. Create Your Bot on Telegram

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command to BotFather
3. Follow the prompts to name your bot and create a username
4. BotFather will provide you with a token. Save this token for later use

### 2. Prepare Your Repository

1. Fork this repository to your GitHub account:
   - Navigate to the repository URL in your browser
   - Click the "Fork" button in the top-right corner
   - Select your account when prompted

You can customize your bot later as described in the "Customizing Your Bot" section below.

### 3. Deploy to Render

1. Sign in to [Render](https://render.com/)
2. From the dashboard, click "New" and select "Blueprint"
3. Connect your Git repository containing this code
4. Render will automatically detect the `render.yaml` file
5. Click "Apply Blueprint"
6. In the environment variables section, add your bot token:
   - Key: `BOT_TOKEN`
   - Value: `<your-telegram-bot-token>`
7. Click "Create Blueprint"

### 4. Verify Deployment

1. Render will start deploying your service
2. Once deployment is complete, send a message to your bot on Telegram
3. Your bot should echo back any messages you send

## Configuration Details

The `render.yaml` file configures your bot as a web service:

```yaml
services:
  - type: web
    name: telegram-bot
    runtime: python
    plan: free
    branch: main
    buildCommand: pip install -r requirements.txt
    startCommand: python3 bot.py
    autoDeploy: true
    envVars:
      - key: BOT_TOKEN
        sync: false
```

You can modify the following fields based on your needs:

- `name`: Change to your preferred service name
- `plan`: Upgrade from `free` if you need more resources
- `branch`: The Git branch to deploy
- `autoDeploy`: Set to `true` to enable automatic deployments on push

## Troubleshooting

If your bot doesn't respond:

1. Check Render logs for any errors
2. Verify that the `BOT_TOKEN` environment variable is set correctly
3. Make sure your bot is running by checking the Render dashboard

## Customizing Your Bot

After forking the repository, you can customize your bot before deploying:

1. Clone your forked repository (optional):

   ```
   git clone https://github.com/your-username/render_telegram_bot.git
   cd render_telegram_bot
   ```

2. Modify the files as needed:

   - `bot.py`: Add more commands or functionality beyond the basic echo feature
   - `render.yaml`: Change service name, plan, or other deployment settings
   - `requirements.txt`: Add additional Python packages if required by your bot

3. Push your changes to GitHub:
   ```
   git add .
   git commit -m "Customize bot functionality"
   git push
   ```

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Python Telegram Bot Documentation](https://python-telegram-bot.readthedocs.io/)
- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)

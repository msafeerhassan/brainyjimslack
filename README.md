# BrainyJim Slack Bot

hey everyone! so i made this slack bot called BrainyJim and honestly it turned out pretty cool. basically it just shares random fun facts and has some interactive stuff like trivia games and number guessing.

## what it does

- serves up random facts on demand with `/fact`
- trivia games with `/trivia` - test your knowledge!
- different fact categories like animals, science, history etc
- number guessing game with `/guess`
- fun facts about specific topics with `/funfact`
- tracks your stats and has leaderboards 
- you can submit your own facts too
- loads more facts from online APIs when running low
- completely random responses for fun

## getting it running

first install the requirements:
```bash
pip install -r requirements.txt
```

then you need to create a slack app and get tokens:
1. go to https://api.slack.com/apps
2. create new app (from scratch)
3. go to OAuth & Permissions
4. add these scopes: app_mentions:read, channels:read, chat:write, commands, users:read
5. install app to workspace
6. copy bot token (starts with xoxb-)
7. go to Basic Information, copy signing secret
8. add slash commands in your app settings for each command you want to use

set them as environment variables:
```bash
# windows
set SLACK_BOT_TOKEN=xoxb-your-bot-token-here
set SLACK_SIGNING_SECRET=your-signing-secret-here

# linux/mac  
export SLACK_BOT_TOKEN=xoxb-your-bot-token-here
export SLACK_SIGNING_SECRET=your-signing-secret-here
```

run it:
```bash
python app.py
```

## commands

### slash commands
- `/fact` - random fact
- `/categoryfact [category]` - fact from specific category  
- `/trivia` - trivia question (use buttons to answer)
- `/guess [number]` - number guessing game
- `/funfact [topic]` - facts about specific topics
- `/random` - completely random response
- `/leaderboard` - trivia scores
- `/mystats` - your personal stats
- `/categories` - see all available categories
- `/submitfact [fact]` - add your own fact
- `/morefacts` - loads more facts from online APIs

### regular commands  
- `!stats` - see fact statistics
- `!info` - detailed help

## notes

- the bot automatically loads facts from various APIs if it runs low
- it stores everything in fact_data.json so data persists
- tracks your trivia scores and personal stats
- use buttons for trivia questions (much easier than reactions)
- each category has tons of different facts to discover

the code is kinda messy but it works fine. made it over a weekend so dont judge too hard 😅

## deploying 24/7 for free

if you want to run this 24/7 without paying anything, here are some good options:

### railway.app (recommended)
1. push your code to github
2. go to railway.app and sign up with github
3. create new project from github repo
4. add environment variables: `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET`
5. it should auto-deploy

### render.com  
1. push to github
2. sign up at render.com
3. create new web service from github
4. set environment variables `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET`
5. deploy

### fly.io
1. install flyctl cli
2. run `fly launch` in your project folder  
3. set secrets: `fly secrets set SLACK_BOT_TOKEN=your_token SLACK_SIGNING_SECRET=your_secret`
4. deploy with `fly deploy`

### heroku (if you can still get free tier)
1. install heroku cli
2. run `heroku create your-app-name`
3. set config vars: `heroku config:set SLACK_BOT_TOKEN=your_token SLACK_SIGNING_SECRET=your_secret`
4. push with `git push heroku main`

### other free options
- heroku alternatives like dokku
- google cloud run (free tier)
- aws lambda (might need some code changes)

most of these have free tiers that are perfect for discord bots. just make sure to set the DISCORD_TOKEN environment variable on whichever platform you choose.

pro tip: railway and render are probably the easiest to set up if you're new to this stuff.

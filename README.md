# BrainyJim Slack Bot

hey everyone! so i made this slack bot called BrainyJim and honestly it turned out pretty cool. basically it just shares random fun facts and has some interactive stuff like trivia games and number guessing.

**UPDATE**: Now uses Socket Mode for easier development and no need for public URLs!

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
3. **ENABLE SOCKET MODE**: go to Socket Mode in sidebar and enable it
4. generate App-Level Token with `connections:write` scope (save this as SLACK_APP_TOKEN)
5. go to OAuth & Permissions
6. add these bot scopes: app_mentions:read, channels:read, chat:write, commands, users:read
7. install app to workspace
8. copy bot token (starts with xoxb-) from OAuth & Permissions
9. add slash commands in your app settings for each command you want to use

set environment variables:
```bash
# windows
set SLACK_BOT_TOKEN=xoxb-your-bot-token-here
set SLACK_APP_TOKEN=xapp-your-app-token-here

# linux/mac  
export SLACK_BOT_TOKEN=xoxb-your-bot-token-here
export SLACK_APP_TOKEN=xapp-your-app-token-here
```

run it locally (no public URL needed!):
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

- **Socket Mode**: now uses socket mode for real-time connection, no public URL needed!
- the bot automatically loads facts from various APIs if it runs low
- it stores everything in fact_data.json so data persists
- tracks your trivia scores and personal stats
- use buttons for trivia questions (much easier than reactions)
- each category has tons of different facts to discover
- perfect for local development and testing

the code is kinda messy but it works fine. made it over a weekend so dont judge too hard 😅

## deploying options

### for local development (recommended)
socket mode is perfect for local development! just run `python app.py` and it connects via websocket. no need for public URLs or complex hosting.

### if you want 24/7 hosting

**Note**: Since this now uses Socket Mode, you can run it on any server without needing a public URL!

### railway.app 
1. push your code to github
2. go to railway.app and sign up with github
3. create new project from github repo
4. add environment variables: `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN`
5. it should auto-deploy

### render.com  
1. push to github
2. sign up at render.com
3. create new web service from github
4. set environment variables `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN`
5. deploy

### fly.io
1. install flyctl cli
2. run `fly launch` in your project folder  
3. set secrets: `fly secrets set SLACK_BOT_TOKEN=your_token SLACK_APP_TOKEN=your_app_token`
4. deploy with `fly deploy`

### heroku (if you can still get free tier)
1. install heroku cli
2. run `heroku create your-app-name`
3. set config vars: `heroku config:set SLACK_BOT_TOKEN=your_token SLACK_APP_TOKEN=your_app_token`
4. push with `git push heroku main`

### other free options
- heroku alternatives like dokku
- google cloud run (free tier)
- any VPS or cloud server (socket mode makes it super easy!)
- even run it on a raspberry pi at home

since socket mode doesn't need webhooks or public URLs, you can literally run this anywhere that has internet. much simpler than the old HTTP mode!

pro tip: for development just run it locally. for production, railway and render are probably the easiest to set up.

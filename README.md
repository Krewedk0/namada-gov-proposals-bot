# Namada governance proposals tracker TG bot

Telegram bot for notifications about new Namada governance proposals available for voting

[Here](https://t.me/namadaseproposals_bot) is an instance of this bot running on Shielded Expedition network

## Disclaimer

To query on-chain data (proposals info, current epoch) this project uses namada CLI calls via `subprocess` module. So in order to deploy this project to your infra make sure that user that runs the bot have `namadac` binary in its `$PATH` and CLI calls are processed by RPC server (by default `localhost:26657`).

It was made this way because at the time of making this project Namada didn't have an API/RPC interface which wouldn't require deserializing Borsh-encoded data.

## Overview

This bot utilizes Telegram API and offers two commands:

- `/start` - Default starting command, subscribes user for new proposals notifications
- `/proposals` - Lists proposals available for voting at the time of request

Data persistency is implemented via a pickle `data.pickle` file created on the first run and stored alongside the bot.

Tracking proposals job runs every 60 seconds and sends all subscribed users proposals that became active in the current epoch.

## Installation

```console
# clone the repo
$ git clone https://github.com/Krewedk0/namada-gov-proposals-bot.git && cd namada-gov-proposals-bot

# install the requirements
$ python3 -m pip install -r requirements.txt
```

## Running

Assuming you already have a TG bot token, pass it via `BOT_TOKEN` env variable and then start the bot:
```console
$ EXPORT BOT_TOKEN=1111111111:token
$ python3 bot.py
```
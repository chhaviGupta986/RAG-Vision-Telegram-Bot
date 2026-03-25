# General Questions

How do I create a bot?
Creating Telegram bots is super-easy, but you will need at least some skills at computer programming. In order for a bot to work, set up a bot account with @BotFather, then connect it to your backend server via our API.

Unfortunately, there are no out-of-the-box ways to create a working bot if you are not a developer. But we're sure you'll soon find plenty of bots created by other people to play with.

I'm a developer. Where can I find some examples?
Here are two sample bots, both written in PHP:

Hello Bot demonstrates the basics of the Telegram bot API.
Simple Poll bot is a more complete example, it supports both long-polling and Webhooks for updates.
Many members of our community are building bots and publishing sources.
We're collecting them on this page »

Ping us on @BotSupport if you've built a bot and would like to share it with others.

Will you add X to the Bot API?
The bot API is still pretty young. There are many potential features to consider and implement. We'll be studying what people do with their bots for a while to see which directions will be most important for the platform.

All bot developers are welcome to share ideas for our Bot API with our @BotSupport account.

What messages will my bot get?

1. All bots, regardless of settings, will receive:

All service messages.
All messages from private chats with users.
All messages from channels where they are a member. 2. Bot admins and bots with privacy mode disabled will receive all messages except messages sent by other bots.

3. Bots with privacy mode enabled will receive:

Commands explicitly meant for them (e.g., /command@this_bot).
General commands from users (e.g. /start) if the bot was the last bot to send a message to the group.
Messages sent via this bot.
Replies to any messages implicitly or explicitly meant for this bot.
Note that each particular message can only be available to one privacy-enabled bot at a time, i.e., a reply to bot A containing an explicit command for bot B or sent via bot C will only be available to bot A. Replies have the highest priority.

Why doesn't my bot see messages from other bots?
Bots talking to each other could potentially get stuck in unwelcome loops. To avoid this, we decided that bots will not be able to see messages from other bots regardless of mode.

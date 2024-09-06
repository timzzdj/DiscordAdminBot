# DiscordAdminBot
This Discord Bot is a simple demonstration of how it would be able to perform Administrative Tasks by using a system of roles.
A Discord Server must already have a set of Escalating roles for the bot to assign and determine when to kick a member.
The escalating roles in this sample are: Reported I, Reported II, Reported III, and Kicked.
The bot monitors the chat and detects any profanity as a requirement to assign these roles.
Other tasks can be addded in a similar systematical way of taking advantage of roles.

New Commands can be added using the same type of structure as line 85.

References for libraries used include:
discord.py: https://pypi.org/project/discord.py/
better_profanity: https://pypi.org/project/better-profanity/

For step by step instructions in creating a discord bot account see:
https://discordpy.readthedocs.io/en/stable/discord.html
https://support-dev.discord.com/hc/en-us/sections/5110493739415-Bots

See Implementation through discord chat history:
https://discord.gg/QQF5QCDe

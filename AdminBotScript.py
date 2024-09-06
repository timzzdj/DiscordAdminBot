#####################################################################
#                                                                   #
#   No.MP531142025090TDJ                                            #
#   Discord Bot performing Administrative task.                     #
#                                                                   #
#####################################################################
import asyncio                              # Time
import discord                              # pip install discord.py --user
from discord.ext import commands            # pip install discord.py --user
from discord.ext import tasks               # pip install discord.py --user
from better_profanity import profanity      # pip install better_profanity --user

#####################################################################
#                               Fields                              #
#####################################################################
# Set up Discord intents to receive specific types of events.
# Use default intents
intents = discord.Intents.default()
# Enable the ability to read message content
intents.message_content = True

# Define role names used for reporting and penalty handling.
# Roles for escalating user penalties
reported_roles = ["Reported I", "Reported II", "Reported III"]
# Role assigned to users who have been kicked
kicked_role_name = "Kicked"

# Create a new instance of the Bot with a command prefix and specified intents.
bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary containing FAQ responses for various keywords.
faq_dict = {
    "roles": "Roles are used to manage permissions for a user or a group of users.",
    "channels": "Channels in Discord can be text or voice-based, where users can communicate.",
    "server": "A server is a dedicated space for your community or group in Discord.",
    "kick": "The 'kick' command removes a user from the server.",
    "mute": "You can mute a user to prevent them from speaking in voice channels or sending messages.",
}

# Dictionary to store user contexts for follow-up interactions after an !ask command.
# Format: {user_id: {"keyword": keyword, "channel": channel, "timestamp": timestamp}}
user_context = {}
#####################################################################
#                               Tasks                               #
#####################################################################
# Task that periodically clears outdated user contexts to avoid stale data.
@tasks.loop(seconds=10)
# Clears user contexts that are older than 60 seconds.
async def clear_old_contexts():
    # Get the current time in seconds
    current_time = asyncio.get_event_loop().time()
    expired_users = [user_id for user_id, context in user_context.items()
                     # Find contexts older than 60 seconds
                     if current_time - context["timestamp"] > 60]
    for user_id in expired_users:
        # Remove expired contexts
        del user_context[user_id]
        # Debug output to the console
        print(f"Cleared context for user {user_id} due to timeout.")
#####################################################################
#                       Commands/Functions                          #
#####################################################################
# Event that triggers when the bot has successfully connected to Discord.
@bot.event
async def on_ready():
    # Output bot login information to the console
    print(f"Logged in as {bot.user}")

# Handles all incoming messages and processes commands.
@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    # Check for profanity in the message content
    if profanity.contains_profanity(message.content):
        # Check messages for profanity and assign a penalty tag if necessary.
        await handle_profanity(message)
    # Process any commands for the message
    await bot.process_commands(message)
    # Handle the context for FAQ interactions
    await handle_faq_context(message)

# Responds with a greeting and provides basic instructions.
@bot.command()
async def hello(ctx):
    # Send a greeting
    await ctx.send(f'Hello {ctx.author.mention}!\n')
    # Send instructions
    await ctx.send(f'For inquiries use !ask and keywords such as roles, channels, server, kick, mute.\n')
    # Inform about profanity filter
    await ctx.send(f'Messages with profanity will be filtered and Users will be reported or kicked.')

# Handles the !ask command and provides interactive FAQ responses.
@bot.command()
async def ask(ctx, *, question: str):
    # Match keywords in the question
    matched_keywords = [keyword for keyword in faq_dict if keyword in question.lower()]
    
    if matched_keywords:
        # Store context for follow-up interactions
        user_context[ctx.author.id] = {
            "keyword": matched_keywords[0],              # Store the first matched keyword
            "channel": ctx.channel,                      # Store the channel where the question was asked
            "timestamp": asyncio.get_event_loop().time() # Store the current time
        }
        # Prompt the user to confirm the detected keyword
        await ctx.send(f"Are you asking about '{matched_keywords[0]}'? (Please reply with 'yes' or 'no')")
    else:
        # No matching keyword found, ask user to use valid keywords
        await ctx.send("I couldn't find a matching topic. Please use keywords like 'roles', 'channels', 'server', etc.")
#####################################################################
#                              Methods                              #
#####################################################################
# Handles user responses ('yes' or 'no') for the FAQ interaction.
async def handle_faq_context(message):
    # No stored context for the user, exit function
    if message.author.id not in user_context:
        return
    # Retrieve the stored context for the user
    context = user_context[message.author.id]
    # The detected keyword
    keyword = context["keyword"]
    # The channel where the interaction started
    channel = context["channel"]

    if message.channel == channel:
        # User confirmed the detected keyword
        if message.content.lower() == 'yes':
            # Send the FAQ response
            await message.channel.send(faq_dict[keyword])
            # Clear context after the conversation
            del user_context[message.author.id]
        elif message.content.lower() == 'no':
            # User denied the detected keyword 
            await message.channel.send("Okay, please try using different keywords.")
            # Clear context after the conversation
            del user_context[message.author.id]
        # Ignore if another command or interaction starts
        elif message.content.startswith('!'):
            return
# Handles profanity filtering and escalates user penalties.
async def handle_profanity(message):
    # The author of the message
    member = message.author
    # The channel where the message was sent
    channel = message.channel
    # Variable to store the user's current reported role
    current_reported_role = None

    # Determine the current reported role, if any
    for role in member.roles:
        # Assign the reported role if found
        if role.name in reported_roles:
            current_reported_role = role.name
            break

    # Handle role assignment or escalation
    if current_reported_role is None:
        # No reported role found, assign "Reported I"
        await assign_role(member, "Reported I", channel)
    else:
        # Get the current level
        current_level = reported_roles.index(current_reported_role)
        # Checks if current role level is not max
        if current_level < len(reported_roles) - 1:
            # Escalate to the next level
            next_role = reported_roles[current_level + 1]
            await assign_role(member, next_role, channel)
        else:
            # User has "Reported III", kick them
            await kick_member(member, channel)

# Assign a new role to a member and remove old reported roles.
async def assign_role(member, role_name, channel):
    # The server (guild) where the member belongs
    guild = member.guild
    # Get the new role by name
    new_role = discord.utils.get(guild.roles, name=role_name)

    # Remove any existing reported roles
    for role in member.roles:
        if role.name in reported_roles:
            # Remove old reported role
            await member.remove_roles(role)

    # Add and assign the new role
    await member.add_roles(new_role)
    # Notify the new role to the member
    await channel.send(f"{member.mention} has been assigned the role {role_name}.")

# Kick the user and assign a 'Kicked' role if they come back.
async def kick_member(member, channel):
    # The server (guild) where the member belongs
    guild = member.guild
    # Get the 'Kicked' role by name
    kicked_role = discord.utils.get(guild.roles, name=kicked_role_name)

    # Kick the member from the server
    await member.kick(reason="Reached Reported III penalty.")
    # Provide reason for the kick
    await channel.send(f"{member.mention} has been kicked for reaching Reported III penalty.")

    # Add a "Kicked" role for tracking if they return
    if kicked_role:
        # Assign the 'Kicked' role to the member
        await member.add_roles(kicked_role)

# Runs the bot with the provided token.
def run_bot(token: str):
    # Start the bot using the specified token
    bot.run(token)
#####################################################################
#                               Main                                #
#####################################################################
# Run the bot
if __name__ == "__main__":
    run_bot('API_KEY')
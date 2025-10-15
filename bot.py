import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta
import pytz
import requests
from ics import Calendar
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Your TimeEdit calendar URL
CALENDAR_URL = os.getenv('CALENDAR_URL')
TIMEZONE = pytz.timezone('Europe/Brussels')

# Fun motivational quotes
MOTIVATIONAL_QUOTES = [
    "You've got this! 💪",
    "Time to be brilliant! ✨",
    "Let's learn something awesome today! 🚀",
    "Your brain is going to love this! 🧠",
    "Another step closer to your goals! 🎯",
    "Knowledge is power! ⚡",
    "You're doing amazing! 🌟",
    "Let's make today count! 📚",
    "Time to shine! ☀️",
    "Learning mode: ACTIVATED! 🎓"
]

# Fun facts about studying
FUN_FACTS = [
    "🧠 Did you know? Your brain uses 20% of your body's energy!",
    "📚 Reading for just 6 minutes can reduce stress by 68%!",
    "☕ The best time to study is between 10 AM and 2 PM, and then again between 4 PM and 10 PM!",
    "🎵 Classical music can help improve concentration while studying!",
    "💤 Getting enough sleep improves memory retention by up to 40%!",
    "🚶 Taking short breaks every 50 minutes improves learning efficiency!",
    "🧘 Meditation before studying can improve focus by up to 14%!",
    "🍎 Eating blueberries can boost concentration and memory!",
    "✍️ Writing notes by hand helps you remember better than typing!",
    "🌈 Using colors in your notes activates both sides of your brain!"
]

def get_calendar_events():
    """Fetch and parse the TimeEdit calendar"""
    try:
        response = requests.get(CALENDAR_URL, timeout=10)
        response.raise_for_status()
        calendar = Calendar(response.text)
        return list(calendar.events)
    except Exception as e:
        print(f"Error fetching calendar: {e}")
        return []

def get_events_for_date(date):
    """Get all events for a specific date"""
    events = get_calendar_events()
    date_events = []
    
    for event in events:
        event_start = event.begin.datetime
        if event_start.tzinfo is None:
            event_start = TIMEZONE.localize(event_start)
        else:
            event_start = event_start.astimezone(TIMEZONE)
        
        if event_start.date() == date.date():
            date_events.append(event)
    
    return sorted(date_events, key=lambda e: e.begin)

def format_event(event):
    """Format a single event nicely"""
    start = event.begin.datetime
    end = event.end.datetime
    
    if start.tzinfo is None:
        start = TIMEZONE.localize(start)
    else:
        start = start.astimezone(TIMEZONE)
    
    if end.tzinfo is None:
        end = TIMEZONE.localize(end)
    else:
        end = end.astimezone(TIMEZONE)
    
    # Get emoji based on time of day
    hour = start.hour
    if hour < 10:
        emoji = "🌅"  # Early morning
    elif hour < 12:
        emoji = "☀️"  # Morning
    elif hour < 14:
        emoji = "🌤️"  # Afternoon
    elif hour < 17:
        emoji = "🌆"  # Late afternoon
    else:
        emoji = "🌙"  # Evening
    
    duration = end - start
    duration_str = f"{duration.seconds // 3600}h {(duration.seconds % 3600) // 60}m"
    
    location = event.location if event.location else "No location specified"
    
    return f"{emoji} **{event.name}**\n⏰ {start.strftime('%H:%M')} - {end.strftime('%H:%M')} ({duration_str})\n📍 {location}\n"

def get_next_class():
    """Get the next upcoming class"""
    events = get_calendar_events()
    now = datetime.now(TIMEZONE)
    
    upcoming = []
    for event in events:
        event_start = event.begin.datetime
        if event_start.tzinfo is None:
            event_start = TIMEZONE.localize(event_start)
        else:
            event_start = event_start.astimezone(TIMEZONE)
        
        if event_start > now:
            upcoming.append(event)
    
    if upcoming:
        upcoming.sort(key=lambda e: e.begin)
        return upcoming[0]
    return None

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="today", description="Show today's timetable")
async def today(interaction: discord.Interaction):
    """Display today's classes"""
    await interaction.response.defer()
    
    now = datetime.now(TIMEZONE)
    events = get_events_for_date(now)
    
    if not events:
        embed = discord.Embed(
            title="📅 Today's Timetable",
            description="🎉 No classes today! Enjoy your free time!",
            color=discord.Color.green(),
            timestamp=now
        )
        quote = random.choice(MOTIVATIONAL_QUOTES)
        embed.set_footer(text=quote)
        await interaction.followup.send(embed=embed)
        return
    
    embed = discord.Embed(
        title=f"📅 Today's Timetable - {now.strftime('%A, %B %d, %Y')}",
        description="Here are your classes for today:",
        color=discord.Color.blue(),
        timestamp=now
    )
    
    for event in events:
        embed.add_field(
            name="\u200b",
            value=format_event(event),
            inline=False
        )
    
    quote = random.choice(MOTIVATIONAL_QUOTES)
    embed.set_footer(text=quote)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="tomorrow", description="Show tomorrow's timetable")
async def tomorrow(interaction: discord.Interaction):
    """Display tomorrow's classes"""
    await interaction.response.defer()
    
    now = datetime.now(TIMEZONE)
    tomorrow_date = now + timedelta(days=1)
    events = get_events_for_date(tomorrow_date)
    
    if not events:
        embed = discord.Embed(
            title="📅 Tomorrow's Timetable",
            description="🎉 No classes tomorrow! Time to relax!",
            color=discord.Color.green(),
            timestamp=now
        )
        quote = random.choice(MOTIVATIONAL_QUOTES)
        embed.set_footer(text=quote)
        await interaction.followup.send(embed=embed)
        return
    
    embed = discord.Embed(
        title=f"📅 Tomorrow's Timetable - {tomorrow_date.strftime('%A, %B %d, %Y')}",
        description="Here's what you have tomorrow:",
        color=discord.Color.purple(),
        timestamp=now
    )
    
    for event in events:
        embed.add_field(
            name="\u200b",
            value=format_event(event),
            inline=False
        )
    
    quote = random.choice(MOTIVATIONAL_QUOTES)
    embed.set_footer(text=quote)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="week", description="Show this week's timetable")
async def week(interaction: discord.Interaction):
    """Display the entire week's schedule"""
    await interaction.response.defer()
    
    now = datetime.now(TIMEZONE)
    # Get Monday of current week
    monday = now - timedelta(days=now.weekday())
    
    embed = discord.Embed(
        title=f"📅 Week Schedule - Week {monday.strftime('%W')}",
        description=f"Your schedule from {monday.strftime('%B %d')} to {(monday + timedelta(days=6)).strftime('%B %d, %Y')}",
        color=discord.Color.orange(),
        timestamp=now
    )
    
    has_classes = False
    for i in range(7):
        day = monday + timedelta(days=i)
        events = get_events_for_date(day)
        
        if events:
            has_classes = True
            day_text = ""
            for event in events:
                start = event.begin.datetime
                if start.tzinfo is None:
                    start = TIMEZONE.localize(start)
                else:
                    start = start.astimezone(TIMEZONE)
                day_text += f"• {start.strftime('%H:%M')} - {event.name}\n"
            
            embed.add_field(
                name=f"{day.strftime('%A, %B %d')}",
                value=day_text,
                inline=False
            )
    
    if not has_classes:
        embed.description = "🎉 No classes this week! Enjoy your break!"
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="next", description="Show the next upcoming class")
async def next_class(interaction: discord.Interaction):
    """Display the next class with countdown"""
    await interaction.response.defer()
    
    next_event = get_next_class()
    now = datetime.now(TIMEZONE)
    
    if not next_event:
        embed = discord.Embed(
            title="🎓 Next Class",
            description="🎉 No more classes scheduled! You're all done!",
            color=discord.Color.green(),
            timestamp=now
        )
        await interaction.followup.send(embed=embed)
        return
    
    start = next_event.begin.datetime
    if start.tzinfo is None:
        start = TIMEZONE.localize(start)
    else:
        start = start.astimezone(TIMEZONE)
    
    end = next_event.end.datetime
    if end.tzinfo is None:
        end = TIMEZONE.localize(end)
    else:
        end = end.astimezone(TIMEZONE)
    
    time_until = start - now
    days = time_until.days
    hours, remainder = divmod(time_until.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    countdown = ""
    if days > 0:
        countdown = f"{days} day(s), {hours} hour(s), {minutes} minute(s)"
    elif hours > 0:
        countdown = f"{hours} hour(s), {minutes} minute(s)"
    else:
        countdown = f"{minutes} minute(s)"
    
    embed = discord.Embed(
        title="🎓 Next Class",
        description=f"**{next_event.name}**",
        color=discord.Color.blue(),
        timestamp=now
    )
    
    embed.add_field(name="⏰ Time", value=f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}", inline=True)
    embed.add_field(name="📅 Date", value=start.strftime('%A, %B %d, %Y'), inline=True)
    embed.add_field(name="📍 Location", value=next_event.location if next_event.location else "No location", inline=True)
    embed.add_field(name="⏳ Time Until Class", value=countdown, inline=False)
    
    quote = random.choice(MOTIVATIONAL_QUOTES)
    embed.set_footer(text=quote)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="freetime", description="Show your free periods today")
async def freetime(interaction: discord.Interaction):
    """Display free time between classes"""
    await interaction.response.defer()
    
    now = datetime.now(TIMEZONE)
    events = get_events_for_date(now)
    
    if not events:
        embed = discord.Embed(
            title="🆓 Free Time Today",
            description="🎉 The whole day is free! No classes!",
            color=discord.Color.green(),
            timestamp=now
        )
        await interaction.followup.send(embed=embed)
        return
    
    embed = discord.Embed(
        title="🆓 Free Periods Today",
        description="Here are your breaks between classes:",
        color=discord.Color.teal(),
        timestamp=now
    )
    
    has_free_time = False
    for i in range(len(events) - 1):
        current_end = events[i].end.datetime
        next_start = events[i + 1].begin.datetime
        
        if current_end.tzinfo is None:
            current_end = TIMEZONE.localize(current_end)
        else:
            current_end = current_end.astimezone(TIMEZONE)
        
        if next_start.tzinfo is None:
            next_start = TIMEZONE.localize(next_start)
        else:
            next_start = next_start.astimezone(TIMEZONE)
        
        free_time = next_start - current_end
        if free_time.seconds > 900:  # More than 15 minutes
            has_free_time = True
            hours, remainder = divmod(free_time.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            
            embed.add_field(
                name=f"⏰ {current_end.strftime('%H:%M')} - {next_start.strftime('%H:%M')}",
                value=f"🎯 Free for {duration}",
                inline=False
            )
    
    if not has_free_time:
        embed.description = "📚 Your classes are back-to-back today! Stay strong!"
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="stats", description="Show your timetable statistics")
async def stats(interaction: discord.Interaction):
    """Display statistics about your schedule"""
    await interaction.response.defer()
    
    events = get_calendar_events()
    now = datetime.now(TIMEZONE)
    
    if not events:
        await interaction.followup.send("No classes found in your calendar!")
        return
    
    # Calculate stats
    total_classes = len(events)
    
    # Classes by day
    day_count = {}
    total_hours = timedelta()
    
    for event in events:
        start = event.begin.datetime
        if start.tzinfo is None:
            start = TIMEZONE.localize(start)
        else:
            start = start.astimezone(TIMEZONE)
        
        day_name = start.strftime('%A')
        day_count[day_name] = day_count.get(day_name, 0) + 1
        
        duration = event.end.datetime - event.begin.datetime
        total_hours += duration
    
    busiest_day = max(day_count, key=day_count.get) if day_count else "None"
    total_hours_num = total_hours.total_seconds() / 3600
    
    embed = discord.Embed(
        title="📊 Your Timetable Statistics",
        description="Here's an overview of your schedule:",
        color=discord.Color.gold(),
        timestamp=now
    )
    
    embed.add_field(name="📚 Total Classes", value=str(total_classes), inline=True)
    embed.add_field(name="⏱️ Total Hours", value=f"{total_hours_num:.1f}h", inline=True)
    embed.add_field(name="🔥 Busiest Day", value=f"{busiest_day} ({day_count.get(busiest_day, 0)} classes)", inline=True)
    
    # Classes per day breakdown
    if day_count:
        days_text = "\n".join([f"**{day}**: {count} classes" for day, count in sorted(day_count.items())])
        embed.add_field(name="📅 Classes per Day", value=days_text, inline=False)
    
    fact = random.choice(FUN_FACTS)
    embed.set_footer(text=fact)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="funfact", description="Get a fun study-related fact!")
async def funfact(interaction: discord.Interaction):
    """Share a random fun fact"""
    fact = random.choice(FUN_FACTS)
    
    embed = discord.Embed(
        title="🎲 Fun Fact!",
        description=fact,
        color=discord.Color.random(),
        timestamp=datetime.now(TIMEZONE)
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="motivation", description="Get a motivational boost!")
async def motivation(interaction: discord.Interaction):
    """Get a motivational quote"""
    quote = random.choice(MOTIVATIONAL_QUOTES)
    
    embed = discord.Embed(
        title="💪 Motivation Boost!",
        description=quote,
        color=discord.Color.gold(),
        timestamp=datetime.now(TIMEZONE)
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Display help information"""
    embed = discord.Embed(
        title="🤖 KdG Timetable Bot - Help",
        description="Here are all the commands you can use:",
        color=discord.Color.blue(),
        timestamp=datetime.now(TIMEZONE)
    )
    
    commands_list = [
        ("📅 /today", "Show today's timetable"),
        ("📅 /tomorrow", "Show tomorrow's timetable"),
        ("📅 /week", "Show this week's schedule"),
        ("🎓 /next", "Show the next upcoming class with countdown"),
        ("🆓 /freetime", "Show your free periods today"),
        ("📊 /stats", "View your timetable statistics"),
        ("🎲 /funfact", "Get a fun study-related fact"),
        ("💪 /motivation", "Get a motivational boost"),
        ("❓ /help", "Show this help message"),
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.set_footer(text="Made with ❤️ for KdG students")
    
    await interaction.response.send_message(embed=embed)

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables!")
        print("Please create a .env file with your Discord bot token.")
        exit(1)
    
    if not CALENDAR_URL:
        print("Error: CALENDAR_URL not found in environment variables!")
        print("Please add your TimeEdit calendar URL to the .env file.")
        exit(1)
    
    bot.run(token)
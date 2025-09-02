import discord
from discord.ext import commands
import os
import threading
from flask import Flask

# إعدادات Flask عشان Render يشوف Port مفتوح
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

# تشغيل Flask في Thread ثاني
threading.Thread(target=run_web).start()

# إعدادات البوت
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

ratings = {}
STORIES_CHANNEL_ID = 1329119283686670427  # <<<< ID الروم
episode_counter = 0  # يعد الحلقات تلقائياً

class RatingView(discord.ui.View):
    def __init__(self, story_id, story_title):
        super().__init__(timeout=None)
        self.story_id = story_id
        self.story_title = story_title
        for i in range(1, 11):
            self.add_item(RatingButton(i, story_id, story_title))

class RatingButton(discord.ui.Button):
    def __init__(self, number, story_id, story_title):
        super().__init__(style=discord.ButtonStyle.primary, label=str(number))
        self.number = number
        self.story_id = story_id
        self.story_title = story_title

    async def callback(self, interaction: discord.Interaction):
        if self.story_id not in ratings:
            ratings[self.story_id] = {"title": self.story_title, "scores": {}}
        ratings[self.story_id]["scores"][interaction.user.id] = self.number
        await interaction.response.send_message(
            f"✅ {interaction.user.mention} قيّم **{self.story_title}** بـ {self.number}/10",
            ephemeral=True
        )

@bot.event
async def on_message(message):
    global episode_counter
    if message.author.bot:
        return

    if message.channel.id == STORIES_CHANNEL_ID:
        episode_counter += 1
        story_id = message.id
        story_title = f"الموسم الرابع - الحلقة {episode_counter}"
        ratings[story_id] = {"title": story_title, "scores": {}}
        view = RatingView(story_id, story_title)
        await message.channel.send(
            f"📖 تم نشر: **{story_title}**\n⬇️ اختر تقييمك:",
            view=view
        )

    await bot.process_commands(message)

@bot.command()
async def results(ctx, episode: int = None):
    if not ratings:
        await ctx.send("⚠️ مافي أي تقييمات للحين.")
        return

    if episode is None:
        msg = "📊 **نتائج التقييمات:**\n"
        for story_id, data in ratings.items():
            scores = data["scores"]
            if scores:
                avg = sum(scores.values()) / len(scores)
                msg += f"- {data['title']}: {avg:.1f}/10 ({len(scores)} تقييم)\n"
        await ctx.send(msg)
    else:
        for story_id, data in ratings.items():
            if f"الحلقة {episode}" in data["title"]:
                scores = data["scores"]
                if not scores:
                    await ctx.send(f"⚠️ مافي تقييمات للحلقة {episode}.")
                    return
                avg = sum(scores.values()) / len(scores)
                await ctx.send(
                    f"📊 نتائج **{data['title']}**: {avg:.1f}/10 ({len(scores)} تقييم)"
                )
                return
        await ctx.send(f"⚠️ ما لقيت الحلقة {episode}.")

# تشغيل البوت باستخدام Environment Variable
bot.run(os.getenv("DISCORD_TOKEN"))

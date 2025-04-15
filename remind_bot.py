import discord
from discord.ext import commands, tasks
import asyncio
import time
import os
from dotenv import load_dotenv


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ユーザーごとのリマインダー保存用
reminders = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def rem(ctx, minutes: int, *, content: str):
    user_id = ctx.author.id
    if user_id not in reminders:
        reminders[user_id] = []

    reminder_id = len(reminders[user_id]) + 1
    trigger_time = time.time() + minutes * 60

    reminders[user_id].append({
        "id": reminder_id,
        "content": content,
        "time": trigger_time,
        "channel_id": ctx.channel.id
    })

    await ctx.send(f"{minutes}分後に以下のメッセージを返します：\n`{content}`（番号: {reminder_id}）")

    await asyncio.sleep(minutes * 60)

    # 時間経過後、まだリストにあれば送信
    if user_id in reminders:
        for r in reminders[user_id]:
            if r["id"] == reminder_id:
                channel = bot.get_channel(r["channel_id"])
                await channel.send(f"{ctx.author.mention} リマインダー：{r['content']}")
                reminders[user_id].remove(r)
                break

@bot.command()
async def remlis(ctx):
    user_id = ctx.author.id
    if user_id not in reminders or not reminders[user_id]:
        await ctx.send("現在、リマインダーはありません。")
        return

    msg = "**あなたのリマインダー一覧：**\n"
    for r in reminders[user_id]:
        remaining = int(r["time"] - time.time())
        mins = remaining // 60
        secs = remaining % 60
        msg += f"番号 `{r['id']}`：`{r['content']}`（残り {mins}分{secs}秒）\n"
    await ctx.send(msg)

@bot.command()
async def remdel(ctx, reminder_id: int):
    user_id = ctx.author.id
    if user_id in reminders:
        for r in reminders[user_id]:
            if r["id"] == reminder_id:
                reminders[user_id].remove(r)
                await ctx.send(f"番号 `{reminder_id}` のリマインダーを削除しました。")
                return
    await ctx.send("その番号のリマインダーは見つかりませんでした。")


# 起動処理
load_dotenv()
bot.run(os.getenv("DISCORD_TOKEN"))

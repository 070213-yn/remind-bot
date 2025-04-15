import discord
from discord.ext import commands, tasks
import asyncio
import time
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
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

    await ctx.send(f"{minutes}分後に以下の内容をお届けいたします：\n`{content}`（番号: {reminder_id}）")

    await asyncio.sleep(minutes * 60)

    # 時間経過後、まだリストにあれば送信
    if user_id in reminders:
        for r in reminders[user_id]:
            if r["id"] == reminder_id:
                channel = bot.get_channel(r["channel_id"])
                await channel.send(f"{ctx.author.mention} お嬢様、リマインダーでございます：{r['content']}")
                reminders[user_id].remove(r)
                break

@bot.command()
async def rem(ctx, *args):
    user_id = ctx.author.id
    if user_id not in reminders:
        reminders[user_id] = []

    if len(args) % 2 != 0:
        await ctx.send("さぁお嬢様、なにをリマインドされますか？ ")
        return

    now = datetime.utcnow() + timedelta(hours=9)

    for i in range(0, len(args), 2):
        datetime_str = args[i]
        content = args[i + 1]

        try:
            target = datetime.strptime(datetime_str, "%m%d%H%M")
            target = target.replace(year=now.year)
            if target <= now:
                target = target.replace(year=now.year + 1)
            seconds = (target - now).total_seconds()
        except Exception:
            await ctx.send(f"申し訳ございません、`{datetime_str}` は日時として正しく読み取れませんでした。形式をご確認くださいませ。")
            continue

        reminder_id = len(reminders[user_id]) + 1
        reminders[user_id].append({
            "id": reminder_id,
            "content": content,
            "time": time.time() + seconds,
            "channel_id": ctx.channel.id
        })

        await ctx.send(f"{target.strftime('%Y/%m/%d %H:%M')} に以下の内容をお届けいたします：\n`{content}`（番号: {reminder_id}）")

        # 各リマインダーは非同期で待機
        async def wait_and_send(user_id, reminder_id, seconds):
            await asyncio.sleep(seconds)
            if user_id in reminders:
                for r in reminders[user_id]:
                    if r["id"] == reminder_id:
                        channel = bot.get_channel(r["channel_id"])
                        await channel.send(f"{ctx.author.mention} お嬢様、リマインダーでございます：{r['content']}")
                        reminders[user_id].remove(r)
                        break

        bot.loop.create_task(wait_and_send(user_id, reminder_id, seconds))


@bot.command()
async def remlis(ctx):
    user_id = ctx.author.id
    if user_id not in reminders or not reminders[user_id]:
        await ctx.send("現在、お嬢様のリマインダーは登録されておりません。")
        return

    msg = "**お嬢様のリマインダー一覧でございます：**\n"
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
                await ctx.send(f"番号 `{reminder_id}` のリマインダーを削除いたしました。")
                return
    await ctx.send("申し訳ございません、その番号のリマインダーは見つかりませんでした。")

@bot.command()
async def remhelp(ctx):
    help_text = (
        "お嬢様、リマインダーBotの使い方をご案内いたします：\n\n"
        "`!rem [MMDDHHmm] [内容]`\n"
        "　例：`!rem 04151400 お紅茶の時間`\n\n"
        "複数同時にご登録いただく場合は、日時とメッセージはペアでご入力くださいませ。\n"
        "　例：`!rem 04151400 ちょっとメイドと話す 04151500 ドレスの仕立て確認`\n\n"
        "その他コマンド：\n"
        "　`!remlis`：現在のリマインダー一覧を表示いたします\n"
        "　`!remdel [番号]`：指定したリマインダーを削除いたします"
    )
    await ctx.send(help_text)

# 起動処理
load_dotenv()
bot.run(os.getenv("DISCORD_TOKEN"))

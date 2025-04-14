import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
from discord import FFmpegPCMAudio
from dotenv import load_dotenv
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 保存用辞書 {user_id: [{"time": datetime, "title": str, "channel": channel}, ...]}
reminders = {}
pending_inputs = {}  # 一時入力状態管理 {user_id: {step, time, channel}}

@bot.event
async def on_ready():
    print(f"ログイン成功: {bot.user}")
    check_reminders.start()

@bot.command()
async def rem(ctx):
    user_id = ctx.author.id
    pending_inputs[user_id] = {"step": "waiting_time", "channel": ctx.channel}
    await ctx.send("リマインドしたい時間を入力してください（例: `202504141600`）")

@bot.command()
async def remlis(ctx):
    user_id = ctx.author.id
    user_reminders = reminders.get(user_id, [])
    if not user_reminders:
        await ctx.send("現在登録されているリマインドはありません。")
        return

    msg = "**現在のリマインド一覧：**\n"
    for i, r in enumerate(user_reminders, start=1):
        time_str = r["time"].strftime('%Y-%m-%d %H:%M')
        msg += f"{i}. {r['title']}（{time_str}）\n"
    await ctx.send(msg)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", timeout=15.0, check=check)
        indices = [int(i.strip()) - 1 for i in msg.content.split(",") if i.strip().isdigit()]
        indices.sort(reverse=True)
        for i in indices:
            if 0 <= i < len(reminders[user_id]):
                reminders[user_id].pop(i)
        await ctx.send("指定したリマインドを削除しました。")
    except asyncio.TimeoutError:
        await ctx.send("削除時間が過ぎたためキャンセルしました。")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    if user_id in pending_inputs:
        state = pending_inputs[user_id]
        if state["step"] == "waiting_time":
            try:
                dt = datetime.strptime(message.content.strip(), "%Y%m%d%H%M")
                state["time"] = dt
                state["step"] = "waiting_title"
                await message.channel.send("リマインドのタイトルを入力してください。")
            except ValueError:
                await message.channel.send("正しい形式で日時を入力してください（例: 202504141600）")
        elif state["step"] == "waiting_title":
            title = message.content.strip()
            reminder = {
                "time": state["time"],
                "title": title,
                "channel": state["channel"],
            }
            reminders.setdefault(user_id, []).append(reminder)
            await message.channel.send(f"✅ リマインドを登録しました：『{title}』")
            del pending_inputs[user_id]
    await bot.process_commands(message)

async def get_user_voice_channel(user_id):
    for guild in bot.guilds:
        member = guild.get_member(user_id)
        if member and member.voice:
            return member.voice.channel
    return None

@tasks.loop(seconds=60)
async def check_reminders():
    now = datetime.now()
    for user_id, reminder_list in list(reminders.items()):
        for r in reminder_list[:]:
            if now >= r["time"]:
                channel = r["channel"]
                user_mention = f"<@{user_id}>"
                await channel.send(f"{user_mention} さんにリマインド 🔔 『{r['title']}』の時間になりました。")

                # 音声再生（ボイスチャンネルに参加していれば）
                voice_channel = await get_user_voice_channel(user_id)
                if voice_channel:
                    try:
                        vc = await voice_channel.connect()
                        vc.play(FFmpegPCMAudio("remind.mp3"))
                        while vc.is_playing():
                            await asyncio.sleep(1)
                        await vc.disconnect()
                    except Exception as e:
                        print(f"音声再生エラー: {e}")

                reminder_list.remove(r)

@bot.command(name="remhelp")
async def remhelp_command(ctx):
    help_text = (
        "**📌 リマインドBot コマンド一覧**\n\n"
        "`!rem`：リマインドを作成します。\n"
        "　→ 日時（例：202504141600）を入力 → タイトルを入力 で登録されます。\n\n"
        "`!remlis`：現在登録中のリマインド一覧を表示します。\n"
        "　→ 数字を送信することで、該当リマインドを削除できます。\n\n"
        "`!remhelp`：このコマンド一覧を表示します。\n"
    )
    await ctx.send(help_text)

# 起動処理
load_dotenv()
bot.run(os.getenv("DISCORD_TOKEN"))

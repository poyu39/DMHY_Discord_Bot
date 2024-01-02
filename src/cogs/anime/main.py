import feedparser
import json
from discord.ext import commands
from discord import app_commands, Interaction
from discord.app_commands import Choice
from settings import Config, logger, replier

CONFIG = Config()


class Anime(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.rss_base_url = 'https://share.dmhy.org/topics/rss/rss.xml'
        self.subscribe_data = self.read_subscribe()

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info('>>已載入 Dmhy<<')

    @app_commands.command(name='動畫資源搜尋', description='搜尋動畫資源')
    @app_commands.rename(keyword='關鍵字', team='字幕組')
    @app_commands.choices(
        team=[
            Choice(name='全部', value=0),
            Choice(name='喵萌奶茶屋', value=669),
        ]
    )
    async def search(self, interaction: Interaction, keyword: str, team: int):
        await interaction.response.defer()
        # 將空白替換成加號
        keyword = keyword.replace(' ', '+')
        if keyword:
            reply_embed = replier.success(value=f'搜尋 {keyword} 的前10筆結果')
            search_result, url = self.search_in_dmhy(keyword, team)
            for anime in search_result[:10]:
                reply_embed.add_field(
                    name='',
                    value=f"[{anime['title']}]({anime['link']})\n更新時間: {anime['date']}",
                    inline=False,
                )
            reply_embed.add_field(
                name='',
                value=f'如果要訂閱此關鍵字的 RSS 請複製以下連結\n{url}',
            )
            reply_embed.set_author(name='Dmhy', url='https://share.dmhy.org/')
            reply_embed.set_thumbnail(url='https://share.dmhy.org/favicon.ico')
            reply_embed.set_footer(text='Source by Dmhy, Developed by poyu39')
            return await interaction.followup.send(embed=reply_embed, ephemeral=True)
        else:
            reply_embed = replier.error(value='請輸入關鍵字')
            return await interaction.followup.send(embed=reply_embed, ephemeral=True)
    
    def search_in_dmhy(self, keyword, team):
        result = []
        url = f'{self.rss_base_url}?keyword={keyword}&order=date-desc'
        if team != 0:
            url += f'&team_id={team}'
        raw_feed = feedparser.parse(url)
        for entry in raw_feed.entries:
            result.append({
                'title': entry.title,
                'link': entry.link,
                'date': entry.published,
                # 'magnet': entry.enclosures[0].href,
            })
        return result, url
    
    @app_commands.command(name='訂閱 RSS', description='當有新資源時會有通知')
    @app_commands.rename(url='訂閱連結')
    async def subscribe(self, interaction: Interaction, url: str):
        await interaction.response.defer()
        reply_embed = None
        if self.rss_base_url not in url:
            reply_embed = replier.error(value='請輸入正確的 RSS 連結')
        if interaction.user.id not in self.subscribe_data:
            self.subscribe_data[interaction.user.id] = {'subscribes': [url]}
        else:
            if url in self.subscribe_data[interaction.user.id]['subscribes']:
                reply_embed = replier.warning(value='已訂閱過此 RSS')
            else:
                self.subscribe_data[interaction.user.id]['subscribes'].append(url)
                reply_embed = replier.success(value='訂閱成功！')
        self.update_subscribe()
        await interaction.followup.send(embed=reply_embed, ephemeral=True)
    
    def read_subscribe(self):
        with open(CONFIG.SUBSCRIBE_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def update_subscribe(self):
        with open(CONFIG.SUBSCRIBE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.subscribe_data, f, ensure_ascii=False, indent=4)
    
    @app_commands.command(name='查看訂閱', description='查看已訂閱的 RSS')
    async def show_subscribe(self, interaction: Interaction):
        await interaction.response.defer()
        if interaction.user.id not in self.subscribe_data or not self.subscribe_data[interaction.user.id]['subscribes']:
            reply_embed = replier.warning(value='你還沒有訂閱任何 RSS')
        else:
            reply_embed = replier.success(value='以下是你的訂閱')
            if interaction.user.id in self.subscribe_data:
                for subscribe in self.subscribe_data[interaction.user.id]['subscribes']:
                    reply_embed.add_field(
                        name='',
                        value=f'{subscribe}',
                        inline=False,
                    )
        await interaction.followup.send(embed=reply_embed, ephemeral=True)
        
    @app_commands.command(name='取消訂閱', description='取消訂閱 RSS')
    @app_commands.rename(url='訂閱連結')
    async def unsubscribe(self, interaction: Interaction, url: str):
        await interaction.response.defer()
        reply_embed = None
        if interaction.user.id in self.subscribe_data:
            if url in self.subscribe_data[interaction.user.id]['subscribes']:
                self.subscribe_data[interaction.user.id]['subscribes'].remove(url)
                reply_embed = replier.success(value='取消訂閱成功！')
            else:
                reply_embed = replier.warning(value='你沒有訂閱過此 RSS')
        else:
            reply_embed = replier.warning(value='你還沒有訂閱任何 RSS')
        self.update_subscribe()
        await interaction.followup.send(embed=reply_embed, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Anime(bot), guild=bot.get_guild(CONFIG.GUILD_ID))

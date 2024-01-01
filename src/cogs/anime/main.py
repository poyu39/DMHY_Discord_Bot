import feedparser
from discord.ext import commands
from discord import app_commands, Interaction

from settings import Config, logger, replier

CONFIG = Config()


class Anime(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.rss_base_url = 'https://share.dmhy.org/topics/rss/rss.xml'

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info('>>已載入 Dmhy<<')

    @app_commands.command(name='動畫資源搜尋', description='搜尋動畫資源')
    @app_commands.rename(keyword='關鍵字')
    async def search(self, interaction: Interaction, keyword: str):
        await interaction.response.defer()
        # 將空白替換成加號
        keyword = keyword.replace(' ', '+')
        if keyword:
            reply_embed = replier.success(value=f'搜尋 {keyword} 的前10筆結果')
            search_result = self.search_in_dmhy(keyword)
            for anime in search_result[:10]:
                reply_embed.add_field(
                    name='',
                    value=f"[{anime['title']}]({anime['link']})\n更新時間: {anime['date']}",
                    inline=False,
                )
            reply_embed.set_footer(text='Source by Dmhy, Developed by poyu39')
            return await interaction.followup.send(embed=reply_embed)
        else:
            reply_embed = replier.error(value='請輸入關鍵字')
            return await interaction.followup.send(embed=reply_embed)
    
    def search_in_dmhy(self, keyword):
        result = []
        raw_feed = feedparser.parse(f'{self.rss_base_url}?keyword={keyword}')
        for entry in raw_feed.entries:
            result.append({
                'title': entry.title,
                'link': entry.link,
                'date': entry.published,
                # 'magnet': entry.enclosures[0].href,
            })
        return result

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Anime(bot), guild=bot.get_guild(CONFIG.GUILD_ID))

import time
from tokenize import Name
import aiohttp
import discord
import importlib
import os
import sys
import json

from discord.ext import commands
from utils import permissions, default, http


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.config()
        self._last_result = None

    def change_config_value(self, value: str, changeto: str):
        """ Change a value from the configs """
        config_name = "config.json"
        with open(config_name, "r") as jsonFile:
            data = json.load(jsonFile)

        data[value] = changeto
        with open(config_name, "w") as jsonFile:
            json.dump(data, jsonFile, indent=2)


    @commands.command()
    @commands.check(permissions.is_owner)
    async def load(self, ctx, name: str):
        """ Loads an extension. """
        try:
            self.bot.load_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(default.traceback_maker(e))
        await ctx.send(f"Loaded extension **{name}.py**")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def unload(self, ctx, name: str):
        """ Unloads an extension. """
        try:
            self.bot.unload_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(default.traceback_maker(e))
        await ctx.send(f"Unloaded extension **{name}.py**")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reload(self, ctx, name: str):
        """ Reloads an extension. """
        try:
            self.bot.reload_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(default.traceback_maker(e))
        await ctx.send(f"Reloaded extension **{name}.py**")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reloadall(self, ctx):
        """ Reloads all extensions. """
        error_collection = []
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                try:
                    self.bot.reload_extension(f"cogs.{name}")
                except Exception as e:
                    error_collection.append(
                        [file, default.traceback_maker(e, advance=False)]
                    )

        if error_collection:
            output = "\n".join([f"**{g[0]}** ```diff\n- {g[1]}```" for g in error_collection])
            return await ctx.send(
                f"Attempted to reload all extensions, was able to reload, "
                f"however the following failed...\n\n{output}"
            )

        await ctx.send("Successfully reloaded all extensions")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reloadutils(self, ctx, name: str):
        """ Reloads a utils module. """
        name_maker = f"utils/{name}.py"
        try:
            module_name = importlib.import_module(f"utils.{name}")
            importlib.reload(module_name)
        except ModuleNotFoundError:
            return await ctx.send(f"Couldn't find module named **{name_maker}**")
        except Exception as e:
            error = default.traceback_maker(e)
            return await ctx.send(f"Module **{name_maker}** returned error and was not reloaded...\n{error}")
        await ctx.send(f"Reloaded module **{name_maker}**")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reboot(self, ctx):
        """ Reboot the bot """
        await ctx.send("Rebooting now...")
        time.sleep(1)
        sys.exit(0)

    @commands.command()
    @commands.check(permissions.is_owner)
    async def dm(self, ctx, user: discord.User, *, message: str):
        """ DM the user of your choice """
        try:
            embed=discord.Embed(title=f"Message from {ctx.author}({ctx.author.id})", description=f"Message: {message}", color=0x2f3136)
            embed.set_thumbnail(url=ctx.author.display_avatar)
            await user.send(embed=embed)
            embed3=discord.Embed(description=f"<:approve:1019330487925362749> Successfully sent DM to {user}", color=0x2ecc71)
            await ctx.send(embed=embed3)
        except discord.Forbidden:
            await ctx.send("Users dms seems to be closed? Maybe they have blocked me.")

    @commands.group()
    @commands.check(permissions.is_owner)
    async def change(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @change.command(name="playing")
    @commands.check(permissions.is_owner)
    async def change_playing(self, ctx, *, playing: str):
        """ Change playing status. """
        status = self.config["status_type"].lower()
        status_type = {"idle": discord.Status.idle, "dnd": discord.Status.dnd}

        activity = self.config["activity_type"].lower()
        activity_type = {"listening": 2, "watching": 3, "competing": 5}

        try:
            await self.bot.change_presence(
                activity=discord.Game(
                    type=activity_type.get(activity, 0), name=playing
                ),
                status=status_type.get(status, discord.Status.online)
            )
            self.change_config_value("playing", playing)
            await ctx.send(f"Successfully changed playing status to **{playing}**")
        except discord.InvalidArgument as err:
            await ctx.send(err)
        except Exception as e:
            await ctx.send(e)

    @change.command(name="username")
    @commands.check(permissions.is_owner)
    async def change_username(self, ctx, *, name: str):
        """ Change username. """
        embed=discord.Embed(description=f"Successfully changed Username. Now using:\n{name}", color=0x2f3136)
        

        try:
            await self.bot.user.edit(username=name)
            await ctx.send(embed=embed)
        except discord.HTTPException as err:
            embed2=discord.Embed(description=f"<a:Error:1004724685470191626>  **{err}**", color=0xFF0000)
            await ctx.send(embed=embed2)

    @change.command(name="nickname")
    @commands.check(permissions.is_owner)
    async def change_nickname(self, ctx, *, name: str = None):
        """ Change nickname. """
        embed=discord.Embed(description=f"Successfully changed Nickname. Now using:\n{name}", color=0x2f3136)
      

        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                await ctx.send(embed=embed)
            else:
                await ctx.send("Successfully removed nickname")
        except Exception as err:
            embed2=discord.Embed(description=f"<a:Error:1004724685470191626>  **{err}**", color=0xFF0000)
        

            await ctx.send(embed=embed2)

    @change.command(name="avatar")
    @commands.check(permissions.is_owner)
    async def change_avatar(self, ctx, url: str = None):
        """ Change avatar. """
        if url is None and len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
        else:
            url = url.strip("<>") if url else None

        try:
            bio = await http.get(url, res_method="read")
            await self.bot.user.edit(avatar=bio)
            embed=discord.Embed(description=f"Successfully changed the avatar.", color=0x2f3136)
            embed.set_image(url=url)
            await ctx.send(embed=embed)
        except aiohttp.InvalidURL:
            await ctx.send("The URL is invalid...")
        except discord.InvalidArgument:
            await ctx.send("This URL does not contain a useable image")
        except discord.HTTPException as err:
            embed2=discord.Embed(description=f"<a:Error:1004724685470191626>   **{err}**", color=0xFF0000)
            await ctx.send(embed=embed2)
        except TypeError:
            await ctx.send("You need to either provide an image URL or upload one with the command")


        @commands.command()
        @commands.check(permissions.is_owner)
        async def stfu(ctx, message):
            












async def setup(bot):
    await bot.add_cog(Admin(bot))

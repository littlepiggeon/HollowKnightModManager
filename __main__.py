import os
import time
from configparser import ConfigParser
from os import getenv
from pathlib import Path

import click
import dotenv

import api

dotenv.load_dotenv(".env")

cp = ConfigParser()
if (cpp := Path.home() / ".hkmm" / "config.ini").is_file():
    cp.read(cpp)


def write_config(section, option, value):
    """
    Write a configuration value to the config file.

    :param section: The section in the config file.
    :param option: The option to set.
    :param value: The value to set for the option.
    """
    if not cp.has_section(section):
        cp.add_section(section)
    cp.set(section, option, str(value))
    cpp.parent.mkdir(parents=True, exist_ok=True)
    cp.write(cpp.open("w"))


def update_time():
    """Update the last update time in the config file."""
    write_config("index", "last_update", time.time())


@click.group("Hollow Knight Mod Manager")
@click.option('--version', '-V', is_flag=True, help='Show the version of the application.')
def cli(version):
    """Hollow Knight Mod Manager CLI."""
    if version:
        click.echo(f"Application Version: {getenv("VERSION")}")
    if not cp.has_option("game", "path"):
        name = input("Please set the game path here: ")
        if os.path.isdir(name):
            write_config("game", "path", name)
        click.echo("Succeeded! You can change your path by using the 'set-game-path' command.")


@cli.command("set-game-path")
@click.argument("path", required=True)
def set_game_path(path):
    """Set the game path."""
    if path:
        if os.path.isdir(path):
            write_config("game", "path", path)
        else:
            click.echo("Please provide a valid game path.")


@cli.command("update", help="Update the mod index.")
def update():
    """Update indexes"""
    api.get_mod_index()
    update_time()


@cli.command("install")
@click.argument("name", required=True)
def install(name):
    """Install a mod."""
    if name:
        if time.time() - float(cp.get("index", "last_update")) > 86400:
            click.echo("Updating mod index...")
            update()
        if not api.install(name, Path(cp.get("game", "path"))):
            click.echo(f"Mod {name} installed successfully.")
        else:
            click.echo(f"Failed to install mod {name}.")
    else:
        click.echo("Please provide a mod name to install.")


@cli.command("list")
def list_mods():
    """List all mods."""
    game_path = Path(cp.get("game", "path"))
    if not game_path.is_dir():
        click.echo("Game path is not set or does not exist.")
        return

    mods = api.get_mod_list(game_path)
    disabled_mods = api.get_disabled_mod_list(game_path)

    if mods:
        click.echo("Available mods:")
        for mod in mods:
            click.echo(f"- {mod}")
    else:
        click.echo("No mods found.")

    if disabled_mods:
        click.echo("\nDisabled mods:")
        for mod in disabled_mods:
            click.echo(f"* {mod}")
    else:
        click.echo("No disabled mods found.")


@cli.command("disable")
@click.argument("name", required=True)
def disable(name):
    """Disable a mod."""
    if name:
        if api.disable(name, Path(cp.get("game", "path"))):
            click.echo(f"Mod {name} disable successfully.")
        else:
            click.echo(f"Failed to disable mod {name}.")
    else:
        click.echo("Please provide a mod name to disable.")


@cli.command("able")
@click.argument("name", required=True)
def able(name):
    """Be able a mod."""
    if name:
        if not api.able(name, Path(cp.get("game", "path"))):
            click.echo(f"Mod \"{name}\" be able successfully.")
        else:
            click.echo(f"Failed to be able mod \"{name}\".")
    else:
        click.echo("Please provide a mod name to be able.")


@cli.command("uninstall")
@click.argument("name", required=True)
def uninstall(name):
    """Uninstall a mod."""
    if name:
        if not api.uninstall(name, Path(cp.get("game", "path"))):
            click.echo(f"Mod {name} uninstalled successfully.")
        else:
            click.echo(f"Failed to uninstall mod {name}.")
    else:
        click.echo("Please provide a mod name to uninstall.")


if __name__ == '__main__':
    cli()

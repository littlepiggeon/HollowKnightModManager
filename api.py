import os.path
from pathlib import Path
from shutil import copy2, copytree
from tempfile import TemporaryFile
from urllib.parse import urlparse
from zipfile import ZipFile

import click
import requests
import urllib3
from lxml import etree

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def download_file(url, local_filename) -> int:
    """
    Downloads a file from the specified URL and saves it to the local filesystem.

    :param url: The URL of the file to download.
    :param local_filename: The local path where the file should be saved.
    :return: 0 if the download was successful, 1 if it failed.
    """
    click.echo(f"Downloading \"{url}\"...")
    with requests.get(url, stream=True, verify=False) as r:
        if r.ok:
            size = int(r.headers.get("Content-Length"))
            d = 0
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(256):
                    d += f.write(chunk)
                    click.echo(f"{(p := d / size) * 100:3.2f}% [{int(p * 50) * '=':50}]({d}/{size})\r", nl=False)
            click.echo()
            return 0
        else:
            click.echo(f"Failed! {r.status_code} {r.reason}")
            return 1


def polish_index(file: Path, table: dict[int, bytes], ):
    with TemporaryFile('wb+', dir=Path.home() / ".hkmm") as tempfile:
        with open(file, 'rb') as f:
            lineno = 1
            while c := f.readline():
                if not (lineno in table):
                    tempfile.write(c)
                else:
                    tempfile.write(table[lineno])
                lineno += 1
        tempfile.seek(0)
        with open(file, 'wb') as f:
            f.write(tempfile.read())


def install(name: str, game_path: Path, is_dependency=False) -> int:
    """
    Install a mod by name.

    :param name: The name of the mod to install.
    :param game_path: The _to to the game directory.
    :param is_dependency: Whether the mod is a dependency.
    :return: 0 if the installation was successful, 1 if the mod was not
    """
    for mod in etree.parse(Path.home() / ".hkmm" / "ModLinks.xml").findall("Manifest"):
        if mod.find("Name").text == name:
            break
    else:
        click.echo("Mod not found")
        return 1

    click.echo(f"Installing mod: {name}" if not is_dependency else f"Installing dependency: {name}")
    (Path.home() / ".hkmm" / "downloads").mkdir(parents=True, exist_ok=True)
    if not download_file((link := mod.find("Link").text.strip()),
                         (_from := Path.home() / ".hkmm" / "downloads" / (
                                 filename := os.path.basename(urlparse(link).path)))):
        for dependency in mod.findall("Dependency"):
            if not install(dependency.text, game_path, is_dependency=True):
                click.echo(f"Failed to install dependency: {dependency.text}")
                return 1
    else:
        click.echo(f"Failed to download mod '{name}'.")
        return 1

    if filename.upper().endswith(".ZIP"):
        with ZipFile(_from, 'r') as zip_ref:
            (game_path / "hollow_knight_Data" / "Managed" / "Mods" / name).mkdir(parents=True, exist_ok=True)
            zip_ref.extractall(game_path / "hollow_knight_Data" / "Managed" / "Mods" / name)
    else:
        (_to := game_path / "hollow_knight_Data" / "Managed" / "Mods" / name).mkdir(parents=True, exist_ok=True)
        copy2(Path.home() / ".hkmm" / "downloads" / filename, _to)

    click.echo(f"mod \"{name}\" installed successfully.")
    return 0


def install_api(game_path: Path) -> int:
    """
    Install the modding API.

    :param game_path: The path to the game directory.
    :return: 0 if the installation was successful, 1 if it failed.
    """
    click.echo("Installing Modding API...")
    (Path.home() / ".hkmm" / "downloads").mkdir(parents=True, exist_ok=True)
    if not download_file("https://github.com/hk-modding/modlinks/raw/refs/heads/main/ApiLinks.xml",
                         (links := Path.home() / ".hkmm" / "ApiLinks.xml")):
        polish_index(links, {2: b"<ApiLinks", 5: b'>'})
        if not download_file((url := (tree := etree.parse(links)).find("Windows").text),
                             (zip_path := Path.home() / ".hkmm" / "downloads" / os.path.basename(urlparse(url).path))):
            for file in tree.findall("File"):
                zip_f = ZipFile(zip_path, 'r')
                with zip_f.open(file.text, 'r') as source:
                    with open(game_path / "hollow_knight_Data" / "Managed" / file.text, 'wb') as target:
                        target.write(source.read())
            click.echo("Modding API installed successfully.")
            return 0
        else:
            click.echo("Failed to download Modding API.")
            return 1
    else:
        click.echo("Failed to download Modding API links.")
        return 1


def disable(name: str, game_path: Path) -> int:
    """
    Disable a mod by name.

    :param name: The name of the mod to disable.
    :param game_path: The path to the game directory.
    :return: 0 if the disabling was successful, 1 if the mod was not found.
    """
    mod_dir = game_path / "hollow_knight_Data" / "Managed" / "Mods"
    mod_path = mod_dir / name
    if mod_path.is_dir():
        copytree(mod_path, mod_dir / "Disabled" / name, dirs_exist_ok=True)

        for item in mod_path.iterdir():
            if item.is_dir():
                item.rmdir()
            else:
                item.unlink()
        mod_path.rmdir()

        click.echo(f"Mod \"{name}\" disabled successfully.")
        return 0
    else:
        click.echo(f"Mod \"{name}\" not found.")
        return 1


def able(name: str, game_path: Path) -> int:
    """
    Be able a mod by name.

    :param name: The name of the mod to be able.
    :param game_path: The path to the game directory.
    :return: 0 if it was successful, 1 if failed.
    """
    mod_dir = game_path / "hollow_knight_Data" / "Managed" / "Mods"
    mod_path = mod_dir / "Disabled" / name
    if mod_path.is_dir():
        copytree(mod_path, mod_dir / name, dirs_exist_ok=True)

        for item in mod_path.iterdir():
            if item.is_dir():
                item.rmdir()
            else:
                item.unlink()
        mod_path.rmdir()
        return 0
    else:
        click.echo(f"Mod \"{name}\" not found.")
        return 1


def uninstall(name: str, game_path: Path) -> int:
    """
    Uninstall a mod by name.

    :param name: The name of the mod to uninstall.
    :param game_path: The path to the game directory.
    :return: 0 if the uninstallation was successful, 1 if the mod was not found.
    """
    mod_dir = game_path / "hollow_knight_Data" / "Managed" / "Mods"
    if not (mod_path := mod_dir / name).is_dir():
        mod_path = mod_dir / "Disabled" / name
    elif not mod_path.is_dir():
        click.echo(f"Mod \"{name}\" not found.")
        return 1
    for item in mod_path.iterdir():
        if item.is_dir():
            item.rmdir()
        else:
            item.unlink()
    mod_path.rmdir()
    click.echo(f"Mod \"{name}\" uninstalled successfully.")
    return 0


def get_mod_index():
    """
    Fetches the mod index from the official URL.
    """
    download_file("https://github.com/hk-modding/modlinks/raw/refs/heads/main/ModLinks.xml",
                  (links := Path.home() / ".hkmm" / "ModLinks.xml"))
    polish_index(links, {2: b"<ModLinks", 5: b'>'})


def get_mod_list(game_path: Path) -> list[str]:
    """Get list of all mods located"""
    moddir = game_path / "hollow_knight_Data" / "Managed" / "Mods"
    return [i for i in os.listdir(moddir) if i != "Disabled" and (moddir / i).is_dir()]


def get_disabled_mod_list(game_path: Path) -> list[str]:
    """Get list of all mods located"""
    moddir = game_path / "hollow_knight_Data" / "Managed" / "Mods" / "Disabled"
    return [i for i in os.listdir(moddir) if (moddir / i).is_dir()]


def upgrade(name: str, game_path: Path) -> int:
    """
    Upgrade a mod by name.

    :param name: The name of the mod to upgrade.
    :param game_path: The path to the game directory.
    :return: 0 if the upgrade was successful, 1 if the mod was not found.
    """
    if uninstall(name, game_path):
        return 1
    if install(name, game_path):
        return 1
    return 0

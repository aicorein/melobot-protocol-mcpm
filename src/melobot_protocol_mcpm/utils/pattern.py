import re
import sys
from functools import lru_cache


class RegexPatternGroup:
    line = re.compile(
        r"\[(?P<hour>\d+):(?P<min>\d+):(?P<sec>\d+)]"
        r" \[(?P<thread>[^]]+)/(?P<logging>[^]/]+)]"
        r": (?P<content>.*)"
    )
    msg = [re.compile(r"(\[Not Secure] )?<(?P<name>[^>]+)> (?P<message>.*)")]
    player_name = re.compile(r"[a-zA-Z0-9_]{3,16}")
    player_joined = re.compile(
        r"(?P<name>[^\[]+)\[(.*?)] logged in with entity id \d+ at \(.+\)"
    )
    player_left = re.compile(r"(?P<name>[^ ]+) left the game")
    server_version = re.compile(r"Starting minecraft server version (?P<version>.+)")
    server_address = re.compile(r"Starting Minecraft server on (?P<ip>\S+):(?P<port>\d+)")
    server_startup_done = re.compile(
        r'Done \([0-9.]+s\)! For help, type "help"( or "\?")?'
    )
    rcon_started = re.compile(r"RCON running on [\w.]+:\d+")


@lru_cache
def search(
    pattern: re.Pattern, text: str, pos: int = 0, endpos: int = sys.maxsize
) -> re.Match | None:
    return pattern.search(text, pos, endpos)


@lru_cache
def fullmatch(
    pattern: re.Pattern, text: str, pos: int = 0, endpos: int = sys.maxsize
) -> re.Match | None:
    return pattern.fullmatch(text, pos, endpos)

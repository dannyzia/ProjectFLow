from collections.abc import Callable
from typing import Any

from project_flow.generators.antigravity import generate as generate_antigravity
from project_flow.generators.claude import generate as generate_claude
from project_flow.generators.cline import generate as generate_cline
from project_flow.generators.cursor import generate as generate_cursor
from project_flow.generators.kilo import generate as generate_kilo
from project_flow.generators.void_gen import generate as generate_void
from project_flow.generators.vscode import generate as generate_vscode
from project_flow.generators.windsurf import generate as generate_windsurf
from project_flow.generators.zed import generate as generate_zed

_GENERATORS: dict[str, Callable[..., list[Any]]] = {
    "vscode": generate_vscode,
    "kilo": generate_kilo,
    "cursor": generate_cursor,
    "windsurf": generate_windsurf,
    "zed": generate_zed,
    "void": generate_void,
    "cline": generate_cline,
    "claude": generate_claude,
    "antigravity": generate_antigravity,
}


def get_all_generators() -> dict[str, Callable[..., list[Any]]]:
    return dict(_GENERATORS)

#!/usr/bin/env python3

import itertools
from pathlib import Path
from typing import Annotated

import typer
from rich import print
from rich.console import Console
from rich.progress import track

from . import api_change

app = typer.Typer(add_completion=False)
stderr = Console(stderr=True)
console = Console()


@app.command()
def migrate(
    paths: Annotated[
        list[Path],
        typer.Argument(
            help="Directory or text files to update (e.g., .py scripts, .ipynb notebooks, .md files). Non-text files will be skipped."
        ),
    ],
    backup_dir: Annotated[
        Path,
        typer.Option(
            help="Path where we will create a directory to copy existing paths into. Must not exist."
        ),
    ] = None,
):
    """Migrate from plenoptic 1.x to 2.0.

    Rewrites all occurrences of old API names to their new equivalents, in-place, for
    each file passed as a command-line argument. After rewriting, reports any deprecated
    usages, which must be updated manually.

    This tool only changes fully resolvable plenoptic objects. For example, it will
    replace `plenoptic.synth.Metamer` with `plenoptic.Metamer`, but will not
    touch `from plenoptic.synthesize import Metamer`.

    We overwrite all files in-place. We therefore recommend that you track your files
    using git or make use of the `--backup-dir` option to create a backup. You are then
    encouraged to double-check all the changes! This tool worked for the developers of
    plenoptic but has not been tested on a wide variety of setups.

    Module aliases
    --------------
    The tool handles the standard module aliases used in plenoptic's tutorials
    and examples:

        import plenoptic as po
        import plenoptic.synthesize as synth
        import plenoptic.simulate as simul

    Non-standard aliases (e.g. `import plenoptic as plen`) are not handled and
    must be updated manually.

    """
    if not backup_dir or backup_dir == Path("."):
        backup = typer.confirm(
            "Are you sure you wish to proceed without making a backup?"
        )
        if not backup:
            raise typer.Abort()
    else:
        if backup_dir.exists():
            raise typer.BadParameter("backup directory must not already exist!")
        backup_dir.mkdir()
        print(f"Copying all specified files into [blue]{backup_dir}[blue]")
        for p in paths:
            p.copy_into(backup_dir)

    deprecated = {}
    UPDATED_API = api_change.API_CHANGE
    UPDATED_API.update(api_change.SYNTH_PLOT_FUNCS)
    UPDATED_API.update(api_change.PLOT_FUNCS)

    # check all possible combinations of the module aliases
    module_aliases = []
    for i in range(1, len(api_change.MODULE_ALIASES) + 1):
        for mods in itertools.combinations(api_change.MODULE_ALIASES, i):
            module_aliases.append({k: api_change.MODULE_ALIASES[k] for k in mods})

    iter_paths = []
    for p in paths:
        if p.is_dir():
            iter_paths.extend(list(p.rglob("**")))
        else:
            iter_paths.append(p)

    for p in track(iter_paths):
        if p.is_dir():
            continue
        try:
            file_contents = p.read_text()
        except Exception as e:
            msg = f"Unable to read text from [blue]{p}[/blue], with following error, skipping."
            err_msg = f"{type(e).__name__}: {e}"
            stderr.print(f"\n[bold red]WARNING:[/bold red] {msg}\n    {err_msg}")
            continue
        for old_func, new_func in UPDATED_API.items():
            file_contents = file_contents.replace(old_func, new_func)
            for aliases in module_aliases:
                old_func_check = old_func
                new_func_check = new_func
                for mod, alias in aliases.items():
                    old_func_check = old_func_check.replace(mod, alias)
                    new_func_check = new_func_check.replace(mod, alias)
                    file_contents = file_contents.replace(
                        old_func_check, new_func_check
                    )
        for dep_func in api_change.DEPRECATED:
            if dep_func in file_contents:
                if dep_func in deprecated:
                    deprecated[dep_func].append(str(p))
                else:
                    deprecated[dep_func] = [str(p)]
            for aliases in module_aliases:
                dep_func_check = dep_func
                for mod, alias in aliases.items():
                    dep_func_check = dep_func_check.replace(mod, alias)
                    if dep_func_check in file_contents:
                        if dep_func_check in deprecated:
                            deprecated[dep_func_check].append(str(p))
                        else:
                            deprecated[dep_func_check] = [str(p)]
        p.write_text(file_contents)

    if deprecated:
        print("The following deprecated functions were found:")
        for dep_func, dep_files in deprecated.items():
            print(f"\t{dep_func}: {dep_files}")

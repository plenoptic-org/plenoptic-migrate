#!/usr/bin/env python3

import typer
from plenoptic import _api_change
import itertools
import pathlib

app = typer.Typer()


@app.command()
def migrate(paths: list[str]):
    deprecated = {}
    UPDATED_API = _api_change.API_CHANGE
    UPDATED_API.update(_api_change.SYNTH_PLOT_FUNCS)
    UPDATED_API.update(_api_change.PLOT_FUNCS)

    # check all possible combinations of the module aliases
    module_aliases = []
    for i in range(1, len(_api_change.MODULE_ALIASES)+1):
        for mods in itertools.combinations(_api_change.MODULE_ALIASES, i):
            module_aliases.append({k: _api_change.MODULE_ALIASES[k] for k in mods})

    for p in paths:
        p = pathlib.Path(p)
        file_contents = p.read_text()
        for old_func, new_func in UPDATED_API.items():
            file_contents = file_contents.replace(old_func, new_func)
            for aliases in module_aliases:
                old_func_check = old_func
                new_func_check = new_func
                for mod, alias in aliases.items():
                    old_func_check = old_func_check.replace(mod, alias)
                    new_func_check = new_func_check.replace(mod, alias)
                    file_contents = file_contents.replace(old_func_check, new_func_check)
        for dep_func in _api_change.DEPRECATED:
            if dep_func in file_contents:
                if dep_func in deprecated:
                    deprecated[dep_func].append(p)
                else:
                    deprecated[dep_func] = [p]
            for aliases in module_aliases:
                dep_func_check = dep_func
                for mod, alias in aliases.items():
                    dep_func_check = dep_func_check.replace(mod, alias)
                    if dep_func_check in file_contents:
                        if dep_func_check in deprecated:
                            deprecated[dep_func_check].append(p)
                        else:
                            deprecated[dep_func_check] = [p]
        p.write_text(file_contents)

    if deprecated:
        print("The following deprecated functions were found:")
        for dep_func, dep_files in deprecated.items():
            print(f"\t{dep_func}: {dep_files}")

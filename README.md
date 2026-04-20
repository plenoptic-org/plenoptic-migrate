# `plenoptic-migrate`

Migrate from plenoptic 1.x to 2.0.

Rewrites all occurrences of old API names to their new equivalents, in-place, for
each file passed as a command-line argument. After rewriting, reports any deprecated
usages that could not be automatically resolved and must be updated manually.

This tool only changes fully resolvable plenoptic objects. For example, it will
replace `plenoptic.synth.Metamer` with `plenoptic.Metamer`, but will not
touch `from plenoptic.synthesize import Metamer`.

We overwrite all files in-place. We therefore recommend that you track your files
using git or make use of the --backup-dir option to create a backup. You are then
encouraged to double-check all the changes! This tool worked for the developers of
plenoptic but has not been tested on a wide variety of setups.

Module aliases
--------------
The tool handles the standard module aliases used in plenoptic&#x27;s tutorials
and examples:

    import plenoptic as po
    import plenoptic.synthesize as synth
    import plenoptic.simulate as simul

Non-standard aliases (e.g. `import plenoptic as plen`) are not handled and
must be updated manually.

**Usage**:

```console
$ plenoptic-migrate [OPTIONS] PATHS...
```

**Arguments**:

* `PATHS...`: Directory or text files to update (e.g., .py scripts, .ipynb notebooks, .md files). Non-text files will be skipped.  [required]

**Options**:

* `--backup-dir PATH`: Path where we will create a directory to copy existing paths into. Must not exist.
* `--help`: Show this message and exit.

#!/usr/bin/env python3
import os
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
BUILD_SH = REPO_ROOT / "build.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


class BuildShTests(unittest.TestCase):
    def test_build_script_marks_wrapper_for_clusterfuzz_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fuzzers = root / "fuzzers"
            fuzzers.mkdir()
            (fuzzers / "sample_fuzzer.py").write_text("print('stub')\n", encoding="utf-8")

            out_dir = root / "out"
            out_dir.mkdir()
            bin_dir = root / "bin"
            bin_dir.mkdir()

            _write_executable(
                bin_dir / "python3",
                "#!/bin/sh\nexit 0\n",
            )
            _write_executable(
                bin_dir / "pyinstaller",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import os
                    import stat
                    import sys
                    from pathlib import Path

                    args = sys.argv[1:]
                    distpath = Path(args[args.index("--distpath") + 1])
                    name = args[args.index("--name") + 1]
                    target = distpath / name
                    target.write_text("#!/bin/sh\\nexit 0\\n", encoding="utf-8")
                    target.chmod(target.stat().st_mode | stat.S_IEXEC)
                    """
                ),
            )

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            env["SRC"] = str(root)
            env["OUT"] = str(out_dir)

            subprocess.run(
                ["bash", str(BUILD_SH)],
                check=True,
                cwd=REPO_ROOT,
                env=env,
            )

            wrapper = (out_dir / "sample_fuzzer").read_text(encoding="utf-8")
            self.assertIn("# LLVMFuzzerTestOneInput for fuzzer detection.", wrapper)
            self.assertIn('"$this_dir/sample_fuzzer.pkg" "$@"', wrapper)


if __name__ == "__main__":
    unittest.main()

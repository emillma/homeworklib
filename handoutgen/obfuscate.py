from pathlib import Path
import shutil


def obfuscate_solution(folder: Path):
    from pyarmor.pyarmor import main as call_pyarmor
    folder_tmp = folder.rename(f"{folder}_tmp")
    platforms = ["windows.x86",
                 "windows.x86_64",
                 "darwin.x86_64",
                 "darwin.arm64",
                 "linux.x86",
                 "linux.x86_64",
                 #  "linux.arm",
                 #  "linux.aarch32",
                 #  "linux.aarch64",
                 #  "vs2015.x86",
                 #  "vs2015.x86_64",
                 #  "linux.armv6",
                 #  "linux.armv7",
                 #  "android.aarch64",
                 #  "android.armv7",
                 #  "android.x86",
                 #  "android.x86_64",
                 #  "uclibc.armv7",
                 #  "linux.ppc64",
                 #  "freebsd.x86_64",
                 #  "musl.x86_64",
                 #  "musl.arm",
                 #  "musl.mips32",
                 #  "linux.mips64",
                 #  "linux.mips64el",
                 #  "poky.x86"
                 ]
    platcmd = [item for plat in platforms for item in ['--platform', plat]]
    call_pyarmor(['obfuscate'] + platcmd
                 + ['--output', str(Path(folder)),
                    str(Path(folder_tmp).joinpath('__init__.py'))])
    shutil.rmtree(folder_tmp)

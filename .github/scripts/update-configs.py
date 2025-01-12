#!/usr/bin/env python3
import json
import subprocess
import os
from urllib.request import urlopen, urlretrieve


def bash(command: str) -> str:
    output = subprocess.check_output(command, shell=True, text=True).strip()
    print(output, flush=True)
    return output


if __name__ == "__main__":
    # Read json from kernel.org
    with urlopen("https://www.kernel.org/releases.json") as response:
        data = json.loads(response.read())

    # Get the latest stable version
    latest_version = "v" + data["latest_stable"]["version"]
    latest_source  = data["releases"][1]["source"]
    # Git clone the latest stable version
    bash(f"git clone --depth=1 --branch={latest_version} https://git.kernel.org/pub/scm/linux/kernel/git/"
         f"stable/linux.git")

    # pull fresh arch linux config to use as base.conf
    urlretrieve(url="https://raw.githubusercontent.com/archlinux/svntogit-packages/packages/linux/trunk/config",
                filename="base.conf")

    # duplicate base.conf to temp_combined.conf
    with open("base.conf", "r") as base:
        with open("temp_combined.conf", "w") as combined:
            combined.write(base.read())

    # append all overlays to combined.conf
    for file in os.listdir("kernel-conf-overlays"):
        if file != "README.md":
            with open(f"kernel-conf-overlays/{file}", "r") as overlay:
                with open("temp_combined.conf", "a") as combined:
                    combined.write("\n" + overlay.read())

    # Copy combined config into local stable repo
    bash("cp temp_combined.conf linux/.config")

    # Update config
    bash("cd linux && make olddefconfig")

    # Copy updated combined config back to repo
    bash("cp linux/.config ./combined-kernel.conf")

    # Update bash script
    with open("build.sh", "r") as file:
        build_script = file.readlines()
    build_script[2] = f"KERNEL_VERSION={latest_version[1:]}\n"
    build_script[3] = f"KERNEL_SOURCE_URL={latest_source[0:]}\n"
    with open("build.sh", "w") as file:
        file.writelines(build_script)

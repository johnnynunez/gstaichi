# -*- coding: utf-8 -*-

# -- stdlib --
import os
import platform

# -- third party --
# -- own --
from .dep import download_dep
from .misc import banner, get_cache_home, path_prepend
from .python import path_prepend


VULKAN_VERSION = "1.4.304.1"


# -- code --
@banner(f"Setup Vulkan {VULKAN_VERSION}")
def setup_vulkan():
    u = platform.uname()
    if u.system == "Linux" and u.machine == "x86_64":
        url = f"https://sdk.lunarg.com/sdk/download/1.4.304.1/linux/vulkansdk-linux-x86_64-{VULKAN_VERSION}.tar.xz"
        prefix = get_cache_home() / f"vulkan-{VULKAN_VERSION}"
        download_dep(url, prefix, strip=1)
        sdk = prefix / "x86_64"
        os.environ["VULKAN_SDK"] = str(sdk)
        path_prepend("PATH", sdk / "bin")
        path_prepend("LD_LIBRARY_PATH", sdk / "lib")
        os.environ["VK_LAYER_PATH"] = str(sdk / "etc" / "vulkan" / "explicit_layer.d")
    elif u.system == "Linux" and u.machine in ("arm64", "aarch64"):
        url = (
            f"https://github.com/johnnynunez/vulkan-sdk-arm/releases/download/{VULKAN_VERSION}/"
            f"vulkansdk-linux-arm64-ubuntu-24.04-arm-{VULKAN_VERSION}.zip"
        )
        prefix = get_cache_home() / f"vulkan-{VULKAN_VERSION}"
        download_dep(url, prefix, strip=1)
        sdk = prefix / "arm64"
        os.environ["VULKAN_SDK"] = str(sdk)
        path_prepend("PATH", sdk / "bin")
        path_prepend("LD_LIBRARY_PATH", sdk / "lib")
        os.environ["VK_LAYER_PATH"] = str(sdk / "etc" / "vulkan" / "explicit_layer.d")
    # elif (u.system, u.machine) == ("Darwin", "arm64"):
    # elif (u.system, u.machine) == ("Darwin", "x86_64"):
    elif (u.system, u.machine) == ("Windows", "AMD64"):
        url = f"https://sdk.lunarg.com/sdk/download/{VULKAN_VERSION}/windows/VulkanSDK-{VULKAN_VERSION}-Installer.exe"
        prefix = get_cache_home() / f"vulkan-{VULKAN_VERSION}"
        download_dep(
            url,
            prefix,
            elevate=True,
            args=[
                "--accept-licenses",
                "--default-answer",
                "--confirm-command",
                "--root",
                prefix,
                "install",
                "com.lunarg.vulkan.sdl2",
                "com.lunarg.vulkan.glm",
                "com.lunarg.vulkan.volk",
                "com.lunarg.vulkan.vma",
                # 'com.lunarg.vulkan.debug',
            ],
        )
        os.environ["VULKAN_SDK"] = str(prefix)
        os.environ["VK_SDK_PATH"] = str(prefix)
        os.environ["VK_LAYER_PATH"] = str(prefix / "Bin")
        path_prepend("PATH", prefix / "Bin")
    else:
        return

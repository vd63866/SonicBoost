import re
import shutil
import subprocess


class AudioController:

    MAX_VOLUME = 125

    def __init__(self):
        if not shutil.which("wpctl"):
            raise RuntimeError("wpctl is not installed")

    def _run(self, *args):
        return subprocess.run(
            ["wpctl", *args],
            capture_output=True,
            text=True,
            timeout=3,
            check=True
        )

    def get_volume(self):
        result = self._run(
            "get-volume",
            "@DEFAULT_SINK@"
        )

        match = re.search(
            r"Volume:\s+([0-9.]+)",
            result.stdout
        )

        if not match:
            raise RuntimeError("Could not read audio volume")

        volume = round(float(match.group(1)) * 100)
        muted = "[MUTED]" in result.stdout

        return volume, muted

    def set_volume(self, volume):
        volume = max(0, min(self.MAX_VOLUME, int(volume)))

        self._run(
            "set-volume",
            "@DEFAULT_SINK@",
            str(volume / 100),
            "--limit",
            str(self.MAX_VOLUME / 100)
        )

    def toggle_mute(self):
        self._run(
            "set-mute",
            "@DEFAULT_SINK@",
            "toggle"
        )

    def reset_volume(self):
        self.set_volume(100)

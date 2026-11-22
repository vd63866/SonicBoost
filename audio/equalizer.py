
import cmath
import math
import subprocess
import time
from pathlib import Path


BANDS = [
    ("31 Hz", 31.25, "band31"),
    ("62 Hz", 62.5, "band62"),
    ("125 Hz", 125.0, "band125"),
    ("250 Hz", 250.0, "band250"),
    ("500 Hz", 500.0, "band500"),
    ("1 kHz", 1000.0, "band1k"),
    ("2 kHz", 2000.0, "band2k"),
    ("4 kHz", 4000.0, "band4k"),
    ("8 kHz", 8000.0, "band8k"),
    ("16 kHz", 16000.0, "band16k"),
]


class PipeWireEqualizer:
    MIN_GAIN = -6.0
    MAX_GAIN = 6.0
    SAMPLE_RATE = 48000
    Q = 1.414

    SINK_NAME = "effect_input.sonicboost"
    OUTPUT_NAME = "effect_output.sonicboost"

    def __init__(self):
        self.project_dir = Path(__file__).resolve().parents[1]

        self.project_config = (
            self.project_dir / "pipewire" / "sonicboost-eq.conf"
        )

        self.user_config = (
            Path.home()
            / ".config/pipewire/pipewire.conf.d"
            / "90-sonicboost-eq.conf"
        )

        self.backup_config = self.user_config.with_name(
            self.user_config.name + ".original"
        )

    @classmethod
    def validate_gains(cls, gains):
        if len(gains) != 10:
            raise ValueError("Exactly 10 equalizer values are required")

        values = []

        for gain in gains:
            value = float(gain)

            if not math.isfinite(value):
                raise ValueError("Gain must be a finite number")

            if not cls.MIN_GAIN <= value <= cls.MAX_GAIN:
                raise ValueError("Gain must be between -6 and +6 dB")

            values.append(value)

        return values

    @classmethod
    def calculate_preamp(cls, gains):
        gains = cls.validate_gains(gains)

        frequencies = [
            20 * (20000 / 20) ** (i / 511)
            for i in range(512)
        ]

        peak_db = 0.0

        for frequency in frequencies:
            omega = 2 * math.pi * frequency / cls.SAMPLE_RATE
            z1 = cmath.exp(-1j * omega)
            z2 = z1 * z1

            total_db = 0.0

            for gain, (_, center, _) in zip(gains, BANDS):
                if gain == 0:
                    continue

                A = 10 ** (gain / 40)
                w0 = 2 * math.pi * center / cls.SAMPLE_RATE
                alpha = math.sin(w0) / (2 * cls.Q)
                cosine = math.cos(w0)

                b0 = 1 + alpha * A
                b1 = -2 * cosine
                b2 = 1 - alpha * A

                a0 = 1 + alpha / A
                a1 = -2 * cosine
                a2 = 1 - alpha / A

                numerator = b0 + b1 * z1 + b2 * z2
                denominator = a0 + a1 * z1 + a2 * z2

                magnitude = abs(numerator / denominator)
                total_db += 20 * math.log10(max(magnitude, 1e-12))

            peak_db = max(peak_db, total_db)

        # Estimated headroom with approximately 1 dB safety margin.
        return (
            peak_db + 1.0
            if peak_db > 0.1
            else 0.0
        )

    @classmethod
    def render_config(cls, gains):
        gains = cls.validate_gains(gains)

        compensation = cls.calculate_preamp(gains)
        preamp_multiplier = 10 ** (-compensation / 20)

        nodes = [
            f"""
            {{
                type = builtin
                name = preamp
                label = linear
                control = {{
                    "Mult" = {preamp_multiplier:.8f}
                    "Add" = 0.0
                }}
            }}
            """
        ]

        for gain, (_, frequency, name) in zip(gains, BANDS):
            nodes.append(
                f"""
                {{
                    type = builtin
                    name = {name}
                    label = bq_peaking
                    control = {{
                        "Freq" = {frequency}
                        "Q" = {cls.Q}
                        "Gain" = {gain}
                    }}
                }}
                """
            )

        chain = ["preamp"] + [band[2] for band in BANDS]

        links = [
            f'{{ output = "{source}:Out" input = "{destination}:In" }}'
            for source, destination in zip(chain, chain[1:])
        ]

        return f"""
context.modules = [
{{
    name = libpipewire-module-filter-chain
    flags = [ ifexists nofail ]

    args = {{
        node.description = "SonicBoost Equalizer"
        media.name = "SonicBoost Equalizer"

        filter.graph = {{
            nodes = [
                {" ".join(nodes)}
            ]

            links = [
                {" ".join(links)}
            ]
        }}

        audio.channels = 2
        audio.position = [ FL FR ]

        capture.props = {{
            node.name = "{cls.SINK_NAME}"
            media.class = Audio/Sink
        }}

        playback.props = {{
            node.name = "{cls.OUTPUT_NAME}"
            node.passive = true
        }}
    }}
}}
]
"""

    @staticmethod
    def run_command(*args, timeout=10):
        try:
            return subprocess.run(
                list(args),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            detail = error.stderr or error.stdout or str(error)
            raise RuntimeError(detail.strip()) from error

    def get_sinks(self):
        output = self.run_command(
            "pactl", "list", "short", "sinks"
        ).stdout

        return {
            fields[1]: fields[0]
            for line in output.splitlines()
            if len(fields := line.split()) >= 2
        }

    def get_sink_inputs(self):
        output = self.run_command(
            "pactl", "list", "short", "sink-inputs"
        ).stdout

        return [
            line.split()
            for line in output.splitlines()
            if len(line.split()) >= 3
        ]

    def find_physical_sink(self):
        sinks = self.get_sinks()

        # Find the current physical destination of
        # the SonicBoost filter-chain output stream.
        for fields in self.get_sink_inputs():
            if fields[2] == "-":
                for name, sink_id in sinks.items():
                    if (
                        sink_id == fields[1]
                        and name != self.SINK_NAME
                    ):
                        return name

        # Fall back to the default physical sink.
        default = self.run_command(
            "pactl", "get-default-sink"
        ).stdout.strip()

        if default in sinks and default != self.SINK_NAME:
            return default

        # Last resort: find an available ALSA output.
        for name in sinks:
            if (
                name.startswith("alsa_output.")
                and name != self.SINK_NAME
            ):
                return name

        raise RuntimeError("Could not identify physical audio output")

    def wait_for_sinks(self, physical_sink, timeout=15):
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            try:
                sinks = self.get_sinks()

                if (
                    self.SINK_NAME in sinks
                    and physical_sink in sinks
                ):
                    return sinks

            except (RuntimeError, OSError, subprocess.SubprocessError):
                pass

            time.sleep(0.5)

        raise RuntimeError(
            "SonicBoost or the physical speaker did not reappear."
        )

    def write_config(self, gains):
        content = self.render_config(gains)

        self.project_config.parent.mkdir(
            parents=True, exist_ok=True
        )

        self.user_config.parent.mkdir(
            parents=True, exist_ok=True
        )

        # Preserve the original user configuration once.
        if (
            self.user_config.exists()
            and not self.backup_config.exists()
        ):
            self.backup_config.write_bytes(
                self.user_config.read_bytes()
            )

        # Write atomically to both locations.
        for path in (self.project_config, self.user_config):
            temporary = path.with_suffix(
                path.suffix + ".tmp"
            )

            temporary.write_text(
                content,
                encoding="utf-8"
            )

            temporary.replace(path)

        return content

    def restore_original_config(self):
        if self.backup_config.exists():
            self.user_config.write_bytes(
                self.backup_config.read_bytes()
            )
        else:
            # Remove the newly-created file if no original existed.
            self.user_config.unlink(missing_ok=True)

    def apply(self, gains):
        gains = self.validate_gains(gains)

        status = self.run_command(
            "systemctl",
            "--user",
            "is-active",
            "pipewire.service"
        ).stdout.strip()

        if status != "active":
            raise RuntimeError("PipeWire is not running")

        physical_sink = self.find_physical_sink()

        previous_default = self.run_command(
            "pactl", "get-default-sink"
        ).stdout.strip()

        self.write_config(gains)

        try:
            # Reload the user-level filter-chain configuration.
            self.run_command(
                "systemctl",
                "--user",
                "restart",
                "pipewire.service",
                timeout=30
            )

            sinks = self.wait_for_sinks(physical_sink)

            eq_id = sinks[self.SINK_NAME]
            physical_id = sinks[physical_sink]

            self.run_command(
                "pactl",
                "set-default-sink",
                self.SINK_NAME
            )

            moved = 0

            for fields in self.get_sink_inputs():
                stream_id, current_sink, client_id = fields[:3]

                # Filter-chain output goes to physical speakers.
                # Application streams go into SonicBoost.
                if client_id == "-":
                    target = physical_sink
                    target_id = physical_id
                else:
                    target = self.SINK_NAME
                    target_id = eq_id

                if current_sink != target_id:
                    self.run_command(
                        "pactl",
                        "move-sink-input",
                        stream_id,
                        target
                    )

                    if client_id != "-":
                        moved += 1

            return (
                "Equalizer applied successfully. "
                f"{moved} application stream(s) routed."
            )

        except Exception as error:
            # Attempt to restore the original configuration.
            try:
                self.restore_original_config()

                self.run_command(
                    "systemctl",
                    "--user",
                    "restart",
                    "pipewire.service",
                    timeout=30
                )

                self.wait_for_sinks(physical_sink)

                sinks = self.get_sinks()

                if previous_default in sinks:
                    self.run_command(
                        "pactl",
                        "set-default-sink",
                        previous_default
                    )

            except Exception as rollback_error:
                raise RuntimeError(
                    f"Equalizer failed: {error}. "
                    f"Rollback also failed: {rollback_error}. "
                    "Check PipeWire service status."
                ) from error

            raise RuntimeError(
                f"Equalizer failed: {error}. "
                "The original PipeWire configuration was restored."
            ) from error

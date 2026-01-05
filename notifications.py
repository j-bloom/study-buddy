import platform
import subprocess

OS_NAME = platform.system()

# Built-in macOS sound (guaranteed to exist)
MAC_SOUND = "/System/Library/Sounds/Glass.aiff"


def send_notification(title: str, message: str):
    if OS_NAME == "Darwin":
        # Play sound first
        subprocess.Popen(
            ["afplay", MAC_SOUND],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Then show alert
        subprocess.run(
            [
                "osascript",
                "-e",
                f'display alert "{title}" message "{message}"'
            ],
            check=False
        )

    elif OS_NAME == "Windows":
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                timeout=5
            )
        except Exception:
            print(f"[NOTIFICATION] {title}: {message}")

    else:
        print(f"[NOTIFICATION] {title}: {message}")

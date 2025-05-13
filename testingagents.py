import subprocess

# List of bots (paths or module names)
bots = [
    ("RandomSensing.py", "reconchess.bots.random_bot"),
    ("reconchess.bots.random_bot", "RandomSensing.py"),
    ("RandomSensing.py", "TroutBot.py"),
    ("TroutBot.py", "RandomSensing.py"),
    ("TroutBot.py", "reconchess.bots.random_bot"),
    ("reconchess.bots.random_bot", "TroutBot.py")
]

print("Starting Tournament\n")

for i, (white, black) in enumerate(bots, 1):
    print(f"\n--- Match {i}: {white} (White) vs {black} (Black) ---")
    try:
        subprocess.run([
            "python", "-m", "reconchess.scripts.rc_bot_match", white, black
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f" Error running match {i}: {e}")

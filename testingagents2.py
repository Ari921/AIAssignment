import subprocess

BOTS = [
    "ImprovedAgent.py",
    "RandomSensing.py",
    "TroutBot.py",
    "RandomAgent.py"
]

def play_match(whitebot, blackbot, matchnum):
    print(f"\nMatch {matchnum}: {whitebot} (White) vs {blackbot} (Black)")
    try:
        result = subprocess.run(
            ["python3", "-m", "reconchess.scripts.rc_bot_match", whitebot, blackbot],
            capture_output=True, text=True, check=True
        )
        output = result.stdout

        for line in output.splitlines():
            if "Winner:" in line:
                print(f" {line.strip()}")
                return

        print(" No winner found in output")

    except subprocess.CalledProcessError as e:
        print(f"Error in match {matchnum}: {e}")

def double_round_robin(bots):
    matchnum = 1
    for i in range(len(bots)):
        for j in range(i + 1, len(bots)):
            bot1 = bots[i]
            bot2 = bots[j]

            #skip this matchup if it's RandomAgent vs TroutBot
            if {"RandomAgent.py", "TroutBot.py"} == {bot1, bot2}:
                continue

            
            for repeat in range(2):
                play_match(bot1, bot2, matchnum)
                matchnum += 1

                play_match(bot2, bot1, matchnum)
                matchnum += 1

if __name__ == "__main__":
    double_round_robin(BOTS)

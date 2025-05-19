
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
        subprocess.run(["python3", "-m", "reconchess.scripts.rc_bot_match", whitebot, blackbot], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error in match {matchnum}: {e}")

def roundrobin(bots):
    matchnum = 1
    for i in range(len(bots)):
        for j in range(i + 1, len(bots)):
            whitebot = bots[i]
            blackbot = bots[j]

            #skip RandomAgent vs TroutBot matches
            if {"RandomAgent.py", "TroutBot.py"} == {whitebot, blackbot}:
                continue

            play_match(whitebot, blackbot, matchnum)
            matchnum += 1
            play_match(blackbot, whitebot, matchnum)
            matchnum += 1

if __name__ == "__main__":
   
    roundrobin(BOTS)
   
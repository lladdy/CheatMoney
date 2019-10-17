import sys

import sc2
from cheatmoney import run_ladder_game
from cheatmoney.cheatmoney import CheatMoney
from sc2 import Race, Difficulty
from sc2.player import Bot, Computer

bot = Bot(Race.Terran, CheatMoney())

# Start game
if __name__ == '__main__':
    if "--LadderServer" in sys.argv:
        # Ladder game started by LadderManager
        print("Starting ladder game...")
        run_ladder_game(bot)
    else:
        # Local game
        print("Starting local game...")
        sc2.run_game(sc2.maps.get("AbyssalReefLE"), [
            bot,
            Computer(Race.Random, Difficulty.VeryHard)
        ], realtime=False)

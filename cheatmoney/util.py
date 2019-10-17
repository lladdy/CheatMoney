

class Util():
    def __init__(self, bot=None):
        self.bot = bot

    def outofbounds(self, pos):
        if not pos:
            return
        raw_map = self.bot.game_info.playable_area
        map_width = raw_map[2]
        map_height = raw_map[3]

        x = pos[0]
        y = pos[1]

        if (x <= 0) or (x >= map_width):
            return True
        elif (y <= 0) or (y >= map_height):
            return True
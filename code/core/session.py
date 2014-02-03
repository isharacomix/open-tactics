# A session is an interactive match of Rules of War between 2 or more teams.
# A session consists of multiple TEAMS each playing on a single MAP governed by
# set of RULES. The RULES and MAP are usually provided in the form of a JSON
# data file.

from . import grid, rules

from graphics import sprites

import copy

# In theory, the game engine should be able to handle multiple sessions
# simultaneously. The session should be provided with a Dict generated from the
# JSON of a map in the following format.
#   rules: a dict containing the unit and terrain definitions
#   grid: a dict containing all of the tiles and other map variables (w,h,etc)
#   players: a list of the players, mapped to the teams in the grid
#   history: (optional) list of moves that have been played so far
class Session(object):
    def __init__(self, data):
        self.data = data
        self.grid = grid.Grid(data["grid"], data["rules"])

        # Load the players. If a team does not have a respective player,
        # destroy that team.
        for t in self.grid.teams:
            t.active = False
        for p in data["players"]:
            pdata = data["players"][p]
            pteam = self.grid.teams[pdata["team"]]
            pteam.active = True
            pteam.name = p
        for t in [t for t in self.grid.teams if not t.active]:
            t.name = "---"
            self.grid.purge(t,True)
        
        # Create the state machine widgets. These contain the ability to
        # undo actions and whatnot.
        self.grid.end_turn()
        self.action = rules.Begin()
        self.startover = copy.deepcopy(self.grid)
        self.checkpoint = copy.deepcopy(self.grid)
        self.inputs = []
        replay = data.pop("history",[])
        self.data["history"] = []
        self.history = []
        
        # Create the grid sprite.
        self.cursor = 0,0
        self.grid_sprite = sprites.Sprite(0,0,60,24)
        self.grid_sprite.fill(' ')
        self.grid_sprite.add_sprite(self.grid.sprite)
        self.cursor_sprite = sprites.Sprite(0,0,1,1,100)
        self.cursor_sprite.putc(None,0,0,"w","X",False,True)
        self.grid_sprite.add_sprite(self.cursor_sprite)
        
    # This exports our data as a dictionary to be JSONified. If history is
    # included, it's like saving a snapshot of the game to be continued later.
    # If griddata is included, it's like using the current snapshot as a new
    # map.
    def export(self, history=True, griddata=False):
        return {}
    
    # This function takes the character that was most recently entered by the
    # player and handles it. Even if no player is playing, this function
    # essentially serves as the step function for the AI.
    def handle_input(self, c):
        for a in self.grid.info():
            pass
        
        # If control belongs to the human, then we process all inputs that way.
        # If control does not belong to the human, then the control simply
        # allows the player to move the map around.
        cx,cy = self.cursor
        result = None
        if self.grid.current_team().control == "human":
            result = None
            if self.action.form == "coord":
                if c == "left": cx -=1
                if c == "right": cx +=1
                if c == "up": cy -= 1
                if c == "down": cy += 1
                if (self.cursor != (cx,cy)):
                    self.cursor = cx,cy
                    self.action.update(self.cursor, self.grid)
                if c == "enter":
                    result = self.action.perform(self.cursor, self.grid)
                    self.inputs.append(self.cursor)
                self.cursor_sprite.move_to(cx,cy)
                    
        # If we got a result from performing an action, we will be given
        # either an order or a new action to perform.
        if result:
            if result == rules.ACT_COMMIT:
                self.history.append((copy.deepcopy(self.checkpoint), self.inputs))
                self.checkpoint = copy.deepcopy(self.grid)
                self.action = rules.Begin()
            elif result == rules.ACT_UNDO:
                self.grid.sprite.kill()
                if self.inputs:
                    self.inputs = []
                    self.grid = copy.deepcopy(self.checkpoint)
                else:
                    cp, acts = self.history.pop()
                    self.grid = cp
                self.grid_sprite.add_sprite(self.grid.sprite)
                self.grid.info()
                self.action = rules.Begin()
            elif result == rules.ACT_RESTART:
                self.history = []
                self.inputs = []
                self.grid.sprite.kill()
                self.grid = copy.deepcopy(self.startover())
                self.checkpoint = copy.deepcopy(self.startover())
                self.action = rules.Begin()
            elif result == rules.ACT_END:
                history = []
                self.data["history"].append(history)
                for (cp,acts) in self.history:
                    history.append(acts)
                self.history = []
                self.grid.end_turn()
                self.startover = copy.deepcopy(self.grid)
                self.checkpoint = copy.deepcopy(self.grid)
                self.action = rules.Begin()
            else:
                self.action = result

    # The session has multiple sprites that need to be rendered, from the
    # view of the grid to the mutliple popups that need to appear.
    def render(self, x, y):
        self.grid_sprite.render(0,0)



    


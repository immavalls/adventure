class AdventureGame:
    def __init__(self):
        self.game_active = True
        self.current_location = "start"
        self.locations = {
            "start": "You are at the beginning of your adventure. There's a path leading north.",
            "forest": "You are in a dark forest. The trees are thick and you can barely see sunlight. Paths lead north and south.",
            "cave": "You have entered a damp cave. The walls are covered with moss and there's a strange noise echoing. Paths lead south and east."
        }

    def process_command(self, command):
        if command.lower() in ["quit", "exit"]:
            self.game_active = False
            return "You have ended your adventure."
        elif command.lower() == "go north":
            if self.current_location == "start":
                self.current_location = "forest"
            elif self.current_location == "forest":
                self.current_location = "cave"
            else:
                return "You can't go north from here."
        elif command.lower() == "go south":
            if self.current_location == "cave":
                self.current_location = "forest"
            elif self.current_location == "forest":
                self.current_location = "start"
            else:
                return "You can't go south from here."
        elif command.lower() == "look around":
            return self.locations.get(self.current_location, "You see nothing of interest.")
        else:
            return "I don't understand that command."
        
        return self.locations.get(self.current_location, "You see nothing of interest.")

    def play(self):
        print("Welcome to your text adventure! Type 'quit' to exit.")
        print(self.locations[self.current_location])
        while self.game_active:
            command = input(">>> ")
            response = self.process_command(command)
            print(response)

if __name__ == "__main__":
    game = AdventureGame()
    game.play()
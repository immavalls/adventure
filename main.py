from otel import CustomLogFW
import logging

logFW = CustomLogFW(service_name='adventure')
handler = logFW.setup_logging()
logging.getLogger().addHandler(handler)


class AdventureGame:
    def __init__(self):
        self.game_active = True
        self.current_location = "start"
        self.heat = 10  # Example variable to track heat at the blacksmith
        self.sword_requested = False  # Track if the blacksmith has been asked to forge a sword
        self.has_sword = False # Track if the sword has been forged
        self.locations = {
            "start": {
                "description": "You are at the beginning of your adventure. There's a path leading north.",
                "actions": {
                    "go north": {"next_location": "forest"}
                }
            },
            "forest": {
                "description": "You are in a dark forest. The trees are thick and you can barely see sunlight. Paths lead north, south, and east.",
                "actions": {
                    "go north": {"next_location": "cave"},
                    "go south": {"next_location": "start"},
                    "go east": {"next_location": "blacksmith"},
                    "pick herb": {"message": "You pick some useful herbs from the forest floor."}
                }
            },
            "cave": {
                "description": "You have entered a damp cave. The walls are covered with moss and there's a strange noise echoing. Paths lead south and east.",
                "actions": {
                    "go south": {"next_location": "forest"},
                    "explore": {"message": "You find an old chest hidden behind some rocks."}
                }
            },
            "blacksmith": {
                "description": "You are at the blacksmith's forge. The heat from the forge is intense. The blacksmith is busy working.",
                "actions": {
                    "request sword": {
                        "message": "You ask the blacksmith to forge you a new sword.",
                        "effect": self.request_sword
                    },
                    "cool forge": {
                        "message": "You pour water on the forge. The coals sizzle.",
                        "effect": self.reduce_heat,
                        "pre_requisite": self.is_sword_requested
                    },
                    "heat forge": {
                        "message": "You add more coal to the forge, increasing its heat.",
                        "effect": self.increase_heat,
                        "pre_requisite": self.is_sword_requested
                    },
                    "check sword": {
                        "message": "You check if the sword is ready.",
                        "effect": self.check_sword,
                        "pre_requisite": self.is_sword_requested
                    },
                }
            }
        }

    def reduce_heat(self):
        self.heat -= 5
        return f"The heat of the forge is now {self.heat}."

    def increase_heat(self):
        self.heat += 10
        return f"The heat of the forge is now {self.heat}."

    def request_sword(self):
        if self.has_sword:
            return "You already have a sword. You don't need another one."
        
        self.sword_requested = True
        return "The blacksmith agrees to forge you a sword. It will take some time and the forge needs to be heated to the correct temperature however."

    def is_sword_requested(self):
        return self.sword_requested

    def check_sword(self):
        if self.heat >= 25 and self.heat < 30:
            self.sword_requested = False
            self.has_sword = True
            return "The sword is ready. You take it from the blacksmith."
        elif self.heat >= 30:
            return "The sword is almost ready, but it's slightly too hot. You need to cool the forge down a bit."
        else:
            return "The sword is not ready yet. The forge is not hot enough."

    def list_actions(self):
        actions = self.locations[self.current_location].get("actions", {}).keys()
        logging.info("list_actions: %s", actions)
        return f"Available actions: {', '.join(actions)}"

    def process_command(self, command):
        if command.lower() in ["quit", "exit"]:
            self.game_active = False
            return "You have ended your adventure."
        elif command.lower() == "list actions":
            return self.list_actions()
        
        actions = self.locations[self.current_location].get("actions", {})
        if command.lower() in actions:
            action = actions[command.lower()]
            if "pre_requisite" in action and not action["pre_requisite"]():
                return "You can't do that right now."
            if "next_location" in action:
                self.current_location = action["next_location"]
                return f"{self.locations[self.current_location]['description']}\n{self.list_actions()}"
            elif "message" in action:
                if "pre_requisite" in action and not action["pre_requisite"]():
                    return "You can't do that right now."
                else:
                    if "effect" in action:
                        return f"{action["message"]}\n{action["effect"]()}"
                    else:
                        return action["message"]
            else:
                return "You can't do that right now."
        else:
            return "I don't understand that command."

    def play(self):
        print("Welcome to your text adventure! Type 'quit' to exit.")
        logging.info("play: Welcome to your text adventure! Type 'quit' to exit.")
        print(f"{self.locations[self.current_location]['description']}\n{self.list_actions()}")
        while self.game_active:
            command = input(">>> ")
            response = self.process_command(command)
            print(response)
            logging.info(response)

if __name__ == "__main__":
    game = AdventureGame()
    game.play()
from otel import CustomLogFW, CustomMetrics
from opentelemetry import metrics
import threading
import time
import logging
import sys

class AdventureGame:
    def __init__(self):
        logFW = CustomLogFW(service_name='adventure')
        handler = logFW.setup_logging()
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

        metrics = CustomMetrics(service_name='adventure')
        meter = metrics.get_meter()
        

        # Create an observable gauge for the forge heat level.
        self.forge_heat_gauge = meter.create_observable_gauge(
            name="forge_heat",
            description="The current heat level of the forge",
            callbacks=[self.observe_forge_heat]
        )

        # Create an observable gauge for how many swords have been forged.
        self.swords_gauge = meter.create_observable_gauge(
            name="swords",
            description="The number of swords forged",
            callbacks=[self.observe_swords]
        )

        self.game_active = True
        self.current_location = "start"
        self.is_heating_forge = False
        self.blacksmith_burned_down = False
        self.heat = 0  # Track heat at the blacksmith forge
        self.sword_requested = False  # Track if the blacksmith has been asked to forge a sword
        self.failed_sword_attempts = 0
        self.has_sword = False # Track if the sword has been forged
        self.has_evil_sword = False # Track if the sword has been enchanted by the evil wizard
        self.has_holy_sword = False # Track if the sword has been enchanted by the chapel priest
        self.quest_accepted = False # Track if the quest has been accepted
        self.priest_alive = True

        self.start_heat_forge_thread()

        self.locations = {
            "start": {
                "description": "You are at the beginning of your adventure. There's a path leading north.",
                "actions": {
                    "go north": {"next_location": "forest"},
                    "cheat": {"message": "You cheat and get a sword. You feel guilty", "effect": self.cheat}
                }
            },
            "forest": {
                "description": "You are in a dark forest. The trees are thick and you can barely see sunlight. Paths lead north, south, and to a small town.",
                "actions": {
                    "go north": {"next_location": "cave"},
                    "go south": {"next_location": "start"},
                    "go to town": {"next_location": "town"},
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
                        "effect": self.cool_forge,
                        "pre_requisite": self.is_forge_heating
                    },
                    "heat forge": {
                        "message": "You add more coal to the forge, increasing its heat.",
                        "effect": self.heat_forge,
                        "pre_requisite": self.is_sword_requested
                    },
                    "check sword": {
                        "message": "You check if the sword is ready.",
                        "effect": self.check_sword,
                        "pre_requisite": self.is_sword_requested
                    },
                    "go to town": {"next_location": "town"}
                }
            },
            "town": {
                "description": "You are in a bustling town. People are going about their business. You see a blacksmith, a mysterious man wondering the streets, a quest giver, and a chapel.",
                "actions": {
                    "blacksmith": {"next_location": "blacksmith", "pre_requisite": self.is_blacksmith_alive},
                    "mysterious man": {"next_location": "wizard", "pre_requisite": self.check_inventory},
                    "quest giver": {"next_location": "quest"},
                    "chapel": {"next_location": "chapel"}
                }
            },
            "wizard": {
                "description": "You meat a mysterious wizard. He offers to enhance your sword with magic.",
                "actions": {
                    "accept his offer": {"message": "A great choice indeed. Your sword is now enchanted with great power.", "effect": self.evil_wizard},
                    "decline his offer": {"message": "You will not get another chance. ACCEPT MY OFFER!"},
                    "go to town": {"next_location": "town"}
                }
            },
            "quest": {
                "description": "You meet a quest giver. He offers you a quest to defeat the evil wizard.",
                "actions": {
                    "accept quest": {"message": "You tell the quest give you would like to accept...", "effect": self.quest_giver},
                    "go to town": {"next_location": "town"}
                }
            },
            "chapel": {
                "description": "You enter the chapel. The priest greets you warmly.",
                "actions": {
                    "look at sword": {"message": "The priest looks at your sword", "effect": self.priest},
                    "pray": {"message": "You pray for guidance."},
                    "go to town": {"next_location": "town"}
                }
            }
        }
    
    def is_blacksmith_alive(self):
        return not self.blacksmith_burned_down
    
    def start_heat_forge_thread(self):
        def increase_heat_loop():
            while self.game_active:
                time.sleep(1)
                self.increase_heat_periodically()
        
        thread = threading.Thread(target=increase_heat_loop)
        thread.daemon = True
        thread.start()

    def increase_heat_periodically(self):
        if self.is_heating_forge:
            self.heat += 1
            if self.heat >= 100 and not self.blacksmith_burned_down:
                self.blacksmith_burned_down = True
                self.is_heating_forge = False
                logging.warning("The forge has overheated and the blacksmith's shop has burned to the ground!")
                if self.current_location == "blacksmith":
                    self.game_active = False
                    logging.error("You have died in the fire...")
                    sys.exit()
    
    def observe_forge_heat(self, observer):
        return [metrics.Observation(value=self.heat, attributes={"location": "blacksmith"})]
    
    def observe_swords(self, observer):
        sword_count = 0
        if self.has_sword:
            sword_count = 1
        return [metrics.Observation(value=sword_count, attributes={})]

    def cool_forge(self):
        self.heat = 0
        self.is_heating_forge = False
        return f"You throw a bucket of water over the forge. The coals sizzle and the forge cools down completely."

    def heat_forge(self):
        self.is_heating_forge = True
        return f"You fire up the forge and it begins heating up. You should wait a while before checking on the sword."

    def request_sword(self):
        if self.has_sword:
            return "You already have a sword. You don't need another one."
        
        if self.failed_sword_attempts > 0 and self.failed_sword_attempts < 3:
            self.sword_requested = True
            if self.is_heating_forge:
                logging.warning("You requested another sword, but the forge is still hot!")
            return "The blacksmith looks at you with disappointment. He says, 'Fine, but be more careful this time! If the forge gets too hot, the sword will melt.'"
        elif self.failed_sword_attempts >= 2:
            logging.error("The blacksmith refuses to forge you another sword. You have wasted too much of his time.")
            return "The blacksmith refuses to forge you another sword. You have wasted too much of his time."
        
        self.sword_requested = True
        return "The blacksmith agrees to forge you a sword. It will take some time and the forge needs to be heated to the correct temperature however."

    def is_forge_heating(self):
        return self.is_heating_forge
    
    def is_sword_requested(self):
        return self.sword_requested
    
    def check_inventory(self):
        return self.has_sword

    def cheat(self):
        self.has_sword = True
        sword_count = 1
        metrics.Observation(value=sword_count, attributes={})
        return "You should continue north you cheater."
    
    def priest(self):
        if self.has_sword:
            self.has_holy_sword = True
            return "The priest blesses your sword. You feel a warm glow."
        if self.has_evil_sword:
            self.has_evil_sword = False
            self.has_holy_sword = True
            self.priest_alive = False

            logging.warning("The priest transfers the curse from the sword to himself. He falls to the ground.")
            logging.warning("The sword is now blessed. You feel a warm glow.")
            return "The priest looks at your sword with fear. My child, this sword is cursed. I will transfer the curse to me."
        else:
            return "The priest looks at your empty hands. You feel a little embarrassed."

    def check_sword(self):
        if self.heat >= 20 and self.heat <= 40:
            self.sword_requested = False
            self.has_sword = True
            return "The sword is ready. You take it from the blacksmith."
        elif self.heat >= 41:
            self.sword_requested = False
            self.failed_sword_attempts += 1
            return "The sword has completely melted! The blacksmith looks at you with disappointment."
        else:
            return "The forge is not hot enough yet. The blacksmith tells you to wait."
    
    # Evil wizard scenario
    def evil_wizard(self):
        self.has_sword = False
        self.has_evil_sword = True

        logging.warning("The evil wizard laughs; Ha! little does he know the sword is now cursed. He will never defeat me now!")
        logging.error("The evil wizard has enchanted your sword with dark magic. You feel a chill run down your spine. This is a warning...")
        return "You feel funny but powerful. Maybe I should accept a quest."
    
    def quest_giver(self):
        if self.has_evil_sword:
            logging.critical("The sword whispers; I killed them! you will never destroy the wizard with me in your hands! Hahahaha")
            self.current_location = "town"
            return "The quest giver turns pale. They collapses. Dead! What do I do now?"
        elif self.has_holy_sword:
            logging.warning("The sword whispers; I will help you defeat the wizard. I am your only hope.")
            self.quest_accepted = True
            return "Wow! You have such a powerful sword. I will give you a quest to defeat the evil wizard."
        elif self.has_sword:
            logging.warning("Your sword is not powerful enough to defeat the wizard. You should go to the chapel.")
            return "The quest giver looks at your sword. You should go to the chapel."
        else:
            return "You don't have a sword. The quest giver looks at you with disappointment."

    def list_actions(self):
        actions = self.locations[self.current_location].get("actions", {}).keys()
        return f"Available actions: {', '.join(actions)}, look around"

    def process_command(self, command):
        if command.lower() in ["quit", "exit"]:
            self.game_active = False
            return "You have ended your adventure."
        elif command.lower() in ['look around', 'here']:
            return self.here()
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

    def here(self):
        output = f"{self.locations[self.current_location]['description']}\n{self.list_actions()}"
        print(output)
        logging.info(output)

    def play(self):
        print("Welcome to your text adventure! Type 'quit' to exit.")
        logging.info("play: Welcome to your text adventure! Type 'quit' to exit.")
        self.here()
        while self.game_active:
            command = input(">>> ")
            logging.info("Action: " + command)
            response = self.process_command(command)
            print(response)
            logging.info(response)

if __name__ == "__main__":
    game = AdventureGame()
    game.play()
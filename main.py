#!/usr/bin/env python3
"""
Elevator Adventure - Interactive Story Game with Real Elevator Simulation
OOP principles: Inheritance, Polymorphism, Encapsulation, Abstraction
"""

import random
import time
from enum import Enum
from typing import List, Optional, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass


class Direction(Enum):
    """Elevator movement direction"""
    UP = "UP"
    DOWN = "DOWN"
    IDLE = "IDLE"


class DoorState(Enum):
    """Door states"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    OPENING = "OPENING"
    CLOSING = "CLOSING"


@dataclass
class ElevatorConfig:
    """Configuration for elevator behavior"""
    movement_delay_per_floor: float = 2.0  # seconds per floor
    door_open_time: float = 3.0  # seconds to open/close
    max_floors: int = 15
    min_floors: int = 1


class Button:
    """Represents an elevator button """
    
    def __init__(self, floor: int):
        self._floor = floor
        self._is_pressed = False
        self._is_stuck = False
    
    @property
    def floor(self) -> int:
        """Get the floor number this button represents"""
        return self._floor
    
    @property
    def is_pressed(self) -> bool:
        """Check if button is currently pressed"""
        return self._is_pressed
    
    @property
    def is_stuck(self) -> bool:
        """Check if button is stuck"""
        return self._is_stuck
    
    def press(self) -> bool:
        """
        Press the button
        Returns True if successfully pressed, False if stuck
        """
        if self._is_stuck:
            return False
        self._is_pressed = True
        return True
    
    def release(self) -> None:
        """Release the button"""
        self._is_pressed = False
    
    def set_stuck(self, stuck: bool = True) -> None:
        """Set button stuck state"""
        self._is_stuck = stuck


class Floor:
    """Represents a building floor"""
    
    def __init__(self, number: int):
        self._number = number
        self._call_button_up: Optional[Button] = None
        self._call_button_down: Optional[Button] = None
    
    @property
    def number(self) -> int:
        """Get floor number"""
        return self._number
    
    def set_call_buttons(self, up: Optional[Button], down: Optional[Button]) -> None:
        """Set the call buttons for this floor"""
        self._call_button_up = up
        self._call_button_down = down
    
    def get_call_button(self, direction: Direction) -> Optional[Button]:
        """Get call button for specified direction"""
        if direction == Direction.UP:
            return self._call_button_up
        elif direction == Direction.DOWN:
            return self._call_button_down
        return None


class ElevatorDoor:
    """Represents elevator doors """
    
    def __init__(self, config: ElevatorConfig):
        self._state = DoorState.CLOSED
        self._config = config
    
    @property
    def state(self) -> DoorState:
        """Get current door state"""
        return self._state
    
    @property
    def is_open(self) -> bool:
        """Check if doors are open"""
        return self._state == DoorState.OPEN
    
    @property
    def is_closed(self) -> bool:
        """Check if doors are closed"""
        return self._state == DoorState.CLOSED
    
    def open(self) -> None:
        """Open the doors with realistic timing"""
        if self._state == DoorState.OPEN:
            return
        
        self._state = DoorState.OPENING
        time.sleep(self._config.door_open_time)
        self._state = DoorState.OPEN
    
    def close(self) -> None:
        """Close the doors with realistic timing"""
        if self._state == DoorState.CLOSED:
            return
        
        self._state = DoorState.CLOSING
        time.sleep(self._config.door_open_time)
        self._state = DoorState.CLOSED
    
    def force_open(self) -> bool:
        """Attempt to force doors open (returns success)"""
        if self._state == DoorState.CLOSING:
            self._state = DoorState.OPENING
            time.sleep(self._config.door_open_time / 2)
            self._state = DoorState.OPEN
            return True
        return False


class ElevatorEvent(ABC):
    """Base class for elevator events """
    
    def __init__(self, floor: int):
        self._floor = floor
        self._resolved = False
    
    @property
    def floor(self) -> int:
        """Get floor where event occurs"""
        return self._floor
    
    @property
    def resolved(self) -> bool:
        """Check if event is resolved"""
        return self._resolved
    
    @abstractmethod
    def get_description(self) -> str:
        """Get event description"""
        pass
    
    @abstractmethod
    def handle_choice(self, choice: int, elevator: 'Elevator') -> tuple[bool, str]:
        """
        Handle player choice
        Returns: (causes_delay: bool, result_message: str)
        """
        pass
    
    @abstractmethod
    def get_choices(self) -> List[str]:
        """Get available choices for this event"""
        pass


class MusicEvent(ElevatorEvent):
    """Loud music event"""
    
    def get_description(self) -> str:
        return f"The elevator music suddenly gets VERY loud on floor {self._floor}..."
    
    def get_choices(self) -> List[str]:
        return [
            "Cover your ears and wait it out",
            "Try to find the volume control",
            "Press all the buttons in frustration"
        ]
    
    def handle_choice(self, choice: int, elevator: 'Elevator') -> tuple[bool, str]:
        if choice == 1:
            return False, "You endure the loud music. Your patience decreases slightly."
        elif choice == 2:
            if random.random() < 0.5:
                self._resolved = True
                return False, "[SUCCESS] You find a hidden volume control and turn it down! The music stops."
            else:
                return True, "[FAILED] You can't find the volume control. The music continues."
        else:
            # Pressing buttons randomly
            elevator.add_random_stop()
            return True, "[WARNING] You press random buttons! The elevator stops briefly..."


class StuckButtonEvent(ElevatorEvent):
    """Stuck button event"""
    
    def __init__(self, floor: int, button: Button):
        super().__init__(floor)
        self._button = button
    
    def get_description(self) -> str:
        return f"You notice a button is stuck on floor {self._floor}!"
    
    def get_choices(self) -> List[str]:
        return [
            "Ignore it",
            "Try to unstick it carefully",
            "Press it repeatedly"
        ]
    
    def handle_choice(self, choice: int, elevator: 'Elevator') -> tuple[bool, str]:
        if choice == 1:
            return False, "You decide to ignore it. Nothing happens."
        elif choice == 2:
            if random.random() < 0.7:
                self._button.set_stuck(False)
                self._resolved = True
                return False, "[SUCCESS] You carefully fix the stuck button! It works now."
            else:
                return True, "[FAILED] You try to fix it but make it worse. The elevator shudders!"
        else:
            return True, "[WARNING] You press it too hard! The elevator jolts and stops."


class UnexpectedStopEvent(ElevatorEvent):
    """Unexpected stop event"""
    
    def get_description(self) -> str:
        return f"The elevator stops unexpectedly on floor {self._floor}! The doors don't open..."
    
    def get_choices(self) -> List[str]:
        return [
            "Wait calmly",
            "Press the door open button",
            "Look for the emergency phone"
        ]
    
    def handle_choice(self, choice: int, elevator: 'Elevator') -> tuple[bool, str]:
        if choice == 1:
            self._resolved = True
            return True, "You wait patiently. The doors open after a moment. False alarm!"
        elif choice == 2:
            elevator.door.force_open()
            self._resolved = True
            return True, "[SUCCESS] You press the door button and the doors open!"
        else:
            return True, "You find the emergency phone but don't need it. The doors eventually open."


class WeirdSoundEvent(ElevatorEvent):
    """Weird sound event"""
    
    def get_description(self) -> str:
        return f"You hear a strange CLUNK sound on floor {self._floor}..."
    
    def get_choices(self) -> List[str]:
        return [
            "Ignore it - elevators make weird sounds",
            "Get worried and check the emergency button",
            "Press the next floor button quickly"
        ]
    
    def handle_choice(self, choice: int, elevator: 'Elevator') -> tuple[bool, str]:
        if choice == 1:
            if random.random() < 0.8:
                return False, "Good call! It was just a normal elevator sound. Nothing happens."
            else:
                return True, "[WARNING] The elevator slows down... but eventually continues."
        elif choice == 2:
            return False, "You check the emergency button but don't press it. The sound stops."
        else:
            elevator.add_random_stop()
            return True, "[WARNING] You panic and hit the button! The elevator stops unnecessarily."


class Elevator:
    """
    Main Elevator class - simulates real elevator behavior
    """
    
    def __init__(self, config: ElevatorConfig, elevator_id: str = "A"):
        self._config = config
        self._elevator_id = elevator_id
        self._current_floor = config.min_floors
        self._direction = Direction.IDLE
        self._door = ElevatorDoor(config)
        self._requested_floors: Set[int] = set()
        self._floor_buttons: dict[int, Button] = {}
        self._floors: List[Floor] = []
        
        # Initialize floor buttons
        for floor in range(config.min_floors, config.max_floors + 1):
            self._floor_buttons[floor] = Button(floor)
        
        # Initialize floors
        for floor_num in range(config.min_floors, config.max_floors + 1):
            self._floors.append(Floor(floor_num))
    
    @property
    def current_floor(self) -> int:
        """Get current floor"""
        return self._current_floor
    
    @property
    def direction(self) -> Direction:
        """Get current direction"""
        return self._direction
    
    @property
    def door(self) -> ElevatorDoor:
        """Get door object"""
        return self._door
    
    @property
    def requested_floors(self) -> Set[int]:
        """Get set of requested floors"""
        return self._requested_floors.copy()
    
    @property
    def elevator_id(self) -> str:
        """Get elevator ID"""
        return self._elevator_id
    
    def get_button(self, floor: int) -> Optional[Button]:
        """Get button for a specific floor"""
        return self._floor_buttons.get(floor)
    
    def press_floor_button(self, floor: int) -> bool:
        """
        Press a floor button inside the elevator
        Returns True if successful
        """
        if not (self._config.min_floors <= floor <= self._config.max_floors):
            return False
        
        button = self._floor_buttons[floor]
        if button.press():
            self._requested_floors.add(floor)
            if self._direction == Direction.IDLE:
                self._direction = Direction.UP if floor > self._current_floor else Direction.DOWN
            return True
        return False
    
    def add_random_stop(self) -> None:
        """Add a random floor stop (for events)"""
        if len(self._requested_floors) < (self._config.max_floors - self._config.min_floors):
            random_floor = random.randint(
                self._config.min_floors,
                self._config.max_floors
            )
            if random_floor != self._current_floor:
                self._requested_floors.add(random_floor)
    
    def move_to_floor(self, target_floor: int) -> None:
        """
        Move elevator to target floor with realistic simulation
        """
        if target_floor == self._current_floor:
            return
        
        # Set direction
        if target_floor > self._current_floor:
            self._direction = Direction.UP
        else:
            self._direction = Direction.DOWN
        
        floors_to_move = abs(target_floor - self._current_floor)
        
        # Simulate movement floor by floor
        for _ in range(floors_to_move):
            time.sleep(self._config.movement_delay_per_floor)
            if self._direction == Direction.UP:
                self._current_floor += 1
            else:
                self._current_floor -= 1
    
    def _get_next_floor(self) -> Optional[int]:
        """
        Smart algorithm: Get next floor to visit
        Processes requests in current direction first
        """
        if not self._requested_floors:
            return None
        
        floors_in_direction = []
        
        if self._direction == Direction.UP:
            floors_in_direction = [f for f in self._requested_floors if f > self._current_floor]
            if not floors_in_direction:
                self._direction = Direction.DOWN
                return self._get_next_floor()
            return min(floors_in_direction)
        
        elif self._direction == Direction.DOWN:
            floors_in_direction = [f for f in self._requested_floors if f < self._current_floor]
            if not floors_in_direction:
                self._direction = Direction.UP
                return self._get_next_floor()
            return max(floors_in_direction)
        
        # IDLE state - determine direction
        if self._requested_floors:
            first = min(self._requested_floors)
            self._direction = Direction.UP if first > self._current_floor else Direction.DOWN
            return self._get_next_floor()
        
        return None
    
    def process_next_request(self) -> bool:
        """
        Process next floor request
        Returns True if movement occurred, False if no requests
        """
        next_floor = self._get_next_floor()
        if next_floor is None:
            self._direction = Direction.IDLE
            return False
        
        # Move to floor
        self.move_to_floor(next_floor)
        
        # Open and close doors
        if not self._door.is_open:
            self._door.open()
        
        # Clear request for this floor
        if next_floor in self._requested_floors:
            button = self._floor_buttons[next_floor]
            button.release()
            self._requested_floors.remove(next_floor)
        
        # Close doors
        if not self._door.is_closed:
            self._door.close()
        
        return True
    
    def get_status(self) -> str:
        """Get elevator status string"""
        return (f"Elevator {self._elevator_id}: Floor {self._current_floor}, "
                f"Direction: {self._direction.value}, "
                f"Doors: {self._door.state.value}, "
                f"Requests: {sorted(self._requested_floors)}")


class Player:
    """Player/Passenger class"""
    
    def __init__(self, name: str):
        self._name = name
        self._patience = 100
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def patience(self) -> int:
        return self._patience
    
    def decrease_patience(self, amount: int) -> None:
        """Decrease player patience"""
        self._patience = max(0, self._patience - amount)
    
    def increase_patience(self, amount: int) -> None:
        """Increase player patience"""
        self._patience = min(100, self._patience + amount)
    
    def has_patience(self) -> bool:
        """Check if player has patience remaining"""
        return self._patience > 0


class Building:
    """Building class - manages elevators and floors"""
    
    def __init__(self, name: str, config: ElevatorConfig):
        self._name = name
        self._config = config
        self._elevators: List[Elevator] = []
    
    def add_elevator(self, elevator: Elevator) -> None:
        """Add an elevator to the building"""
        self._elevators.append(elevator)
    
    def get_elevator(self, index: int) -> Optional[Elevator]:
        """Get elevator by index"""
        if 0 <= index < len(self._elevators):
            return self._elevators[index]
        return None
    
    @property
    def elevators(self) -> List[Elevator]:
        """Get all elevators"""
        return self._elevators.copy()


class InteractiveElevatorMode:
    """
    Interactive elevator mode - direct control of elevator
    Users can select floors to travel to
    """
    
    def __init__(self):
        self._config = ElevatorConfig()
        self._elevator = Elevator(self._config, "A")
    
    def print_slow(self, text: str, delay: float = 0.02) -> None:
        """Print text with typing effect"""
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()
    
    def get_floor_input(self) -> Optional[int]:
        """Get floor number from user"""
        while True:
            try:
                floor_str = input(f"\nEnter floor number ({self._config.min_floors}-{self._config.max_floors}) or 'q' to quit: ").strip()
                if floor_str.lower() == 'q':
                    return None
                floor = int(floor_str)
                if self._config.min_floors <= floor <= self._config.max_floors:
                    return floor
                print(f"Floor must be between {self._config.min_floors} and {self._config.max_floors}")
            except ValueError:
                print("Please enter a valid floor number or 'q' to quit")
    
    def play(self) -> None:
        """Main interactive loop"""
        print("\n" + "="*60)
        self.print_slow("INTERACTIVE ELEVATOR MODE", 0.05)
        print("="*60)
        time.sleep(0.3)
        
        self.print_slow(f"\nWelcome to Interactive Elevator Mode!")
        self.print_slow(f"The building has floors {self._config.min_floors} to {self._config.max_floors}")
        self.print_slow(f"Current floor: {self._elevator.current_floor}")
        self.print_slow("Select floors to travel to. Type 'q' to quit.\n")
        
        while True:
            # Show current status
            print(f"\n{'='*60}")
            print(f"Current Floor: {self._elevator.current_floor}")
            print(f"Direction: {self._elevator.direction.value}")
            print(f"Doors: {self._elevator.door.state.value}")
            if self._elevator.requested_floors:
                print(f"Pending Requests: {sorted(self._elevator.requested_floors)}")
            print(f"{'='*60}")
            
            # Get floor input
            target_floor = self.get_floor_input()
            if target_floor is None:
                print("\nExiting Interactive Elevator Mode. Goodbye!")
                break
            
            # Press button
            if target_floor == self._elevator.current_floor:
                print(f"\nAlready at floor {target_floor}!")
                continue
            
            if not self._elevator.press_floor_button(target_floor):
                print(f"\n[WARNING] Button for floor {target_floor} is stuck! Try another floor.")
                continue
            
            print(f"\nFloor {target_floor} requested.")
            
            # Process pending requests if any
            self._process_pending_requests()
    
    def _process_pending_requests(self) -> None:
        """Process all pending elevator requests using smart algorithm"""
        while self._elevator.requested_floors:
            next_floor = self._elevator._get_next_floor()
            if next_floor is None:
                break
            
            self._move_to_floor(next_floor)
    
    def _move_to_floor(self, target_floor: int) -> None:
        """Process elevator movement to target floor"""
        # Close doors if open
        if self._elevator.door.is_open:
            self.print_slow("Doors closing...")
            self._elevator.door.close()
        
        # Show starting information
        start_floor = self._elevator.current_floor
        direction = Direction.UP if target_floor > start_floor else Direction.DOWN
        
        print(f"\n{'='*60}")
        self.print_slow(f"Elevator starting at floor {start_floor}", 0.02)
        self.print_slow(f"Traversing {'up' if direction == Direction.UP else 'down'} to floor {target_floor}...", 0.02)
        print(f"{'='*60}\n")
        time.sleep(0.3)
        
        # Move floor by floor
        for floor_num in range(start_floor + 1, target_floor + 1) if direction == Direction.UP else range(start_floor - 1, target_floor - 1, -1):
            # Update current floor
            if direction == Direction.UP:
                self._elevator._current_floor += 1
            else:
                self._elevator._current_floor -= 1
            
            # Show current floor during traversal
            arrow = "^" if direction == Direction.UP else "v"
            self.print_slow(f"{arrow} Now at floor {self._elevator.current_floor} {arrow}", 0.02)
            time.sleep(self._config.movement_delay_per_floor)
        
        # Arrived at destination
        print(f"\n{'='*60}")
        self.print_slow(f"ARRIVED AT FLOOR {target_floor}!")
        print(f"{'='*60}")
        
        # Open doors
        if not self._elevator.door.is_open:
            self.print_slow(f"\nDoors opening...")
            self._elevator.door.open()
            time.sleep(0.3)
        
        # Release button and clear request
        button = self._elevator.get_button(target_floor)
        if button:
            button.release()
        self._elevator._requested_floors.discard(target_floor)
        
        # Set direction to IDLE if no more requests
        if not self._elevator.requested_floors:
            self._elevator._direction = Direction.IDLE


class ElevatorAdventureGame:
    """
    Main game class - combines elevator simulation with interactive story
    """
    
    def __init__(self):
        self._config = ElevatorConfig()
        self._building = Building("TechCorp Building", self._config)
        self._player: Optional[Player] = None
        self._selected_elevator: Optional[Elevator] = None
        
        # Initialize elevators
        elevator_a = Elevator(self._config, "A")
        elevator_b = Elevator(self._config, "B")
        elevator_c = Elevator(self._config, "C")
        
        # Make elevator C have some quirks
        button_c = elevator_c.get_button(5)
        if button_c:
            if random.random() < 0.5:
                button_c.set_stuck(True)
        
        self._building.add_elevator(elevator_a)
        self._building.add_elevator(elevator_b)
        self._building.add_elevator(elevator_c)
    
    def print_slow(self, text: str, delay: float = 0.03) -> None:
        """Print text with typing effect"""
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()
    
    def wait_for_input(self, prompt: str = "\nPress Enter to continue...") -> None:
        """Wait for user input"""
        input(prompt)
    
    def get_choice(self, prompt: str, options: List[str]) -> int:
        """Get user choice"""
        while True:
            print(f"\n{prompt}")
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")
            
            try:
                choice = int(input(f"\nEnter your choice (1-{len(options)}): "))
                if 1 <= choice <= len(options):
                    return choice
                print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")
    
    def handle_event(self, event: ElevatorEvent) -> bool:
        """Handle an elevator event"""
        self.print_slow(f"\n{event.get_description()}")
        choices = event.get_choices()
        player_choice = self.get_choice("What do you do?", choices)
        
        causes_delay, message = event.handle_choice(player_choice, self._selected_elevator)
        self.print_slow(f"\n{message}")
        
        # Adjust patience based on delay
        if causes_delay:
            self._player.decrease_patience(random.randint(5, 20))
        else:
            if "[SUCCESS]" in message:
                self._player.increase_patience(5)
        
        return causes_delay
    
    def play(self) -> None:
        """Main game loop"""
        # Introduction
        print("\n" + "="*60)
        self.print_slow("ELEVATOR ADVENTURE", 0.05)
        print("="*60)
        time.sleep(0.5)
        
        self.print_slow("\nYou step into the grand lobby of the TechCorp building.")
        self.print_slow("The day is sunny, your coffee is warm, and you have somewhere to be.")
        self.wait_for_input()
        
        # Get player name
        name = input("\nWhat's your name, brave elevator rider? ").strip()
        if not name:
            name = "Adventurer"
        
        self._player = Player(name)
        
        target_floor = random.randint(5, self._config.max_floors)
        self.print_slow(f"\nWelcome, {name}! Today you need to get to floor {target_floor}.")
        self.print_slow(f"The building is {self._config.max_floors} stories tall. This should be easy, right?")
        self.wait_for_input()
        
        # Choose elevator
        print("\n" + "="*60)
        self.print_slow("You approach the elevator bank. Three elevators are available.")
        
        elevator_choice = self.get_choice(
            "Which elevator do you choose?",
            [
                "Elevator A (looks new and shiny)",
                "Elevator B (looks reliable)",
                "Elevator C (has a 'strange' button)"
            ]
        )
        
        self._selected_elevator = self._building.get_elevator(elevator_choice - 1)
        
        if elevator_choice == 1:
            self.print_slow("\nYou choose Elevator A. It looks pristine!")
            self._player.increase_patience(10)
        elif elevator_choice == 2:
            self.print_slow("\nYou choose Elevator B. The safe choice!")
        else:
            self.print_slow("\nYou choose Elevator C. You like to live dangerously!")
            self._player.decrease_patience(10)
        
        self.wait_for_input()
        
        # Press button
        print("\n" + "="*60)
        self.print_slow(f"You press the button for floor {target_floor}...")
        
        if not self._selected_elevator.press_floor_button(target_floor):
            self.print_slow("[WARNING] The button is stuck! You'll have to try another floor.")
            target_floor = random.choice([f for f in range(1, 16) if f != target_floor])
            self._selected_elevator.press_floor_button(target_floor)
            self.print_slow(f"You press floor {target_floor} instead...")
        
        self.print_slow("*ding* The elevator arrives!")
        self.wait_for_input()
        
        # Journey begins
        print("\n" + "="*60)
        self.print_slow("The doors slide open. You step inside.")
        self.print_slow(f"Current floor: {self._selected_elevator.current_floor}")
        self.print_slow(f"Destination: Floor {target_floor}")
        self.print_slow(f"Patience level: {self._player.patience}%")
        self.wait_for_input()
        
        # Main journey loop - floor by floor with events
        print("\n" + "="*60)
        print("ELEVATOR JOURNEY BEGINNING")
        print("="*60)
        
        # Close doors before starting
        if self._selected_elevator.door.is_open:
            self._selected_elevator.door.close()
        
        # Move floor by floor with progress display
        floors_to_travel = abs(target_floor - self._selected_elevator.current_floor)
        direction = Direction.UP if target_floor > self._selected_elevator.current_floor else Direction.DOWN
        start_floor = self._selected_elevator.current_floor
        
        # Show starting floor
        print(f"\n{'='*60}")
        self.print_slow(f"Elevator starting at floor {start_floor}", 0.02)
        self.print_slow(f"Traversing {'up' if direction == Direction.UP else 'down'} to floor {target_floor}...", 0.02)
        print(f"{'='*60}\n")
        time.sleep(0.5)
        
        # Traverse floor by floor
        for floor_num in range(start_floor + 1, target_floor + 1) if direction == Direction.UP else range(start_floor - 1, target_floor - 1, -1):
            # Update current floor
            if direction == Direction.UP:
                self._selected_elevator._current_floor += 1
            else:
                self._selected_elevator._current_floor -= 1
            
            # Show current floor during traversal
            arrow = "^" if direction == Direction.UP else "v"
            self.print_slow(f"{arrow} Now at floor {self._selected_elevator.current_floor} {arrow}", 0.02)
            time.sleep(self._config.movement_delay_per_floor)
            
            # Random event during journey 
            if self._selected_elevator.current_floor < target_floor and random.random() < 0.5:
                # Create random event 
                event_type = random.randint(0, 3)
                current_floor = self._selected_elevator.current_floor
                
                if event_type == 0:
                    event = MusicEvent(current_floor)
                elif event_type == 1:
                    # Stuck button event - need a button
                    button = self._selected_elevator.get_button(random.randint(1, 15))
                    if button:
                        event = StuckButtonEvent(current_floor, button)
                    else:
                        event = MusicEvent(current_floor)  # Fallback
                elif event_type == 2:
                    event = UnexpectedStopEvent(current_floor)
                else:
                    event = WeirdSoundEvent(current_floor)
                
                delay = self.handle_event(event)
                if delay:
                    time.sleep(1.0)  # Longer delay for events
                
                # Check patience after event
                if not self._player.has_patience():
                    print("\n[FURY] You've lost all patience! You decide to take the stairs instead.")
                    return
            
            #  suspense building
            if random.random() < 0.2 and self._selected_elevator.current_floor < target_floor:
                suspense_msgs = [
                    "The elevator feels slower than usual...",
                    "You wonder if you'll make it on time...",
                    "This is taking longer than expected...",
                    "Your coffee is getting cold...",
                ]
                self.print_slow(f"\n{random.choice(suspense_msgs)}", 0.02)
                self._player.decrease_patience(2)
        
        # Arrived at destination
        print(f"\n{'='*60}")
        self.print_slow(f"ARRIVED AT FLOOR {target_floor}!")
        print(f"{'='*60}")
        
        # Open doors at destination
        if not self._selected_elevator.door.is_open:
            self.print_slow(f"\nDoors opening...")
            self._selected_elevator.door.open()
            time.sleep(0.5)
        
        # Open doors at final destination
        if self._selected_elevator.current_floor == target_floor and not self._selected_elevator.door.is_open:
            self._selected_elevator.door.open()
        
        # Check if made it to target
        if self._selected_elevator.current_floor == target_floor:
            print("\n" + "="*60)
            print("SUCCESS!")
            print("="*60)
            self.print_slow(f"\n[SUCCESS] You made it to floor {target_floor}!")
            self.print_slow("The doors open smoothly...")
            
            if self._player.patience >= 80:
                self.print_slow("\nYou kept your cool the whole way! You're an elevator master!")
            elif self._player.patience >= 50:
                self.print_slow("\nYou made it! A bit stressed, but successful.")
            else:
                self.print_slow("\nYou made it, but that was rough! Your patience was tested.")
            
            self.print_slow(f"\nYour final patience level: {self._player.patience}%")
            self.print_slow("\nGreat work! You completed your elevator adventure!")
        else:
            print("\n" + "="*60)
            print("GAME OVER")
            print("="*60)
            print("\nYou couldn't handle the elevator stress and gave up!")
            print("Maybe next time you'll take the stairs?")
        
        self.wait_for_input("\n\nPress Enter to exit...")


def show_menu() -> int:
    """Display main menu and get user choice"""
    print("\n" + "="*60)
    print("THE ELEVATOR")
    print("="*60)
    print("\nSelect a mode:")
    print("1. Interactive Elevator Mode")
    print("   - Direct control of the elevator")
    print("   - Choose any floor to travel to")
    print("   - See the elevator simulation in action")
    print("\n2. Adventure Mode")
    print("   - Interactive story with random events")
    print("   - Navigate challenges to reach your destination")
    print("   - Manage your patience level")
    
    while True:
        try:
            choice = int(input("\nEnter your choice (1-2): "))
            if choice in [1, 2]:
                return choice
            print("Please enter 1 or 2")
        except ValueError:
            print("Please enter a number")


def main():
    """Main entry point"""
    try:
        mode_choice = show_menu()
        
        if mode_choice == 1:
            # Interactive Elevator Mode
            elevator = InteractiveElevatorMode()
            elevator.play()
        else:
            # Adventure Mode
            game = ElevatorAdventureGame()
            game.play()
            
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Thanks for playing!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

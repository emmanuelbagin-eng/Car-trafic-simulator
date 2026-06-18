import random

class Car:
    def __init__(self, color, width, height, speed, crossRoadChangeDirection):
        self.initializeRandomyCar()
        self.move()

    def removeCar(self):
        print("Removing the car from the simulation...")

    def initializeRandomyCar(self):
        self.color = random.choice(["red", "blue", "green", "yellow", "black"])
        self.width = random.randint(1, 2)
        self.height = random.randint(1, 2)
        self.speed = random.randint(10, 30)
        self.crossRoadChangeDirection = random.choice(["straight", "left", "right"])


    def printCar(self):
        print("Car color:", self.color)
        print("Car width:", self.width)
        print("Car height:", self.height)
        print("Car speed:", self.speed, "m/s")

    def move(self):
        print("The car is moving at a speed of", self.speed, "m/s")


    def changeSpeed(self, vitesse):
        self.speed = vitesse
        print("New speed:", self.speed, "m/s")
    
    def turn(self, direction):
        if direction.lower() == "left":
            print("Turning left...")
        elif direction.lower() == "right":
            print("Turning right...")
        else:
            print("Invalid direction. Please specify 'left' or 'right'.")
    
    
    def changeDirection(self):
        # we have 3 at the cross-road, so we can change the direction of the car: 
        # 1. continue straight
        # 2. take left
        # 3. take right
        print("Changing direction to:", self.crossRoadChangeDirection)
        


    def lidar(self):
        # This function simulates the LIDAR sensor of the car, which scans the environment 
        # and detects obstacles.
        print("Scanning the environment with LIDAR...  ")

from traffic import RoadSystem, TrafficLightSystem


class Simulation:
    def __init__(self):
        print("Initialisation de la simulation")
        self.trafficLightSystem = TrafficLightSystem()
        self.roadSystem = RoadSystem()  
        self.generateRandomly4CarsEachSecondInEachDirection(5)  # Génération aléatoire de 5 voitures par seconde dans chaque direction

    


    def generateRandomly4CarsEachSecondInEachDirection(self, numberOfCars): 
        print("Génération aléatoire de", numberOfCars, "voitures par seconde dans chaque direction")
        # un algo pour générer aléatoirement des voitures dans chaque direction, mais pour l'instant on va juste afficher un message
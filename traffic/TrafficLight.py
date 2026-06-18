class TrafficLight:
    greenOrRedTime = 30
    yellowTime = 5

    def __init__(self, redLight, greenLight, yellowLight):
        self.__color = "Red"
    

    def drawLight(self):
        print("Affichage du feu de circulation")
        print("Couleur du feu : ", self.__color)
        print("Durée du feu vert : ", self.greenOrRedTime, " secondes")
        print("Durée du feu rouge : ", self.greenOrRedTime, " secondes")
        print("Durée du feu jaune : ", self.yellowTime, " secondes")

    def authorizeLight(self): 
        self.greenLight = "mettre une couleur verte vive"
        self.redLight = "mettre une couleur rouge sombre"
        self.yellowLight = "mettre une couleur jaune sombre"
        print("Feu vert") 


    def stopLight(self): 
        self.greenLight = "mettre une couleur verte sombre"
        self.redLight = "mettre une couleur rouge vive"
        self.yellowLight = "mettre une couleur jaune sombre"
        print("Feu rouge")


    def cautionLight(self): 
        self.greenLight = "mettre une couleur verte sombre"
        self.redLight = "mettre une couleur rouge sombre"
        self.yellowLight = "mettre une couleur jaune vive"

        ## Ici le jaune doit clignoter, 
        # mais pour l'instant on ne peut pas le faire en console, donc on va juste afficher un message
        print("Feu jaune")
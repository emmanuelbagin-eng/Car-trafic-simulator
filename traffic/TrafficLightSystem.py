from traffic import TrafficLight


class TrafficLightSystem:

    def __init__(self, mbFeu :TrafficLight, mtFeu : TrafficLight, llFeu : TrafficLight, lrFeu: TrafficLight):
        print("Initialisation du système de feux de circulation")
        self.initializeTrafficLights()
        self.launchTrafficLightSystem()
        self.drawTrafficLights()
    

    def drawTrafficLights(self):
        print("Affichage des feux de circulation")
        self.mbFeu.drawLight()
        self.mtFeu.drawLight()
        self.llFeu.drawLight()
        self.lrFeu.drawLight()

    
    def initializeTrafficLights(self):
        print("Initialisation des feux de circulation")
        self.mbFeu.authorizeLight()
        self.mtFeu.authorizeLight()
        self.llFeu.stopLight()
        self.lrFeu.stopLight()

    def authorizeLateralTraffic(self):
        print("Autorisation du trafic latéral")
        self.mbFeu.stopLight()
        self.mtFeu.stopLight()
        self.llFeu.authorizeLight()
        self.lrFeu.authorizeLight()
    
    def authorizeMainTraffic(self):
        print("Autorisation du trafic principal")
        self.mbFeu.authorizeLight()
        self.mtFeu.authorizeLight()
        self.llFeu.stopLight()
        self.lrFeu.stopLight()
    
    def cautionMainTraffic(self):
        print("Mise en garde du trafic principal")
        self.mbFeu.cautionLight()
        self.mtFeu.cautionLight()
        self.llFeu.stopLight()
        self.lrFeu.stopLight()
    
    def cautionLateralTraffic(self):
        print("Mise en garde du trafic latéral")
        self.mbFeu.stopLight()
        self.mtFeu.stopLight()
        self.llFeu.cautionLight()
        self.lrFeu.cautionLight()
    

    def launchTrafficLightSystem(self):
        print("Lancement du système de feux de circulation")
        # un algo pour swifter entre les feux de circulation, mais pour l'instant on va juste afficher un message
        
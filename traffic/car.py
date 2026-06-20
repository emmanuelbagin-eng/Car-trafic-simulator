import random


class Car:
    """
    Représente une voiture sur le Canvas.

    BUG CORRIGÉ : le constructeur écrasait systématiquement tous les paramètres
    reçus en appelant 'self.initializeRandomyCar()'. Cette méthode est conservée
    (pour générer des voitures aléatoires à la demande), mais elle n'est plus
    appelée automatiquement dans __init__ : les valeurs passées en paramètres
    sont désormais réellement respectées.

    OPTIMISATIONS AJOUTÉES :
      - La vitesse est désormais systématiquement bornée entre MIN_SPEED et
        MAX_SPEED (2 à 5 pixels/frame), pour garantir un déplacement fluide
        à ~30 FPS sans "téléportation" visuelle, quelle que soit la valeur
        fournie au constructeur.
      - Un attribut 'has_turned' empêche une voiture de réévaluer son virage
        en boucle tant qu'elle traverse le carré central du carrefour.
      - Une méthode 'turn()' permet de changer dynamiquement la direction et
        l'orientation visuelle (largeur/hauteur) de la voiture lorsqu'elle
        s'engage dans l'intersection.
    """

    DIRECTIONS = ("N", "S", "E", "O")

    # Vitesse minimale et maximale en pixels par frame. Une vitesse plus élevée
    # ferait "téléporter" visuellement les voitures sur un Canvas Tkinter animé
    # à ~30 FPS ; une vitesse plus faible donnerait une simulation trop lente.
    MIN_SPEED = 2
    MAX_SPEED = 5

    def __init__(self, color="red", width=20, height=20, speed=5,
                 crossRoadChangeDirection="straight"):
        self.color = color
        self.width = width
        self.height = height

        # La vitesse est toujours bornée entre MIN_SPEED et MAX_SPEED, quelle
        # que soit la valeur reçue, pour rester cohérente avec une animation
        # Tkinter à ~30 FPS (root.after(30, ...)).
        self.speed = max(self.MIN_SPEED, min(self.MAX_SPEED, speed))

        self.crossRoadChangeDirection = crossRoadChangeDirection

        # Attributs de positionnement, indispensables pour l'affichage Canvas
        self.x = 0
        self.y = 0
        self.direction = "E"
        self.is_stopped = False

        # Drapeau anti-boucle : une fois le virage effectué au centre du
        # carrefour, ce drapeau empêche toute nouvelle réévaluation de la
        # direction tant que la voiture n'a pas quitté l'intersection.
        self.has_turned = False

    def initializeRandomyCar(self):
        """
        Génère un état aléatoire pour la voiture (couleur, vitesse, comportement
        au carrefour). Disponible à la demande, mais plus appelée automatiquement
        par le constructeur.
        """
        colors = ["red", "blue", "green", "orange", "purple", "cyan", "magenta"]
        self.color = random.choice(colors)
        self.speed = random.randint(self.MIN_SPEED, self.MAX_SPEED)
        self.crossRoadChangeDirection = random.choice(["straight", "left", "right"])
        self.direction = random.choice(self.DIRECTIONS)
        self.has_turned = False

    def move(self):
        """
        Avance la voiture d'un pas selon sa direction.

        IMPORTANT : si 'self.is_stopped' est True (feu rouge devant elle OU
        voiture trop proche détectée par l'anti-collision de la Simulation),
        la méthode ne modifie ABSOLUMENT aucune coordonnée et retourne
        immédiatement.
        """
        if self.is_stopped:
            return

        if self.direction == "N":
            self.y -= self.speed
        elif self.direction == "S":
            self.y += self.speed
        elif self.direction == "E":
            self.x += self.speed
        elif self.direction == "O":
            self.x -= self.speed

    def stop(self):
        """Immobilise la voiture (feu rouge devant elle, ou voiture trop proche)."""
        self.is_stopped = True

    def resume(self):
        """Autorise à nouveau la voiture à avancer."""
        self.is_stopped = False

    def turn(self, new_direction):
        """
        Effectue un virage au centre du carrefour.

        - Change 'self.direction' vers 'new_direction'.
        - Pivote les dimensions visuelles (largeur/hauteur) UNIQUEMENT si
          l'axe de déplacement change réellement (un véhicule orienté
          Nord/Sud est dessiné "haut" ; un véhicule orienté Est/Ouest est
          dessiné "large"). Une trajectoire "straight" ne change pas d'axe
          et ne déclenche donc aucune inversion.
        - Réinitialise 'crossRoadChangeDirection' à "straight" et active le
          drapeau 'has_turned' pour empêcher toute boucle de virage tant que
          la voiture reste dans le carré central de l'intersection.
        """
        was_vertical = self.direction in ("N", "S")
        will_be_vertical = new_direction in ("N", "S")
        if was_vertical != will_be_vertical:
            self.width, self.height = self.height, self.width

        self.direction = new_direction
        self.crossRoadChangeDirection = "straight"
        self.has_turned = True

    def __repr__(self):
        return (f"Car(color={self.color!r}, x={self.x}, y={self.y}, "
                f"direction={self.direction!r}, is_stopped={self.is_stopped}, "
                f"has_turned={self.has_turned})")
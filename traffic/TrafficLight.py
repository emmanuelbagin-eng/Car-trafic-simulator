class TrafficLight:
    """
    Représente un feu de circulation individuel.
    L'attribut public 'color' reflète l'état courant du feu et est utilisé
    par la couche graphique (Simulation) pour dessiner le cercle correspondant.
    """

    def __init__(self, name="TrafficLight", x=0, y=0):
        self.name = name
        # Position sur le Canvas, utilisée pour dessiner le feu (cercle)
        self.x = x
        self.y = y
        # Etat par défaut : Rouge
        self.color = "Red"

    def authorizeLight(self):
        """Autorise le passage : le feu passe au Vert."""
        self.color = "Green"

    def stopLight(self):
        """Interdit le passage : le feu passe au Rouge."""
        self.color = "Red"

    def cautionLight(self):
        """Phase d'avertissement : le feu passe au Jaune."""
        self.color = "Yellow"

    def __repr__(self):
        return f"TrafficLight(name={self.name!r}, color={self.color!r})"
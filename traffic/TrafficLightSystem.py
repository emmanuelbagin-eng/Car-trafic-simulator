class TrafficLightSystem:
    """
    Orchestre les 4 feux du carrefour :
      - mbFeu : feu Main Bas    (route principale, sens Nord/Sud)
      - mtFeu : feu Main Haut   (route principale, sens Nord/Sud)
      - llFeu : feu Latéral Gauche (route latérale, sens Est/Ouest)
      - lrFeu : feu Latéral Droit  (route latérale, sens Est/Ouest)

    BUG CORRIGÉ : l'appel fantôme à 'self.launchTrafficLightSystem()' (méthode
    inexistante qui provoquait un crash immédiat) a été supprimé. Le système
    est désormais initialisé "à froid" : c'est l'appelant (Simulation) qui
    décide de l'état de départ via les méthodes ci-dessous.

    ROBUSTESSE AJOUTÉE : 'authorizeMainTraffic()' et 'authorizeLateralTraffic()'
    forcent désormais systématiquement l'axe perpendiculaire au Rouge AVANT
    de passer leur propre axe au Vert. Cette double sécurité garantit qu'il
    est structurellement impossible d'obtenir un état où le trafic principal
    et le trafic latéral sont Verts en même temps, même en cas d'appel
    incorrect ou désordonné depuis l'extérieur (ex: Simulation).
    """

    def __init__(self, mbFeu, mtFeu, llFeu, lrFeu):
        self.mbFeu = mbFeu
        self.mtFeu = mtFeu
        self.llFeu = llFeu
        self.lrFeu = lrFeu

    # --- Trafic principal (route verticale, Nord/Sud) ---

    def authorizeMainTraffic(self):
        """Passe le trafic principal au Vert.
        Sécurité : le trafic latéral est forcé au Rouge avant toute
        autorisation du trafic principal, pour éliminer tout risque de
        conflit Vert/Vert entre axes perpendiculaires."""
        self.stopLateralTraffic()
        self.mbFeu.authorizeLight()
        self.mtFeu.authorizeLight()

    def cautionMainTraffic(self):
        """Passe le trafic principal au Jaune."""
        self.mbFeu.cautionLight()
        self.mtFeu.cautionLight()

    def stopMainTraffic(self):
        """Passe le trafic principal au Rouge."""
        self.mbFeu.stopLight()
        self.mtFeu.stopLight()

    # --- Trafic latéral (route horizontale, Est/Ouest) ---

    def authorizeLateralTraffic(self):
        """Passe le trafic latéral au Vert.
        Sécurité symétrique : le trafic principal est forcé au Rouge avant
        toute autorisation du trafic latéral."""
        self.stopMainTraffic()
        self.llFeu.authorizeLight()
        self.lrFeu.authorizeLight()

    def cautionLateralTraffic(self):
        """Passe le trafic latéral au Jaune."""
        self.llFeu.cautionLight()
        self.lrFeu.cautionLight()

    def stopLateralTraffic(self):
        """Passe le trafic latéral au Rouge."""
        self.llFeu.stopLight()
        self.lrFeu.stopLight()

    # --- Helpers de lecture / validation d'état ---

    def get_main_color(self):
        return self.mbFeu.color

    def get_lateral_color(self):
        return self.llFeu.color

    def is_state_consistent(self):
        """
        Retourne True si aucun conflit n'existe entre les deux axes du
        carrefour, c'est-à-dire si le trafic principal et le trafic latéral
        ne sont JAMAIS Verts en même temps.

        Utile pour des tests unitaires ou une vérification défensive depuis
        la boucle d'animation de Simulation.
        """
        main_green = self.mbFeu.color == "Green" or self.mtFeu.color == "Green"
        lateral_green = self.llFeu.color == "Green" or self.lrFeu.color == "Green"
        return not (main_green and lateral_green)
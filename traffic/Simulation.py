import random
import time
import tkinter as tk

from .RoadSystem import RoadSystem
from .TrafficLight import TrafficLight
from .TrafficLightSystem import TrafficLightSystem
from .car import Car


class Simulation:
    """
    Application principale Tkinter du Traffic System.

    BUG CORRIGÉ : la classe n'était pas liée à Tkinter et instanciait
    'TrafficLightSystem()' sans lui passer les 4 feux requis (TypeError
    immédiat). Elle crée maintenant les 4 TrafficLight, les passe au
    TrafficLightSystem, dessine le carrefour sur un Canvas, fait apparaître
    des voitures à intervalle aléatoire et anime tout via une boucle
    récursive basée sur root.after().

    OPTIMISATIONS AJOUTÉES :
      - Nettoyage mémoire strict : toute voiture qui dépasse les limites du
        Canvas (+ marge OOB_MARGIN) est immédiatement et définitivement
        retirée de 'self.cars' (et de son rectangle Canvas associé).
      - Anti-collision basique : une voiture s'arrête non seulement si son
        feu est Rouge, mais aussi si une autre voiture la précède de trop
        près sur la même voie.
      - Timer d'animation à 30 ms (~33 FPS) pour une fluidité régulière,
        avec des durées de phases de feux recalculées en conséquence.
      - Logique de virage : au centre du carrefour, chaque voiture applique
        sa 'crossRoadChangeDirection' ("straight"/"left"/"right") pour
        changer de trajectoire, en respectant strictement la priorité des
        feux tricolores (le virage n'est évalué que lorsque la voiture est
        déjà engagée dans le carrefour, donc nécessairement au Vert).
      - CORRECTIF ANTI-COLLISION CROISÉE : ajout d'une phase "tout rouge" de
        dégagement entre chaque bascule d'axe (MAIN <-> LATERAL). Sans cette
        phase, une voiture encore engagée dans le carrefour au moment du
        changement de feu pouvait percuter une voiture qui démarrait juste
        sur l'axe perpendiculaire. Le "tout rouge" ne se lève désormais que
        lorsque le carrefour est physiquement vide (voir
        '_is_intersection_occupied'), avec un délai minimum incompressible
        et un garde-fou anti-blocage permanent.
      - CORRECTIF TIMING EN SECONDES RÉELLES : toutes les durées de phases
        (Vert, Jaune, tout-rouge) sont désormais mesurées avec
        'time.monotonic()', en secondes réelles, et non plus en comptant des
        frames d'animation. C'est plus fiable : la durée de sécurité du
        "tout rouge" ne dépend plus du rythme effectif de la boucle Tkinter.
      - CORRECTIF FUSION AU VIRAGE : deux voitures qui tournent en même temps
        depuis des directions opposées peuvent converger vers LA MÊME voie
        de sortie (ex: une voiture venant du Sud qui tourne à droite et une
        venant du Nord qui tourne à gauche aboutissent toutes les deux vers
        l'Est). Avant de valider un virage, '_is_turn_safe' vérifie
        désormais qu'aucune autre voiture n'occupe déjà la voie de
        destination à proximité du point de fusion ; si ce n'est pas le cas,
        la voiture patiente au centre du carrefour jusqu'à ce que la voie
        se libère, au lieu de se téléporter sur une voiture déjà présente.
    """

    CANVAS_SIZE = 600
    ROAD_WIDTH = 100
    FPS_DELAY_MS = 30  # ~33 FPS, cycle de feux synchronisé sur ce timer

    # Marge (en pixels) au-delà des limites du Canvas à partir de laquelle
    # une voiture est considérée comme définitivement sortie et doit être
    # supprimée de la mémoire (ex: x < -50 ou x > 650 pour un Canvas 600x600).
    OOB_MARGIN = 50

    # Distance de sécurité minimale (pixels) à respecter entre deux voitures
    # consécutives sur la même voie avant que la voiture de derrière ne
    # doive s'arrêter (anti-collision basique).
    SAFETY_GAP = 26

    # Durées des phases en SECONDES RÉELLES (et non plus en nombre de frames).
    # CORRECTIF FIABILITÉ : compter des "frames" d'animation pour mesurer un
    # délai de sécurité est fragile, car le rythme réel de la boucle
    # 'animation_loop' peut varier légèrement selon la charge de la machine.
    # On mesure désormais le temps écoulé avec 'time.monotonic()', ce qui
    # garantit des durées fiables en secondes, indépendamment du nombre de
    # frames effectivement écoulées.
    PHASE_DURATIONS = {
        "MAIN_GREEN": 5.0,     # secondes
        "MAIN_YELLOW": 2.0,    # secondes
        "LATERAL_GREEN": 5.0,  # secondes
        "LATERAL_YELLOW": 2.0,  # secondes
    }

    # --- Phases "tout rouge" de dégagement (clearance interval) ---
    # CORRECTIF COLLISION (axes perpendiculaires) : sans cette phase
    # intermédiaire, une voiture encore engagée dans le carrefour au moment
    # où le feu bascule pour l'autre axe se retrouve nez à nez avec une
    # voiture qui vient juste de démarrer sur l'axe perpendiculaire. Le
    # "tout rouge" impose un délai minimum, EN SECONDES RÉELLES, où LES DEUX
    # axes sont Rouges, et ne se lève que lorsque le carrefour est
    # physiquement vide de toute voiture (vérifié par
    # '_is_intersection_occupied'). 'ALL_RED_MAX_DURATION' est un garde-fou
    # anti-blocage si une voiture restait bloquée indéfiniment.
    ALL_RED_MIN_DURATION = 1.5   # secondes minimum, quoi qu'il arrive
    ALL_RED_MAX_DURATION = 4.0   # secondes maximum (sécurité anti-deadlock)

    # Table des transitions : phase courante -> phase suivante.
    PHASE_ORDER = {
        "MAIN_GREEN": "MAIN_YELLOW",
        "MAIN_YELLOW": "ALL_RED_TO_LATERAL",
        "ALL_RED_TO_LATERAL": "LATERAL_GREEN",
        "LATERAL_GREEN": "LATERAL_YELLOW",
        "LATERAL_YELLOW": "ALL_RED_TO_MAIN",
        "ALL_RED_TO_MAIN": "MAIN_GREEN",
    }

    LIGHT_COLOR_MAP = {"Red": "red", "Yellow": "#f5d800", "Green": "#21c521"}

    # Table de virage : pour chaque direction d'ARRIVÉE de la voiture, donne
    # la nouvelle direction selon son choix "straight" / "left" / "right".
    TURN_MAP = {
        "N": {"straight": "N", "left": "O", "right": "E"},  # vient du Sud
        "S": {"straight": "S", "left": "E", "right": "O"},  # vient du Nord
        "E": {"straight": "E", "left": "N", "right": "S"},  # vient de l'Ouest
        "O": {"straight": "O", "left": "S", "right": "N"},  # vient de l'Est
    }

    def __init__(self):
        self.running = True

        self.road_system = RoadSystem(
            width=self.CANVAS_SIZE, height=self.CANVAS_SIZE, road_width=self.ROAD_WIDTH
        )

        # Géométrie du carrefour, calculée une seule fois et réutilisée
        # partout (spawn, alignement de voie, détection du centre, etc.)
        self.cx = self.CANVAS_SIZE // 2
        self.half = self.ROAD_WIDTH // 2
        self.road_min = self.cx - self.half   # 250
        self.road_max = self.cx + self.half   # 350

        # Position (en pixels) de chaque voie de circulation, utilisée à la
        # fois pour le "spawn" des voitures et pour leur réalignement après
        # un virage au centre du carrefour.
        self.lane_x = {
            "S": self.cx - self.half / 2,  # voie de gauche du sens Nord/Sud (275)
            "N": self.cx + self.half / 2,  # voie de droite du sens Nord/Sud (325)
        }
        self.lane_y = {
            "O": self.cx - self.half / 2,  # voie du haut du sens Est/Ouest (275)
            "E": self.cx + self.half / 2,  # voie du bas du sens Est/Ouest (325)
        }

        # --- Fenêtre principale & Canvas ---
        self.root = tk.Tk()
        self.root.title("Traffic System Simulation")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.canvas = tk.Canvas(
            self.root,
            width=self.CANVAS_SIZE,
            height=self.CANVAS_SIZE,
            bg="#0b3d0b",  # vert sombre
            highlightthickness=0,
        )
        self.canvas.pack()

        # --- Création des 4 feux et du système de feux ---
        cx, half = self.cx, self.half
        self.mbFeu = TrafficLight(name="MainBas", x=cx + half + 20, y=cx + half + 20)
        self.mtFeu = TrafficLight(name="MainHaut", x=cx - half - 20, y=cx - half - 20)
        self.llFeu = TrafficLight(name="LateralGauche", x=cx - half - 20, y=cx + half + 20)
        self.lrFeu = TrafficLight(name="LateralDroit", x=cx + half + 20, y=cx - half - 20)

        self.traffic_light_system = TrafficLightSystem(
            self.mbFeu, self.mtFeu, self.llFeu, self.lrFeu
        )

        # Etat de départ explicite : trafic principal prioritaire au lancement.
        # On passe par '_enter_phase' (et non un appel direct) pour que
        # l'initialisation suive exactement la même logique que le reste du
        # cycle de vie des feux.
        self.phase = None
        self.phase_start_time = 0.0
        self._enter_phase("MAIN_GREEN")

        # --- Voitures ---
        self.cars = []
        self.car_visuals = {}  # Car -> id de l'objet rectangle sur le Canvas

        # --- Dessin initial ---
        self.draw_roads_tk()
        self.light_visuals = {}
        self._draw_lights_init()

        # --- Lancement des boucles ---
        self.spawn_car()
        self.animation_loop()

        self.root.mainloop()

    # ------------------------------------------------------------------
    # Dessin statique du décor
    # ------------------------------------------------------------------

    def draw_roads_tk(self):
        """Dessine l'intersection : route verticale, route horizontale et
        lignes médianes blanches pointillées (le fond vert sombre du Canvas
        sert d'herbe)."""
        size = self.CANVAS_SIZE
        road_x1, road_x2 = self.road_min, self.road_max  # 250, 350
        road_y1, road_y2 = self.road_min, self.road_max

        road_color = "#3d3d3d"
        line_color = "#2a2a2a"

        # Route verticale (axe Nord/Sud)
        self.canvas.create_rectangle(
            road_x1, 0, road_x2, size, fill=road_color, outline=line_color
        )
        # Route horizontale (axe Est/Ouest)
        self.canvas.create_rectangle(
            0, road_y1, size, road_y2, fill=road_color, outline=line_color
        )
        # Carré central de l'intersection (par-dessus, légèrement plus clair)
        self.canvas.create_rectangle(
            road_x1, road_y1, road_x2, road_y2, fill="#454545", outline=line_color
        )

        # Lignes médianes blanches pointillées
        dash_pattern = (12, 10)
        cx = self.cx
        self.canvas.create_line(cx, 0, cx, road_y1, fill="white", width=2, dash=dash_pattern)
        self.canvas.create_line(cx, road_y2, cx, size, fill="white", width=2, dash=dash_pattern)
        self.canvas.create_line(0, cx, road_x1, cx, fill="white", width=2, dash=dash_pattern)
        self.canvas.create_line(road_x2, cx, size, cx, fill="white", width=2, dash=dash_pattern)

    def _draw_lights_init(self):
        radius = 9
        for feu in (self.mbFeu, self.mtFeu, self.llFeu, self.lrFeu):
            circle_id = self.canvas.create_oval(
                feu.x - radius, feu.y - radius, feu.x + radius, feu.y + radius,
                fill=self._light_color(feu.color), outline="black", width=2,
            )
            self.light_visuals[feu.name] = circle_id

    def _light_color(self, color_name):
        return self.LIGHT_COLOR_MAP.get(color_name, "gray")

    def _update_lights_visuals(self):
        for feu in (self.mbFeu, self.mtFeu, self.llFeu, self.lrFeu):
            circle_id = self.light_visuals[feu.name]
            self.canvas.itemconfig(circle_id, fill=self._light_color(feu.color))

    # ------------------------------------------------------------------
    # Cycle logique des feux (Vert -> Jaune -> Vert -> Jaune ...)
    # ------------------------------------------------------------------

    def _update_light_cycle(self):
        """
        Fait progresser le cycle des feux en fonction du temps RÉEL écoulé
        (secondes), mesuré avec 'time.monotonic()' — et non plus en
        comptant des frames d'animation, ce qui rendait la durée de
        sécurité du "tout rouge" dépendante du rythme effectif de la
        boucle Tkinter.

        Pour les phases normales (GREEN/YELLOW), la transition se fait à
        durée fixe (en secondes), comme avant.

        Pour les phases "ALL_RED_TO_LATERAL" / "ALL_RED_TO_MAIN", la
        transition est conditionnée à DEUX critères :
          1) un délai minimum incompressible (ALL_RED_MIN_DURATION, en
             secondes réelles) s'est écoulé, ET
          2) le carrefour est physiquement vide de toute voiture
             ('_is_intersection_occupied()' retourne False) ;
        SAUF si le délai maximum (ALL_RED_MAX_DURATION) est atteint, auquel
        cas la transition est forcée par sécurité (anti-blocage permanent).
        """
        elapsed = time.monotonic() - self.phase_start_time

        if self.phase in ("ALL_RED_TO_LATERAL", "ALL_RED_TO_MAIN"):
            min_elapsed = elapsed >= self.ALL_RED_MIN_DURATION
            max_elapsed = elapsed >= self.ALL_RED_MAX_DURATION
            intersection_clear = not self._is_intersection_occupied()

            if max_elapsed or (min_elapsed and intersection_clear):
                self._enter_phase(self.PHASE_ORDER[self.phase])
            return

        duration = self.PHASE_DURATIONS[self.phase]
        if elapsed >= duration:
            self._enter_phase(self.PHASE_ORDER[self.phase])

    def _enter_phase(self, new_phase):
        """
        Fait entrer le système dans 'new_phase' : relève l'horodatage de
        départ de phase ('time.monotonic()') et applique l'action
        correspondante sur les feux. Centralise TOUTES les transitions (y
        compris l'état initial) pour qu'il n'existe qu'un seul endroit où
        l'on décide "que faire des feux" à chaque phase.
        """
        self.phase = new_phase
        self.phase_start_time = time.monotonic()

        if new_phase == "MAIN_GREEN":
            self.traffic_light_system.authorizeMainTraffic()
        elif new_phase == "MAIN_YELLOW":
            self.traffic_light_system.cautionMainTraffic()
        elif new_phase == "ALL_RED_TO_LATERAL":
            self.traffic_light_system.stopMainTraffic()
        elif new_phase == "LATERAL_GREEN":
            self.traffic_light_system.authorizeLateralTraffic()
        elif new_phase == "LATERAL_YELLOW":
            self.traffic_light_system.cautionLateralTraffic()
        elif new_phase == "ALL_RED_TO_MAIN":
            self.traffic_light_system.stopLateralTraffic()

        # Vérification défensive : à tout instant, les deux axes
        # perpendiculaires ne doivent jamais être Verts simultanément.
        assert self.traffic_light_system.is_state_consistent(), (
            "Etat incohérent détecté : conflit Vert/Vert entre axes perpendiculaires"
        )

    def _is_intersection_occupied(self):
        """
        Retourne True si au moins une voiture se trouve physiquement à
        l'intérieur du carré central du carrefour (zone road_min-road_max en
        X ET en Y). Utilisé pour décider si l'on peut, sans risque, donner
        le Vert à l'axe perpendiculaire (cf. phases ALL_RED_*).
        """
        for car in self.cars:
            if self.road_min <= car.x <= self.road_max and self.road_min <= car.y <= self.road_max:
                return True
        return False

    # ------------------------------------------------------------------
    # Génération ("spawn") des voitures
    # ------------------------------------------------------------------

    def spawn_car(self):
        if not self.running:
            return

        size = self.CANVAS_SIZE
        margin = 30

        direction = random.choice(Car.DIRECTIONS)
        colors = ["#e74c3c", "#3498db", "#f39c12", "#9b59b6", "#1abc9c", "#e67e22"]
        speed = random.randint(Car.MIN_SPEED, Car.MAX_SPEED)

        car = Car(
            color=random.choice(colors),
            width=18,
            height=18,
            speed=speed,
            crossRoadChangeDirection=random.choice(["straight", "straight", "left", "right"]),
        )
        car.direction = direction

        if direction == "S":  # apparaît en haut, se dirige vers le bas
            car.x = self.lane_x["S"]
            car.y = -margin
        elif direction == "N":  # apparaît en bas, se dirige vers le haut
            car.x = self.lane_x["N"]
            car.y = size + margin
        elif direction == "E":  # apparaît à gauche, se dirige vers la droite
            car.x = -margin
            car.y = self.lane_y["E"]
        elif direction == "O":  # apparaît à droite, se dirige vers la gauche
            car.x = size + margin
            car.y = self.lane_y["O"]

        self.cars.append(car)
        rect_id = self.canvas.create_rectangle(0, 0, 0, 0, fill=car.color, outline="black")
        self.car_visuals[car] = rect_id
        self._update_car_visual(car)

        next_spawn_ms = int(random.uniform(1.5, 2.0) * 1000)
        self.root.after(next_spawn_ms, self.spawn_car)

    # ------------------------------------------------------------------
    # Feux : la voiture doit-elle s'arrêter avant l'intersection ?
    # ------------------------------------------------------------------

    def _is_light_green_for(self, car):
        if car.direction in ("N", "S"):
            return self.mbFeu.color == "Green"
        return self.llFeu.color == "Green"

    def _is_approaching_intersection(self, car):
        """
        Retourne True si la voiture est encore AVANT le carrefour (zone de
        freinage), selon sa direction d'arrivée. Dès qu'elle est entrée dans
        le carré central, elle n'est plus "en approche" : la priorité
        absolue du feu rouge ne s'applique qu'avant l'engagement.
        """
        stop_margin = 45

        if car.direction == "S":
            return (self.road_min - stop_margin) <= car.y < self.road_min
        if car.direction == "N":
            return self.road_max < car.y <= (self.road_max + stop_margin)
        if car.direction == "E":
            return (self.road_min - stop_margin) <= car.x < self.road_min
        if car.direction == "O":
            return self.road_max < car.x <= (self.road_max + stop_margin)
        return False

    # ------------------------------------------------------------------
    # Anti-collision basique : distance de sécurité sur la même voie
    # ------------------------------------------------------------------

    def _car_ahead_too_close(self, car):
        """
        Retourne True si une autre voiture, circulant dans la MÊME direction
        et alignée sur la MÊME voie, se trouve devant 'car' à une distance
        inférieure à SAFETY_GAP. Empêche les voitures de se chevaucher ou de
        s'empiler les unes sur les autres.
        """
        lane_tolerance = 5  # tolérance d'alignement (pixels) sur l'axe perpendiculaire

        for other in self.cars:
            if other is car or other.direction != car.direction:
                continue

            if car.direction in ("N", "S"):
                if abs(other.x - car.x) > lane_tolerance:
                    continue
                if car.direction == "S" and other.y > car.y:
                    gap = other.y - car.y - (car.height / 2 + other.height / 2)
                    if gap < self.SAFETY_GAP:
                        return True
                elif car.direction == "N" and other.y < car.y:
                    gap = car.y - other.y - (car.height / 2 + other.height / 2)
                    if gap < self.SAFETY_GAP:
                        return True
            else:  # "E" ou "O"
                if abs(other.y - car.y) > lane_tolerance:
                    continue
                if car.direction == "E" and other.x > car.x:
                    gap = other.x - car.x - (car.width / 2 + other.width / 2)
                    if gap < self.SAFETY_GAP:
                        return True
                elif car.direction == "O" and other.x < car.x:
                    gap = car.x - other.x - (car.width / 2 + other.width / 2)
                    if gap < self.SAFETY_GAP:
                        return True

        return False

    # ------------------------------------------------------------------
    # Virage au centre du carrefour
    # ------------------------------------------------------------------

    def _reached_center(self, car):
        """Retourne True si la voiture a atteint (ou dépassé) le centre exact
        du carrefour (x=300 ou y=300), selon sa direction de provenance."""
        if car.direction == "N":
            return car.y <= self.cx
        if car.direction == "S":
            return car.y >= self.cx
        if car.direction == "E":
            return car.x >= self.cx
        if car.direction == "O":
            return car.x <= self.cx
        return False

    def _align_to_lane(self, car, new_direction):
        """Replace la voiture sur la voie correspondant à sa nouvelle
        direction, et la recentre sur l'axe perpendiculaire pour une
        transition visuelle propre au moment du virage."""
        if new_direction in ("N", "S"):
            car.x = self.lane_x[new_direction]
            car.y = self.cx
        else:
            car.y = self.lane_y[new_direction]
            car.x = self.cx

    def _is_turn_safe(self, car, new_direction):
        """
        CORRECTIF FUSION : retourne False s'il existe déjà une autre voiture
        sur la voie de DESTINATION ('new_direction'), trop proche du point
        d'insertion (centre du carrefour), ce qui éviterait que deux
        voitures convergent au même endroit au même instant.

        Cas concret : une voiture venant du Sud qui tourne à droite et une
        voiture venant du Nord qui tourne à gauche aboutissent TOUTES LES
        DEUX en direction "E" (Est). Sans cette vérification, elles se
        seraient téléportées exactement sur les mêmes coordonnées au moment
        du virage.
        """
        if new_direction in ("N", "S"):
            target_x = self.lane_x[new_direction]
            target_y = self.cx
        else:
            target_y = self.lane_y[new_direction]
            target_x = self.cx

        for other in self.cars:
            if other is car or other.direction != new_direction:
                continue

            if new_direction in ("N", "S"):
                if abs(other.x - target_x) > 5:
                    continue
                if abs(other.y - target_y) < (self.SAFETY_GAP + max(car.height, other.height) / 2):
                    return False
            else:
                if abs(other.y - target_y) > 5:
                    continue
                if abs(other.x - target_x) < (self.SAFETY_GAP + max(car.width, other.width) / 2):
                    return False

        return True

    def _must_wait_before_turning(self, car):
        """
        Retourne True si la voiture a atteint le centre du carrefour, qu'elle
        s'apprête à tourner (donc à changer d'axe), MAIS que la voie de
        destination n'est pas encore sûre (cf. '_is_turn_safe'). Dans ce
        cas, la voiture doit patienter au centre — sans pour autant que
        'has_turned' soit activé — jusqu'à ce que la voie se libère.
        """
        if car.has_turned:
            return False
        if not self._reached_center(car):
            return False

        new_direction = self.TURN_MAP[car.direction][car.crossRoadChangeDirection]
        if new_direction == car.direction:
            return False  # trajectoire "straight" : rien à attendre

        return not self._is_turn_safe(car, new_direction)

    def _handle_turn(self, car):
        """
        Applique la règle de virage UNIQUEMENT lorsque :
          1) la voiture n'a pas déjà tourné pour cette traversée
             (car.has_turned est False), et
          2) elle a atteint le centre du carrefour.

        Une voiture ne peut donc jamais décider de tourner avant d'être
        engagée dans l'intersection : tant qu'elle est en phase d'approche,
        c'est la priorité du feu rouge (_is_approaching_intersection) qui
        prévaut et l'empêche d'avancer jusqu'au centre.

        NOTE : cette méthode n'est appelée par '_update_car_state' que
        lorsque '_must_wait_before_turning' a déjà confirmé que la voie de
        destination est sûre — le virage effectif ne peut donc jamais créer
        de chevauchement avec une voiture déjà présente sur cette voie.
        """
        if car.has_turned:
            return
        if not self._reached_center(car):
            return

        new_direction = self.TURN_MAP[car.direction][car.crossRoadChangeDirection]

        if new_direction != car.direction:
            car.turn(new_direction)
            self._align_to_lane(car, new_direction)
        else:
            # Trajectoire "straight" : pas de changement de direction, mais on
            # marque tout de même le passage du centre pour éviter toute
            # réévaluation inutile à chaque frame suivante.
            car.has_turned = True
            car.crossRoadChangeDirection = "straight"

    # ------------------------------------------------------------------
    # Mise à jour d'état et affichage d'une voiture
    # ------------------------------------------------------------------

    def _update_car_state(self, car):
        must_stop_for_light = (
            self._is_approaching_intersection(car) and not self._is_light_green_for(car)
        )
        must_stop_for_traffic = self._car_ahead_too_close(car)
        must_wait_for_turn = self._must_wait_before_turning(car)

        if must_stop_for_light or must_stop_for_traffic or must_wait_for_turn:
            car.stop()
            return

        car.resume()
        self._handle_turn(car)
        car.move()

    def _update_car_visual(self, car):
        rect_id = self.car_visuals[car]
        half_w, half_h = car.width / 2, car.height / 2
        self.canvas.coords(
            rect_id,
            car.x - half_w, car.y - half_h,
            car.x + half_w, car.y + half_h,
        )

    def _is_out_of_bounds(self, car):
        """
        Retourne True si la voiture a définitivement quitté le Canvas
        (au-delà de OOB_MARGIN pixels hors de ses limites). Utilisé pour la
        purge mémoire de 'self.cars' afin d'éviter tout ralentissement de
        l'application après plusieurs minutes d'exécution.
        """
        margin = self.OOB_MARGIN
        size = self.CANVAS_SIZE
        return (
            car.x < -margin or car.x > size + margin
            or car.y < -margin or car.y > size + margin
        )

    # ------------------------------------------------------------------
    # Boucle d'animation principale (~30 ms / ~33 FPS)
    # ------------------------------------------------------------------

    def animation_loop(self):
        if not self.running:
            return

        # 1. Cycle logique des feux, synchronisé sur le même timer que
        #    le défilement visuel des voitures.
        self._update_light_cycle()
        self._update_lights_visuals()

        # 2. Déplacement de chaque voiture (feux + anti-collision + virage)
        #    et redessin de son rectangle sur le Canvas.
        cars_to_remove = []
        for car in self.cars:
            self._update_car_state(car)
            self._update_car_visual(car)
            if self._is_out_of_bounds(car):
                cars_to_remove.append(car)

        # 3. Nettoyage mémoire strict : suppression DÉFINITIVE des voitures
        #    sorties du Canvas, à la fois de la liste 'self.cars' et de leur
        #    rectangle sur le Canvas, afin de ne jamais laisser grossir la
        #    mémoire au fil du temps.
        for car in cars_to_remove:
            rect_id = self.car_visuals.pop(car)
            self.canvas.delete(rect_id)
            self.cars.remove(car)

        self.root.after(self.FPS_DELAY_MS, self.animation_loop)

    # ------------------------------------------------------------------
    # Fermeture propre de l'application
    # ------------------------------------------------------------------

    def on_close(self):
        self.running = False
        self.root.destroy()
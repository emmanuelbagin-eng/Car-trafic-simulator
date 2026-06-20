class RoadSystem:
    """
    Représente la géométrie du carrefour : une route verticale (axe Nord/Sud)
    et une route horizontale (axe Est/Ouest) qui se croisent au centre du Canvas.
    """

    def __init__(self, width=600, height=600, road_width=100):
        self.width = width
        self.height = height
        self.road_width = road_width

        half = road_width // 2
        center_x = width // 2
        center_y = height // 2

        # (x1, y1, x2, y2) de la route verticale
        self.vertical_road = (center_x - half, 0, center_x + half, height)
        # (x1, y1, x2, y2) de la route horizontale
        self.horizontal_road = (0, center_y - half, width, center_y + half)

        # Zone exacte de l'intersection (carré central)
        self.intersection = (
            center_x - half,
            center_y - half,
            center_x + half,
            center_y + half,
        )

    def get_vertical_bounds(self):
        return self.vertical_road

    def get_horizontal_bounds(self):
        return self.horizontal_road

    def get_intersection_bounds(self):
        return self.intersection

    def is_inside_intersection(self, x, y):
        x1, y1, x2, y2 = self.intersection
        return x1 <= x <= x2 and y1 <= y <= y2
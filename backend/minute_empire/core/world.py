
class World:
    QUADRANT_SIZE = 15
    MAP_SIZE = QUADRANT_SIZE * 2 + 1

    def get_map_bounds(self):
        # Should go from -15 to 15
        x_min = - self.QUADRANT_SIZE
        x_max = self.QUADRANT_SIZE
        y_min = - self.QUADRANT_SIZE
        y_max = self.QUADRANT_SIZE
        return x_min, x_max, y_min, y_max
    
    def get_total_map_slots(self):
        return (self.QUADRANT_SIZE*2+1) * (self.QUADRANT_SIZE+1)

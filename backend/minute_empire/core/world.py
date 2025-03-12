class World:
    # Class constants
    QUADRANT_SIZE = 15
    MAP_SIZE = QUADRANT_SIZE * 2 + 1

    @classmethod
    def get_map_bounds(cls):
        # Should go from -15 to 15
        x_min = - cls.QUADRANT_SIZE
        x_max = cls.QUADRANT_SIZE
        y_min = - cls.QUADRANT_SIZE
        y_max = cls.QUADRANT_SIZE
        return x_min, x_max, y_min, y_max
    
    @classmethod
    def get_total_map_slots(cls):
        return (cls.QUADRANT_SIZE*2+1) * (cls.QUADRANT_SIZE+1)

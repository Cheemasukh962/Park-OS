"""Walking distances between class buildings and lots: Google's real walks where we have them,
the straight line otherwise. Used by the reminder planner, which needs many building-lot pairs."""
from parking.data import feature_id
from parking.geo import distance
from parking.google_routes import as_metres, real_walks
from parking.ranking import nearest_lots


class WalkTable:
    def __init__(self, buildings, lots, affiliation, walk_limit_min):
        # Ask Google (or the cache) once per building, for the lots near it.
        # hour=23 covers every lot this user could ever use, so later classes are included too
        self.real = {}                                       # (building id, lot id) → (seconds, route metres)
        for building in buildings:
            candidates = nearest_lots(building, lots, affiliation, 23)
            answers = real_walks(building, f"b{feature_id(building)}", candidates, walk_limit_min)
            for lot_id, answer in answers.items():
                self.real[(feature_id(building), lot_id)] = answer

    def metres(self, building, lot):
        # Same units as geo.distance(), so it can be passed to the planner as walk=
        answer = self.real.get((feature_id(building), feature_id(lot)))
        return as_metres(answer[0]) if answer else distance(building, lot)

    def route_metres(self, building, lot):
        # Google's walking route length if known, otherwise the straight line
        answer = self.real.get((feature_id(building), feature_id(lot)))
        return answer[1] if answer else distance(building, lot)

    def is_real(self, building, lot):
        return (feature_id(building), feature_id(lot)) in self.real

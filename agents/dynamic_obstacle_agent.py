
class DynamicObstacleAgent:
    """Coordinates dynamic-obstacle requests and validates replanned paths."""

    def __init__(self):
        self.last_obstacle = None
        self.last_status = "idle"

    def validate_paths(self, paths, obstacle):
        """Reject paths that enter the newly added obstacle."""
        x, y = obstacle

        if not isinstance(paths, dict) or not paths:
            self.last_status = "invalid_paths"
            return False

        for robot_id, path in paths.items():
            if not isinstance(path, list):
                self.last_status = "invalid_paths"
                return False

            for position in path:
                if (
                    not isinstance(position, (list, tuple))
                    or len(position) != 2
                ):
                    self.last_status = "invalid_paths"
                    return False

                if position[0] == x and position[1] == y:
                    self.last_status = "unsafe_path"
                    return False

        self.last_obstacle = (x, y)
        self.last_status = "validated"
        return True

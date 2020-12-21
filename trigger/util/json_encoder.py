import dataclasses
from enum import Enum
import json
from trigger.train.scoring_calculator import ScoringCalculator

import numpy


class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return { o.__class__.__name__ : dataclasses.asdict(o) } 
            if isinstance(o, Enum):
                return o.name
            if type(o).__module__ == numpy.__name__:
                if isinstance(o, numpy.ndarray):
                    return o.tolist()
                else:
                    return o.item()
            if isinstance(o, ScoringCalculator):
                return o.describe()
            return super().default(o)
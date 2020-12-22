from trigger.scoring import ScoringCalculator, Scoring
from trigger.test.match import eval_matches
from trigger.test.cluster import eval_cluster
from trigger.operations import AddInfo, CalculateMatchesInfo, CalculateScoringInfo, EvaluateClustersAndMatchesInfo, EvaluateClustersInfo, EvaluateMatchesInfo, Operation, OperationType, RemoveInfo, UpdateInfo
from trigger.transformers.transformer_pipeline import Instance, TransformerPipeline
from trigger.clusters.processor import Processor

import numpy

from typing import Any, Dict, List, Optional

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('trigger_interface')
logger.setLevel(logging.INFO)

class TriggerInterface:
    def __init__(
        self,
        processor: Processor,
        transformers: Dict[str, TransformerPipeline],
        scoring_calculator: ScoringCalculator = ScoringCalculator()
    ) -> None:
        self.processor: Processor = processor
        self.transformers: Dict[str, TransformerPipeline] = transformers
        self.scoring_calculator = scoring_calculator
        self.instances_map: Dict[str, Instance] = {}

    def find_transformer_for_key(self, key: str) -> Optional[TransformerPipeline]:
        transformer = self.transformers.get(key, None)

        if transformer is None:
            logger.warning(f"No transformer with key='{key}'")
        
        return transformer

    def create_instance_or_none(self, transformer_key: Optional[str], value: Any) -> Optional[Instance]:

        if transformer_key is None:
            assert isinstance(value, numpy.ndarray)
            return Instance(value, value)

        transformer = self.find_transformer_for_key(transformer_key)

        if transformer is None:
            return None

        return transformer.transform(value)

    def create_instances_filter_none(self, transformer_keys: List[Optional[str]], values: List[Any]) -> List[Instance]:
        instances = [
            self.create_instance_or_none(transformer_key, value)
            for transformer_key, value in zip(transformer_keys, values)
        ]

        return list(filter(None, instances)) 

    def add(self, tags: List[str], transformer_keys: List[Optional[str]], values: List[Any]) -> None:
        instances = self.create_instances_filter_none(transformer_keys, values)
        
        for tag, instance in zip(tags, instances):
            self.add_instance(tag, instance)

    def add_instance(self, tag: str, instance: Instance) -> None:
        self.processor.process(tag, instance.embedding)
        self.instances_map[tag] = instance

    def update(self, tags: List[str], transformer_keys: List[Optional[str]], values: List[Any]) -> bool:
        instances = self.create_instances_filter_none(transformer_keys, values)
        
        for tag, instance in zip(tags, instances):
            if not self.update_instance(tag, instance):
                return False

        return True

    def update_instance(self, tag: str, instance: Instance) -> bool:
        if not tag in self.instances_map:
            return False
        
        self.processor.update(tag, instance.embedding)
        self.instances_map[tag] = instance

        return True

    def remove(self, tags: List[str]) -> None:
        for tag in tags:
            self.processor.remove(tag)
            del self.instances_map[tag]

    def get_scorings_for(self, transformer_keys: List[Optional[str]], values: List[Any]) -> List[List[Scoring]]:
        instances = self.create_instances_filter_none(transformer_keys, values)
        
        return [
            self.get_scorings_for_instance(instance)
            for instance in instances
        ]
            

    def get_scorings_for_instance(self, instance: Instance) -> List[Scoring]:
        
        if len(self.instances_map) == 0:
            return []

        would_be_cluster_id = self.processor.predict(instance.embedding)

        tags = self.processor.get_tags_in_cluster(would_be_cluster_id)

        temp = [
            self.calculate_scoring_between_instance_and_tag_or_none(instance, tag)
            for tag in tags
        ]

        return list(filter(None, temp))

    
    def get_matches_for(self, transformer_keys: List[Optional[str]], values: List[Any]) -> List[List[Scoring]]:
        instances = self.create_instances_filter_none(transformer_keys, values)

        return [
            self.get_matches_for_instance(instance)
            for instance in instances
        ]
    
    def get_matches_for_instance(self, instance: Instance) -> List[Scoring]:

        scorings = self.get_scorings_for_instance(instance)

        return [
            scoring
            for scoring in scorings
            if scoring.is_match
        ]

    def calculate_scorings_between_values_and_tags(self, transformer_keys: List[Optional[str]], values: List[Any], tags: List[str]) -> List[Scoring]:
        instances = self.create_instances_filter_none(transformer_keys, values)

        temp = [
            self.calculate_scoring_between_instance_and_tag_or_none(instance, tag)
            for tag, instance in zip(tags, instances)
        ]

        return list(filter(None, temp))

    def calculate_scoring_between_instance_and_tag_or_none(self, instance: Instance, tag: str) -> Optional[Scoring]:
        instances = self.get_instances_by_tag([tag])

        if len(instances) == 0:
            return None

        instance2 = instances[0]

        return self.calculate_scoring_between_instances(instance, tag, instance2)

    def calculate_scoring_between_instances(self, instance1: Instance, tag2: str, instance2: Instance) -> Scoring:
        return self.scoring_calculator(instance1, tag2, instance2)
    
    
    def get_instances_by_tag(self, tags: List[str]) -> List[Instance]:
        temp = [
            self.instances_map.get(tag, None)
            for tag in tags
        ]

        return list(filter(None, temp))

    def on_operation(self, operation: Operation):
        if operation.type == OperationType.ADD:
            add_info: AddInfo = operation.info
            self.add([add_info.tag], [add_info.transformer_key], [add_info.value])

        elif operation.type == OperationType.REMOVE:
            remove_info: RemoveInfo = operation.info
            self.remove([remove_info.tag])

        elif operation.type == OperationType.UPDATE:
            update_info: UpdateInfo = operation.info
            self.update([update_info.tag], [update_info.transformer_key], [update_info.value])

        elif operation.type == OperationType.CALCULATE_SCORES:
            calculate_scoring_info: CalculateScoringInfo = operation.info
            return self.get_scorings_for(
                [calculate_scoring_info.transformer_key],
                [calculate_scoring_info.value],
            )[0]

        elif operation.type == OperationType.CALCULATE_MATCHES:
            calculate_matches_info: CalculateMatchesInfo = operation.info
            return self.get_matches_for([calculate_matches_info.transformer_key], [calculate_matches_info.value])[0]
            
        elif operation.type == OperationType.EVALUATE_CLUSTERS:
            evaluate_clusters_info: EvaluateClustersInfo = operation.info
            return eval_cluster(self)
            
        elif operation.type == OperationType.EVALUATE_MATCHES:

            evaluate_matches_info: EvaluateMatchesInfo = operation.info
            matches = eval_matches(self, evaluate_matches_info.values, )
            if not evaluate_matches_info.fetch_instance:
                del matches["by_value"]
            return matches
            
        elif operation.type == OperationType.EVALUATE_CLUSTERS_AND_MATCHES:
            evaluate_clusters_and_matches_info: EvaluateClustersAndMatchesInfo = operation.info

            clusters_evaluation = eval_cluster(self)
            matches_evaluation = eval_matches(self, evaluate_clusters_and_matches_info.values)

            if not evaluate_clusters_and_matches_info.fetch_instance:
                del matches_evaluation["by_value"]

            results = clusters_evaluation
            results['matches_results'] = matches_evaluation

            return results

    def describe(self) -> Dict[str, Any]:
        return {
            "transformers": self.transformers,
            "scoring_calculator": self.scoring_calculator
        }
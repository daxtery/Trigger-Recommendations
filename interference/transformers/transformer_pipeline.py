from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar
from typing_extensions import Protocol

import numpy

T = TypeVar('T')

@dataclass
class Instance(Generic[T]):
    value: T
    embedding: numpy.ndarray = field(repr=False)

class TransformerPipeline(Protocol, Generic[T]):

    @abstractmethod
    def transform(self, value: T) -> Instance[T]:...


class NumpyToInstancePipeline(TransformerPipeline[numpy.ndarray]):

    def transform(self, numpy_array: numpy.ndarray) -> Instance[numpy.ndarray]:
        assert isinstance(numpy_array, numpy.ndarray)
        return Instance(numpy_array, numpy_array)
    
class IdentityPipeline(TransformerPipeline[T]):

    def transform(self, instance: Instance[T]) -> Instance[T]:
        assert hasattr(instance, 'value')
        assert hasattr(instance, 'embedding')
        return instance
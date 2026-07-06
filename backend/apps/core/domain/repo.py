"""
Repository pattern for DDD.
Abstracts persistence from domain logic.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic
from django.db import models

T = TypeVar('T', bound=models.Model)


class Repository(ABC, Generic[T]):
    """Base repository interface."""

    @abstractmethod
    def get(self, id) -> Optional[T]:
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        pass

    @abstractmethod
    def add(self, entity: T) -> T:
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        pass

    @abstractmethod
    def delete(self, id) -> bool:
        pass

    @abstractmethod
    def exists(self, id) -> bool:
        pass


class DjangoRepository(Repository[T]):
    """Generic Django ORM repository implementation."""

    def __init__(self, model_class: type):
        self._model = model_class

    def get(self, id) -> Optional[T]:
        try:
            return self._model.objects.get(pk=id)
        except self._model.DoesNotExist:
            return None

    def get_all(self) -> List[T]:
        return list(self._model.objects.all())

    def add(self, entity: T) -> T:
        entity.save()
        return entity

    def update(self, entity: T) -> T:
        entity.save()
        return entity

    def delete(self, id) -> bool:
        count, _ = self._model.objects.filter(pk=id).delete()
        return count > 0

    def exists(self, id) -> bool:
        return self._model.objects.filter(pk=id).exists()

    def filter(self, **kwargs) -> List[T]:
        return list(self._model.objects.filter(**kwargs))

    def get_by(self, **kwargs) -> Optional[T]:
        try:
            return self._model.objects.get(**kwargs)
        except self._model.DoesNotExist:
            return None

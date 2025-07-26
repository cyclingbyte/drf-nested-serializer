import pytest
from django.db import models
from django.db.utils import IntegrityError
from django.test import TestCase
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from drf_nested_model_serializer.serializer import NestedModelSerializer


class M2OChild(models.Model):
    name = models.CharField(max_length=20)
    parent = models.ForeignKey(
        "M2OParent",
        related_name="children",
        on_delete=models.CASCADE,
    )


class M2OParent(models.Model):
    name = models.CharField(max_length=20)


class M2OChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = M2OChild
        fields = "__all__"


class M2OParentSerializer(NestedModelSerializer):
    children = M2OChildSerializer(many=True)

    class Meta:
        model = M2OParent
        fields = "__all__"


class TestOneToOneNotNullNotBlank(TestCase):
    def test_create_parent_with_child(self):
        data = {
            "children": [{"name": "Child1"}, {"name": "Child2"}],
            "name": "Parent1",
        }
        serializer = M2OParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        parent = serializer.save()
        assert parent.children.count() == 2, (
            f"Expected 2 children, got {parent.children.count()}"
        )
        assert parent.children.first().name == "Child1", (
            f"Expected 'Child1', got '{parent.children.first().name}'"
        )
        assert parent.children.last().name == "Child2", (
            f"Expected 'Child2', got '{parent.children.last().name}'"
        )
        assert parent.name == "Parent1", f"Expected 'Parent1', got '{parent.name}'"

    def test_create_parent_without_children_fails(self):
        data = {"name": "Parent2"}
        serializer = M2OParentSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

import pytest
from django.db import models
from django.db.utils import IntegrityError
from django.test import TestCase
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from drf_nested_model_serializer.serializer import NestedModelSerializer


# Models
class Child(models.Model):
    name = models.CharField(max_length=20, blank=False, null=False)


class Parent(models.Model):
    child = models.OneToOneField(
        Child,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="parent",
    )
    name = models.CharField(max_length=20, blank=False, null=False)


# Serializers
class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child
        fields = "__all__"


class ParentSerializer(NestedModelSerializer):
    child = ChildSerializer()

    class Meta:
        model = Parent
        fields = "__all__"


# Tests
class TestOneToOneNotNullNotBlank(TestCase):
    def test_create_parent_with_child(self):
        data = {
            "child": {"name": "Child2"},
            "name": "Parent2",
        }
        serializer = ParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        parent = serializer.save()
        assert parent.child.name == "Child2", (
            f"Expected 'Child2', got '{parent.child.name}'"
        )
        assert parent.name == "Parent2", f"Expected 'Parent2', got '{parent.name}'"  # noqa: E501

    def test_create_parent_without_child_fails(self):
        data = {"name": "Parent3"}
        serializer = ParentSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_child_without_parent_fails(self):
        data = {"child": {"name": "Child3"}}
        serializer = ParentSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_parent_with_blank_child_name_fails(self):
        data = {
            "child": {"name": ""},
            "name": "Parent4",
        }
        serializer = ParentSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_parent_with_null_child_name_fails(self):
        data = {
            "child": {"name": None},
            "name": "Parent5",
        }
        serializer = ParentSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_parent_with_blank_name_fails(self):
        data = {
            "child": {"name": "Child6"},
            "name": "",
        }
        serializer = ParentSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_two_parents_with_same_child_fails(self):
        child = Child.objects.create(name="Child7")
        data1 = {
            "child": ChildSerializer(child).data,
            "name": "Parent6",
        }
        serializer1 = ParentSerializer(data=data1)
        assert serializer1.is_valid(), serializer1.errors
        parent1 = serializer1.save()
        assert parent1.child.name == "Child7", (
            f"Expected 'Child7', got '{parent1.child.name}'"
        )
        data2 = {
            "child": ChildSerializer(child).data,
            "name": "Parent7",
        }
        serializer2 = ParentSerializer(data=data2)
        assert serializer2.is_valid(), serializer2.errors
        with pytest.raises(IntegrityError):
            serializer2.save()

    def test_update_parent_with_child(self):
        child = Child.objects.create(name="Child10")
        parent = Parent.objects.create(child=child, name="Parent10")
        data = {
            "child": {"id": child.id, "name": "UpdatedChild"},
            "name": "UpdatedParent",
        }
        serializer = ParentSerializer(instance=parent, data=data)
        assert serializer.is_valid(), serializer.errors
        updated_parent = serializer.save()
        assert updated_parent.child.name == "UpdatedChild", (
            f"Expected 'UpdatedChild', got '{updated_parent.child.name}'"
        )
        assert updated_parent.name == "UpdatedParent", (
            f"Expected 'UpdatedParent', got '{updated_parent.name}'"
        )


# Reverse relationship tests
class ParentWithoutChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        exclude = ("child",)


class ChildWithParentSerializer(NestedModelSerializer):
    parent = ParentWithoutChildSerializer()

    class Meta:
        model = Child
        fields = "__all__"


class TestOneToOneNotNullNotBlankReverse(TestCase):
    def test_create_child_with_parent(self):
        data = {
            "name": "Child11",
            "parent": {"name": "Parent11"},
        }
        serializer = ChildWithParentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        child = serializer.save()
        assert child.name == "Child11", f"Expected 'Child11', got '{child.name}'"  # noqa: E501
        assert child.parent.name == "Parent11", (
            f"Expected 'Parent11', got '{child.parent.name}'"
        )

    def test_create_child_without_parent_fails(self):
        data = {"name": "Child12"}
        serializer = ChildWithParentSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_parent_without_child_fails(self):
        data = {"parent": {"name": "Parent12"}}
        serializer = ChildWithParentSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_child_with_blank_name_fails(self):
        data = {
            "name": "",
            "parent": {"name": "Parent13"},
        }
        serializer = ChildWithParentSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_child_with_null_name_fails(self):
        data = {
            "name": None,
            "parent": {"name": "Parent14"},
        }
        serializer = ChildWithParentSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_child_with_blank_parent_name_fails(self):
        data = {
            "name": "Child15",
            "parent": {"name": ""},
        }
        serializer = ChildWithParentSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_child_with_null_parent_name_fails(self):
        data = {
            "name": "Child16",
            "parent": {"name": None},
        }
        serializer = ChildWithParentSerializer(data=data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_two_children_with_same_parent_fails(self):
        data1 = {
            "name": "Child17",
            "parent": {"name": "ParentWithoutChild17"},
        }
        serializer1 = ChildWithParentSerializer(data=data1)
        assert serializer1.is_valid(), serializer1.errors
        child1 = serializer1.save()
        parent = child1.parent
        assert child1.name == "Child17", f"Expected 'Child17', got '{child1.name}'"  # noqa: E501
        data2 = {
            "name": "Child18",
            "parent": ParentWithoutChildSerializer(parent).data,
        }
        serializer2 = ChildWithParentSerializer(data=data2)
        assert serializer2.is_valid(), serializer2.errors
        child2 = serializer2.save()
        assert child2.name == "Child18", f"Expected 'Child18', got '{child2.name}'"  # noqa: E501
        assert child2.parent == parent, "Child2 should have the same parent as child1"  # noqa: E501
        child1.refresh_from_db()
        assert not hasattr(child1, "parent"), "Parent should not be set for child1"  # noqa: E501

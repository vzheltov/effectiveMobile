from rest_framework import serializers


class MockOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    owner_email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    mock = serializers.BooleanField()


class MockOrderInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one field is required.")
        return attrs


class MockOrderCreateResponseSerializer(serializers.Serializer):
    mock = serializers.BooleanField()
    detail = serializers.CharField()
    order = MockOrderInputSerializer()


class MockOrderActionResponseSerializer(serializers.Serializer):
    mock = serializers.BooleanField()
    detail = serializers.CharField()
    order_id = serializers.IntegerField()


class MockProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    owner_email = serializers.EmailField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    mock = serializers.BooleanField()

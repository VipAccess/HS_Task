import re

from rest_framework import serializers

from .models import Profile


class PhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        cleaned_phone = re.sub(r'\D', '', value)
        if len(cleaned_phone) == 11 and cleaned_phone.startswith('8') or len(
                cleaned_phone) == 12 and cleaned_phone.startswith('375'):
            return '+375' + cleaned_phone[-9:]

        raise serializers.ValidationError(
            "Некорректный номер телефона")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        phone = representation.get('phone', '')
        if phone:
            cleaned_phone = re.sub(r'\D', '', phone)
            if len(cleaned_phone) == 11 and cleaned_phone.startswith(
                    '8') or len(
                cleaned_phone) == 12 and cleaned_phone.startswith('375'):
                representation['phone'] = '+375' + cleaned_phone[-9:]
        return representation


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone', 'invite_code', 'activated_invite']
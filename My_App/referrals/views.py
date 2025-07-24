import random
from time import sleep
import string
import secrets

from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .serializers import PhoneSerializer
from .models import Profile


def generate_code(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))


class AuthAPIView(APIView):
    def post(self, request):
        serializer = PhoneSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            confirmation_code = str(random.randrange(1000, 10000))
            cache.set(f'confirmation_{phone}', confirmation_code, 120)
            sleep(2)

            # Добавил код в ответ для удобства тестирования
            return Response({
                "detail": "Код отправлен на ваш телефон",
                "code": confirmation_code},
                status=status.HTTP_200_OK)

        return Response({"detail": "Некорректный номер телефона"},
                        status=status.HTTP_400_BAD_REQUEST)


class VerifyAPIView(APIView):
    def post(self, request):
        serializer = PhoneSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
        else:
            return Response({"detail": "Некорректный номер телефона"},
                            status=status.HTTP_400_BAD_REQUEST)

        code = request.data.get('code')
        cached_code = cache.get(f'confirmation_{phone}')
        if cached_code != code:
            return Response({'detail': 'Неверный код'},
                            status=status.HTTP_401_UNAUTHORIZED)

        try:
            profile = Profile.objects.get(phone=phone)
            user = profile.user
            return Response({'detail': "Пользователь авторизован"},
                            status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            try:
                user = User.objects.create_user(
                    username=f'user_{phone}',
                    password=generate_code(15)
                )
                invite_code = generate_code(6)
                profile = Profile.objects.create(
                    user=user,
                    phone=phone,
                    invite_code=invite_code
                )

                return Response({
                    'detail': 'Пользователь создан и авторизован',
                    'user_id': user.id,
                    'phone': phone,
                    'invite_code': invite_code,
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                if 'user' in locals():
                    user.delete()
                return Response({'error': str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

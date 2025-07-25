import random
from time import sleep
import string
import secrets

from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

from .serializers import PhoneSerializer, ProfileSerializer
from .models import Profile, ReferralRelationship


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

            # Имитация задержки на сервере
            sleep(2)

            # Добавил код в ответ для удобства тестирования
            return Response({
                "detail": "Код отправлен на ваш телефон",
                "code": confirmation_code})

        return Response({"error": "Некорректный номер телефона"},
                        status=status.HTTP_400_BAD_REQUEST)


class VerifyAPIView(APIView):
    def post(self, request):
        serializer = PhoneSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
        else:
            return Response({"error": "Некорректный номер телефона"},
                            status=status.HTTP_400_BAD_REQUEST)

        code = request.data.get('code')
        cached_code = cache.get(f'confirmation_{phone}')
        if cached_code != code:
            return Response({'error': 'Неверный код'},
                            status=status.HTTP_401_UNAUTHORIZED)

        try:
            profile = Profile.objects.get(phone=phone)
            user = profile.user

            token, created = Token.objects.get_or_create(user=user)

            return Response({
                "detail": "Пользователь авторизован",
                "user_id": user.id,
                "phone": profile.phone,
                "invite_code": profile.invite_code,
                "token": token.key})
        except Profile.DoesNotExist:
            try:
                user = User.objects.create_user(
                    username=f'user_{phone}',
                    password=generate_code()
                )
                invite_code = generate_code(6)
                profile = Profile.objects.create(
                    user=user,
                    phone=phone,
                    invite_code=invite_code
                )

                token = Token.objects.create(user=user)

                return Response({
                    'detail': 'Пользователь авторизован',
                    'user_id': user.id,
                    'phone': phone,
                    'invite_code': invite_code,
                    'token': token.key
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                if 'user' in locals():
                    user.delete()
                return Response({'error': str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileAPIView(APIView):
    def get(self, request, phone):
        data = {'phone': phone}
        serializer_phone = PhoneSerializer(data=data)

        if serializer_phone.is_valid():
            phone = serializer_phone.validated_data['phone']
            try:
                queryset = Profile.objects.get(phone=phone)
            except Profile.DoesNotExist:
                return Response({'error': 'Номер не найден'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = ProfileSerializer(queryset)
            return Response(serializer.data)
        return Response({'error': "Некорректный номер телефона"}, status=status.HTTP_400_BAD_REQUEST)


class InviteAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        referral_code = request.data.get('referral_code')
        if not referral_code:
            return Response(
                {'error': 'Введите реферальный код'},
                status=status.HTTP_400_BAD_REQUEST
            )
        profile = Profile.objects.get(user=request.user)
        if profile.activated_invite:
            return Response({
                'error': 'Вы уже активировали реферальный код'
            }, status=status.HTTP_400_BAD_REQUEST)

        if profile.invite_code == referral_code:
            return Response(
                {'error': 'Нельзя использовать собственный реферальный код'},
                status=status.HTTP_400_BAD_REQUEST
            )

        inviter = Profile.objects.filter(invite_code=referral_code).first()
        if not inviter:
            return Response({
                'error': 'Неверный реферальный код'
            }, status=status.HTTP_400_BAD_REQUEST)

        ReferralRelationship.objects.create(
            inviter=inviter,
            referral=profile,
            referral_token=inviter.invite_code
        )
        profile.activated_invite = referral_code
        profile.save()

        return Response({'detail': 'Реферальный код успешно активирован'})



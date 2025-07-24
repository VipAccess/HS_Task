import random
from time import sleep

from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .serializers import PhoneSerializer


class AuthAPIView(APIView):
    def post(self, request):
        serializer = PhoneSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            confirmation_code = str(random.randrange(1000, 10000))
            cache.set(f'confirmation_{phone}', confirmation_code, 120)
            sleep(2)
            return Response({"detail": "Код отправлен на ваш телефон"}, status=status.HTTP_200_OK)

        return Response({"detail": "Некорректный номер телефона"}, status=status.HTTP_400_BAD_REQUEST)
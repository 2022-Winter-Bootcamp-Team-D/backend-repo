from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from store.models import Store
from waiting.models import Waiting
from user.models import User
from django.core import serializers
from .serializer import StoreJoinSerializer
from .notification import notify
from .serializer import StoreBreaktimeSerializer
from .serializer import StoreDetailSerializer
from .serializer import StoreWaitingsSerializer
import json


@api_view(['POST'])
def signin(request):
    store_name = request.data['store_name']
    phone_num = request.data['phone_num']
    latitude = request.data['latitude']
    longitude = request.data['longitude']
    password = request.data['password']

    try:
        object = Store.objects.create(store_name=store_name, phone_num=phone_num, latitude=latitude, longitude=longitude,
                                      password=password)
        response = StoreJoinSerializer(object)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    return Response(data=response.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def enter_notify(request):
    # result = notify.enter_notify(request)
    notify.enter_notify(token=request.data['token'])

    return Response('호출에 성공했습니다!', status=status.HTTP_200_OK)


@api_view(['PATCH'])
def breaktime(request):
    store_id = request.data['store_id']

    try:
        object = Store.objects.get(store_id=store_id)
        object.is_waiting = not object.is_waiting
        object = object.save()

    except:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_200_OK)


@api_view(['PATCH'])
def detail(request):
    store_id = request.data['store_id']
    information = request.data['information']

    try:
        object = Store.objects.get(store_id=store_id)
        object.information = information
        object = object.save()

    except:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_200_OK)


class waitings(APIView):
    def get(self, request):
        store_id = request.data['store_id']
        WA = 'WA'
        # try:
        store = Store.objects.get(store_id=store_id)
        waitings = Waiting.objects.raw(
            """SELECT waiting_id, name, people, phone_num FROM Waiting WHERE store_id=%s AND status=%s""" % (store_id, "'WA'"))
        waiting = serializers.serialize(
            "json", waitings, fields=("phone_num", "people", "name"))
        print(waitings[0])
        # print(waitings)
        # if waitings == null:
        # waitings.information = store.information
        # waitings.is_waiting = store.is_waiting
        # response = StoreWaitingsSerializer(waitings)
        # except:
        #     return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(waiting, status=status.HTTP_200_OK)

    def patch(self, request):
        store_id = request.data['store_id']
        waiting_id = request.data['waiting_id']

        try:
            waiting = Waiting.objects.get(waiting_id=waiting_id)
            waiting.status = 'EN'
            waiting.save()

            # response = StoreWaitingsSerializer(object)
            # enter_notify(request)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_200_OK)


@api_view(['PATCH'])
def cancellations(request):
    waiting_id = request.data['waiting_id']
    store_id = request.data['store_id']

    Waiting.objects.filter(waiting_id=waiting_id,
                           store_id=store_id).update(status='CN')
    return Response("웨이팅이 성공적으로 취소 됐습니다.", status=200)

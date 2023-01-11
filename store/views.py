from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from store.models import Store
from user.models import User
from waiting.models import Waiting
from .serializer import StoreJoinSerializer
from .notification import notify
from .serializer import StoreBreaktimeSerializer
from .serializer import StoreDetailSerializer
from .serializer import StoreWaitingsSerializer


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


@api_view(['GET'])
def waitings(request):
    store_id = request.data['store_id']

    try:
        object = Store.objects.get(store_id=store_id)
        object = Waiting.objects.filter(store_id=object, status='WA')

        response = StoreWaitingsSerializer(object)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_200_OK)


@api_view(['PATCH'])
def cancellations(request):
    waiting_id = request.data['waiting_id']
    store_id = request.data['store_id']
    token = User.objects.get(waiting_id=waiting_id).token

    Waiting.objects.filter(waiting_id=waiting_id, store_id=store_id).update(status='CN')
    notify.cancel_notify(token)
    return Response("웨이팅이 성공적으로 취소 됐습니다.", status=200)

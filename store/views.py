from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from store.models import Store
from waiting.models import Waiting
from user.models import User
from .serializer import StoreJoinSerializer
from .notification import notify


@api_view(['POST'])
def signin(request):
    store_name = request.data['store_name']
    phone_num = request.data['phone_num']
    latitude = request.data['latitude']
    longitude = request.data['longitude']
    password = request.data['password']

    try:
        object = Store.objects.create(store_name=store_name, phone_num=phone_num, latitude=latitude,
                                      longitude=longitude,
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


# 가게의 웨이팅 목록, 상세정보, 웨이팅 받는지 여부를 반환
def search_waitings(store_id):
    store = Store.objects.get(store_id=store_id)
    data = {}
    data["data"] = []
    data["information"] = store.information
    data["is_waiting"] = store.is_waiting

    # 가게 웨이팅이 없을경우 상세정보랑 웨이팅 상태만 반환
    try:
        waitings = Waiting.objects.raw(
            """SELECT waiting_id
            FROM Waiting 
            WHERE store_id=%s AND status=%s""" % (store_id, "'WA'"))
    except:
        return Response(data, status=status.HTTP_200_OK, content_type="text/json-comment-filtered")

    for i in waitings:
        temp = {
            "waiting_id": i.pk,
            "name": i.name,
            "phone_num": i.phone_num,
            "people": i.people
        }
        data["data"].append(temp)
    return data


class waitings(APIView):
    def get(self, request):
        store_id = request.data['store_id']
        data = search_waitings(store_id)
        return Response(data, status=status.HTTP_200_OK, content_type="text/json-comment-filtered")

    def patch(self, request):
        waiting_id = request.data['waiting_id']

        try:
            waiting = Waiting.objects.get(waiting_id=waiting_id)
            waiting.status = 'EN'
            waiting.save()
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_200_OK)


def search_waiting_order(waiting_id, store_id):
    waiting_teams = Waiting.objects.filter(waiting_id__lt=waiting_id, store_id=store_id, status="WA")
    waiting_order = len(waiting_teams) + 1
    return waiting_order


@api_view(['PATCH'])
def cancellations(request):
    waiting_id = request.data['waiting_id']
    store_id = request.data['store_id']
    waiting_order = search_waiting_order(waiting_id, store_id)
    try:
        cancel_token = User.objects.get(waiting_id=waiting_id).token

        # status를 CN(CANCEL)로 바꿔주고 취소 알림 보내기
        Waiting.objects.filter(waiting_id=waiting_id, store_id=store_id).update(status='CN')
        notify.cancel_notify(cancel_token)

        # 다음 웨이팅 팀이 존재하는지 확인 없으면 바로 리턴
        data = search_waitings(store_id)
        auto_token = User.objects.get(waiting_id=data["data"][0]['waiting_id']).token

        # 취소한 웨이팅이 1순위였고 다음 웨이팅 팀이 존재할 경우 다음 팀에게 1순위 알림 보내기
        if waiting_order == 1:
            notify.auto_notify(auto_token)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(data, status=status.HTTP_200_OK, content_type="text/json-comment-filtered")

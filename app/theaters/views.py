from datetime import datetime

from django.db.models import Count, Q
from rest_framework.generics import ListAPIView

from utils import convert_list_to_dict
from .models import Schedule, Theater
from .serializers import (
    ScheduleMovieSerializer, ScheduleTheaterListSerializer, ScheduleRegionCountSerializer
)


# 해당 상영관의 상영시간 정보
class ScheduleList(ListAPIView):
    serializer_class = ScheduleMovieSerializer

    def get_queryset(self):
        date_int = self.kwargs.get('date', None)
        date = datetime.strptime(str(date_int), '%y%m%d')

        theater_id = self.kwargs.get('theater_id', None)

        movie = self.request.query_params.get('movie', None)

        if movie is not None:
            movies = list(map(int, movie.split()))

            movies_dict = convert_list_to_dict(movies)
            queryset = Schedule.objects.filter(
                Q(movie=movies_dict[0]) | Q(movie=movies_dict[1]) | Q(movie=movies_dict[2])
            ).filter(
                start_time__date=date,
                screen__theater_id=theater_id,
            )
        else:
            queryset = Schedule.objects.filter(
                start_time__date=date,
                screen__theater_id=theater_id,
            )

        return queryset


# 상영 중인 상영관 정보
class ScheduleTheaterList(ListAPIView):
    serializer_class = ScheduleTheaterListSerializer

    def get_queryset(self):
        date_int = self.kwargs['date']

        date = datetime.strptime(str(date_int), '%y%m%d')

        movie = self.request.query_params.get('movie', None)

        if movie is not None:
            movies = list(map(int, movie.split()))

            movies_dict = convert_list_to_dict(movies)
            queryset = Theater.objects.filter(
                Q(screens__schedules__movie=movies_dict[0]) |
                Q(screens__schedules__movie=movies_dict[1]) |
                Q(screens__schedules__movie=movies_dict[2])
            ).filter(
                screens__schedules__start_time__date=date
            ).distinct('id')
        else:
            queryset = Theater.objects.filter(screens__schedules__start_time__date=date).distinct('id')

        return queryset


# 상영 중인 상영관 지역 기준 합산
class ScheduleRegionCount(ListAPIView):
    serializer_class = ScheduleRegionCountSerializer

    def get_queryset(self):
        date_int = self.kwargs['date']

        date = datetime.strptime(str(date_int), '%y%m%d')
        movie = self.request.query_params.get('movie', None)

        if movie is not None:
            movies = list(map(int, movie.split()))

            movies_dict = convert_list_to_dict(movies)
            queryset = Theater.objects.filter(
                Q(screens__schedules__movie=movies_dict[0]) |
                Q(screens__schedules__movie=movies_dict[1]) |
                Q(screens__schedules__movie=movies_dict[2])
            ).filter(
                screens__schedules__start_time__date=date
            ).values(
                'region', 'region__name'
            ).annotate(Count('name', distinct=True))

        else:
            queryset = Theater.objects.filter(
                screens__schedules__start_time__date=date
            ).values(
                'region', 'region__name'
            ).annotate(
                Count('name', distinct=True)
            )

        return queryset


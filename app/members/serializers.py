import datetime

from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.utils import email_address_exists
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q
from phonenumber_field.serializerfields import PhoneNumberField
from rest_auth.registration.serializers import RegisterSerializer
from rest_auth.serializers import LoginSerializer as DefaultLoginSerializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer as DefaultTokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from movies.models import Movie, Rating, MovieLike
from movies.serializers import MovieTimelineSerializer
from reservations.models import Reservation
from utils.custom_functions import reformat_duration, check_google_oauth_api
from .exceptions import (
    TakenEmailException, UsernameDuplicateException, GoogleUniqueIdDuplicatesException,
    SocialSignUpUsernameFieldException, LoginFailException, UnidentifiedUniqueIdException,
    PasswordNotMatchingException
)
from .models import Profile

Member = get_user_model()


class SignUpSerializer(RegisterSerializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    mobile = PhoneNumberField()
    birth_date = serializers.DateField()

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise TakenEmailException
        return email

    def validate_username(self, username):
        try:
            Member.objects.get(username=username)
            raise UsernameDuplicateException
        except ObjectDoesNotExist:
            return username

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise PasswordNotMatchingException
        data['password'] = data.pop('password1')
        data.pop('password2')
        return data

    # django-rest-auth 사용을 위해 user 인스턴스를 반환하는 save() 메소드 재정의
    # https://django-rest-auth.readthedocs.io/en/latest/configuration.html
    def save(self, request):
        self.is_valid()
        validated_data = self.validated_data
        password = validated_data.pop('password')
        member = Member.objects.create(**validated_data)
        member.set_password(password)
        member.save()
        return member


class SocialSignUpSerializer(SignUpSerializer):
    password1, password2 = None, None
    unique_id = serializers.CharField(required=True, write_only=True)

    def validate_unique_id(self, unique_id):
        try:
            Member.objects.get(unique_id=unique_id)
            raise GoogleUniqueIdDuplicatesException
        except ObjectDoesNotExist:
            return unique_id

    def validate(self, data):
        if data['username'] != data['email']:
            raise SocialSignUpUsernameFieldException
        return data

    # django-rest-auth 사용을 위해 user 인스턴스를 반환하는 save() 메소드 재정의
    # https://django-rest-auth.readthedocs.io/en/latest/configuration.html
    def save(self, request):
        self.is_valid()
        validated_data = self.validated_data
        member = Member.objects.create(**validated_data)
        member.set_password(validated_data['unique_id'])
        member.save()
        return member


class JWTSerializer(serializers.Serializer):
    refresh = serializers.SerializerMethodField()
    access = serializers.SerializerMethodField()
    id = serializers.IntegerField(source='user.id')
    username = serializers.CharField(source='user.username')
    name = serializers.CharField(source='user.name')
    email = serializers.EmailField(source='user.email')
    birth_date = serializers.DateField(source='user.birth_date')
    mobile = PhoneNumberField(source='user.mobile')

    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def get_refresh(self, obj):
        return str(self.get_token(obj['user']))

    def get_access(self, obj):
        return str(self.get_token(obj['user']).access_token)


# for Documentation
class CheckUsernameDuplicateSerializer(serializers.Serializer):
    username = serializers.CharField()


class LoginSerializer(DefaultLoginSerializer):
    email = None
    username = serializers.CharField(required=True)


class SocialLoginSerializer(LoginSerializer):
    google_id_token = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        username = data['username']
        password = data['password']
        google_id_token = data['google_id_token']
        user = self.authenticate(username=username, password=password)
        if user is None:
            raise LoginFailException
        unique_id = check_google_oauth_api(google_id_token)
        if user.unique_id != unique_id:
            raise UnidentifiedUniqueIdException
        data['user'] = user
        return data


class TokenRefreshResultSerializer(serializers.Serializer):
    access = serializers.CharField()


class TokenRefreshSerializer(DefaultTokenRefreshSerializer):
    def to_representation(self, instance):
        return TokenRefreshResultSerializer(instance).data


class ProfileDetailSerializer(serializers.ModelSerializer):
    regions = serializers.StringRelatedField(many=True)
    genres = serializers.StringRelatedField(many=True)

    class Meta:
        model = Profile
        fields = [
            'id',
            'tier',
            'point',
            'regions',
            'genres',
            'time',
            'is_disabled',
        ]


class MemberDetailSerializer(serializers.ModelSerializer):
    profile = ProfileDetailSerializer()
    reserved_movies_count = serializers.SerializerMethodField('get_reserved_movies_count')
    watched_movies_count = serializers.SerializerMethodField('get_watched_movies_count')
    like_movies_count = serializers.SerializerMethodField('get_like_movies_count')
    rating_movies_count = serializers.SerializerMethodField('get_rating_movies_count')

    class Meta:
        model = Member
        fields = [
            'id',
            'email',
            'name',
            'mobile',
            'birth_date',
            'profile',
            'reserved_movies_count',
            'watched_movies_count',
            'like_movies_count',
            'rating_movies_count',
        ]

    def get_reserved_movies_count(self, member):
        return Movie.objects.filter(
            schedules__reservations__member=member,
            schedules__reservations__payment__isnull=False,
            schedules__reservations__payment__is_canceled=False,
            schedules__start_time__gt=datetime.datetime.today(),
        ).count()

    def get_watched_movies_count(self, member):
        return Movie.objects.filter(
            schedules__reservations__member=member,
            schedules__reservations__payment__isnull=False,
            schedules__reservations__payment__is_canceled=False,
            schedules__start_time__lte=datetime.datetime.today(),
        ).count()

    def get_like_movies_count(self, member):
        return Movie.objects.filter(
            like_members__pk=member.pk,
            movie_likes__liked=True
        ).count()

    def get_rating_movies_count(self, member):
        return Rating.objects.filter(
            member=member
        ).count()


class LikeMoviesSerializer(serializers.ModelSerializer):
    movie_id = serializers.IntegerField(source='movie.id')
    movie_name = serializers.CharField(source='movie.name_kor')
    poster = serializers.ImageField(source='movie.poster')
    grade = serializers.CharField(source='movie.grade')
    acc_favorite = serializers.SerializerMethodField('get_acc_favorite')
    open_date = serializers.DateField(source='movie.open_date', format='%Y-%m-%d')
    running_time = serializers.SerializerMethodField('get_running_time')
    directors = serializers.SerializerMethodField('get_directors')
    genres = serializers.SerializerMethodField('get_genres')
    liked_at = serializers.DateField(format='%Y-%m-%d')

    class Meta:
        model = MovieLike
        fields = [
            'movie_id',
            'movie_name',
            'poster',
            'grade',
            'acc_favorite',
            'open_date',
            'running_time',
            'directors',
            'genres',
            'liked_at',
        ]

    def get_acc_favorite(self, movielike):
        likes_count = movielike.movie.movie_likes.filter(liked=True).count()
        result = likes_count + 689 - (movielike.movie.pk * 24)
        return result if result >= 0 else likes_count + 11

    def get_running_time(self, movielike):
        return reformat_duration(movielike.movie.running_time)

    def get_directors(self, movielike):
        return movielike.movie.directors.values_list('name', flat=True)

    def get_genres(self, movielike):
        return movielike.movie.genres.values_list('name', flat=True)


class WatchedMoviesSerializer(serializers.ModelSerializer):
    payment_id = serializers.IntegerField(source='payment.id')
    reservation_code = serializers.CharField(source='payment.code')
    price = serializers.IntegerField(source='payment.price')
    discount_price = serializers.IntegerField(source='payment.discount_price')
    screen_type = serializers.CharField(source='schedule.screen.screen_type')
    screen_name = serializers.CharField(source='schedule.screen.name')
    seat_grade = serializers.SerializerMethodField('get_seat_grade')
    seat_name = serializers.SerializerMethodField('get_seat_name')
    theater_name = serializers.CharField(source='schedule.screen.theater.name')
    theater_region = serializers.CharField(source='schedule.screen.theater.region.name')
    start_time = serializers.DateTimeField(source='schedule.start_time', format='%Y-%m-%d %H:%M')
    payed_at = serializers.DateTimeField(source='payment.payed_at', format='%Y-%m-%d')
    movie = MovieTimelineSerializer(source='schedule.movie')

    class Meta:
        model = Reservation
        fields = [
            'payment_id',
            'reservation_code',
            'price',
            'discount_price',
            'screen_type',
            'screen_name',
            'seat_grade',
            'seat_name',
            'theater_name',
            'theater_region',
            'start_time',
            'payed_at',
            'movie',
        ]

    def get_seat_grade(self, reservation):
        return reservation.seat_grades.annotate(
            adult=Count('grade', filter=Q(grade='adult')),
            teen=Count('grade', filter=Q(grade='teen')),
            preferential=Count('grade', filter=Q(grade='preferential'))
        ).values('adult', 'teen', 'preferential')

    def get_seat_name(self, reservation):
        return reservation.seats.values_list('name', flat=True)

    def get_acc_favorite(self, reservation):
        likes_count = reservation.schedule.movie.movie_likes.filter(liked=True).count()
        result = likes_count + 689 - (reservation.schedule.movie.pk * 24)
        return result if result >= 0 else likes_count + 11

    def get_running_time(self, obj):
        return reformat_duration(obj.schedule.movie.running_time)


class RatingMoviesSerializer(serializers.ModelSerializer):
    rating_id = serializers.IntegerField(source='id')
    movie_name = serializers.CharField(source='movie.name_kor')
    poster = serializers.ImageField(source='movie.poster')

    class Meta:
        model = Rating
        fields = [
            'rating_id',
            'movie_name',
            'poster',
            'created_at',
            'score',
            'key_point',
            'comment',
        ]


class ReservedMoviesSerializer(serializers.ModelSerializer):
    reservation_id = serializers.IntegerField(source='id')
    reservation_code = serializers.CharField(source='payment.code')
    price = serializers.IntegerField(source='payment.price')
    discount_price = serializers.IntegerField(source='payment.discount_price')
    movie_name = serializers.CharField(source='schedule.movie.name_kor')
    poster = serializers.ImageField(source='schedule.movie.poster')
    screen_type = serializers.CharField(source='schedule.screen.screen_type')
    screen_name = serializers.CharField(source='schedule.screen.name')
    theater_name = serializers.CharField(source='schedule.screen.theater.name')
    start_time = serializers.DateTimeField(source='schedule.start_time', format='%Y-%m-%d %H:%M')
    payed_at = serializers.DateTimeField(source='payment.payed_at', format='%Y-%m-%d %H:%M')
    payment_id = serializers.IntegerField(source='payment.pk')
    receipt_id = serializers.CharField(source='payment.receipt_id')
    seat_grade = serializers.SerializerMethodField('get_seat_grade')
    seat_name = serializers.SerializerMethodField('get_seat_name')
    saving_point = serializers.SerializerMethodField('get_saving_point')

    class Meta:
        model = Reservation
        fields = [
            'reservation_id',
            'reservation_code',
            'price',
            'discount_price',
            'movie_name',
            'poster',
            'screen_type',
            'screen_name',
            'theater_name',
            'start_time',
            'seat_grade',
            'seat_name',
            'payed_at',
            'payment_id',
            'receipt_id',
            'saving_point',
        ]

    def get_seat_grade(self, reservation):
        return reservation.seat_grades.annotate(
            adult=Count('grade', filter=Q(grade='adult')),
            teen=Count('grade', filter=Q(grade='teen')),
            preferential=Count('grade', filter=Q(grade='preferential'))
        ).values('adult', 'teen', 'preferential')

    def get_seat_name(self, reservation):
        return reservation.seats.values_list('name', flat=True)

    def get_saving_point(self, reservation):
        if reservation.member.profile.tier == 'basic':
            discount_rate = 0.01
        else:
            discount_rate = 0.02

        if not reservation.payment.discount_price:
            discount_price = 0
        else:
            discount_price = reservation.payment.discount_price

        return round((reservation.payment.price - discount_price) * discount_rate)


class CanceledReservationMoviesSerializer(serializers.ModelSerializer):
    reservation_id = serializers.IntegerField(source='id')
    canceled_at = serializers.DateTimeField(source='payment.canceled_at', format='%Y-%m-%d %H:%M')
    movie_name = serializers.CharField(source='schedule.movie.name_kor')
    theater_name = serializers.CharField(source='schedule.screen.theater.name')
    start_time = serializers.DateTimeField(source='schedule.start_time', format='%Y-%m-%d %H:%M')
    canceled_payment = serializers.IntegerField(source='payment.price')
    canceled_discount_price = serializers.IntegerField(source='payment.discount_price')

    class Meta:
        model = Reservation
        fields = [
            'reservation_id',
            'canceled_at',
            'movie_name',
            'theater_name',
            'start_time',
            'canceled_payment',
            'canceled_discount_price',
        ]

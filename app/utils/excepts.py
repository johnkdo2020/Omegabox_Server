from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError as DRFValidationError
from rest_framework.views import exception_handler

from config import settings


def rest_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        if not settings.DEBUG:
            raise exc
        if hasattr(exc, 'message_dict'):
            exc = DRFValidationError(detail={'error': exc.message_dict})
        elif hasattr(exc, 'message'):
            exc = DRFValidationError(detail={'error': exc.message})
        elif hasattr(exc, 'messages'):
            exc = DRFValidationError(detail={'error': exc.messages})

    response = exception_handler(exc, context)

    if response:
        response.data['status'] = response.status_code
        response.data['code'] = getattr(exc, 'code', getattr(exc, 'default_code', None)) or response.data['detail'].code
    return response


class TakenNumberException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '이미 가입된 번호입니다.'
    default_code = 'TakenNumber'


class InvalidScheduleIdException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '유효하지 않은 스케쥴입니다.'
    default_code = 'InvalidScheduleID'


class TakenSeatException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '이미 예약된 좌석입니다.'
    default_code = 'TakenSeat'


class InvalidGradeChoicesException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '유효하지 않은 선택 사항입니다. ' \
                     + '선택 가능 옵션: adult, teen, preferential'
    default_code = 'InvalidGradeChoices'


class InvalidSeatException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '예약 불가능한 좌석입니다. - 띄어앉기석'
    default_code = 'InvalidSeat(sit_apart)'


class InvalidSeatIdException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '유효하지 않은 좌석 id입니다.'
    default_code = 'InvalidSeatId'


class SeatNamesMissingException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '좌석의 이름을 반드시 query parameter로 전달해야합니다.'
    default_code = 'SeatNamesMissing'


class FailToGetBootPayAccessTokenException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '부트페이 access token 획득 실패'
    default_code = 'FailToGetBootPayAccessToken'


class VerifyRequestFailException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '부트페이 영수증 검증 요청 실패'
    default_code = 'VerifyRequestFail'


class UnverifiedReceiptException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '부트페이 영수증 검증 실패 - 결제완료가 아니거나 가격이 틀림'
    default_code = 'UnverifiedReceipt'


class PaymentCancelFailException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '결제 취소가 실패했습니다.'
    default_code = 'PaymentCancelFail'


class PaymentIdReceiptIdNotMatchingException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'payment_id와 receipt_id가 매칭되지 않습니다.'
    default_code = 'PaymentIDReceiptIDNotMatching'


class ReservationOwnershipException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '예약자와 결제자가 다릅니다.'
    default_code = 'ReservationOwnership'


class PriceNotMatchingException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '요청한 취소 금액이 결제했던 금액과 다릅니다.'
    default_code = 'PriceNotMatching'


class IncorrectPriceExceptionException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '결제 요청 금액(price + discount_price)이 결제해야하는 금액과 다릅니다.'
    default_code = 'IncorrectPrice'


class InvalidGoogleAccessTokenException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Google Access Token이 유효하지 않습니다.'
    default_code = 'InvalidGoogleAccessToken'


class InvalidReservationIdException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '유효하지 않은 reservation id입니다. - 삭제 불가능'
    default_code = 'InvalidReservationId'

from datetime import datetime
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from django.http.response import JsonResponse

from django.contrib.auth.models import User
from dbconnect import get_db_handle, get_collection_handle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

dbName = get_db_handle("apex-azure")
userCollection = get_collection_handle(dbName, "user")
creditCardCollection = get_collection_handle(dbName, "credit-cards")
creditCardTransCollection = get_collection_handle(dbName, "credit-card-transactions")
payeeCollection = get_collection_handle(dbName, "payee-details")

@api_view(['POST'])
# @permission_classes([IsAdminUser])
@permission_classes([AllowAny])
def signup(request):
    data = json.loads(request.body)
    username = data['username']
    password = data['password']

    try:
        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already exist."}, status=400, safe=False)
        else:
            User.objects.create_user(username=username, password=password)
            return JsonResponse({"success": "User has been created"}, status=200, safe=False)
    except Exception as e:
        print(repr(e))
        return JsonResponse({"error": "Something went wrong when registering user. Please try again."}, status=400, safe=False)

@api_view(['POST'])
# @permission_classes([IsAdminUser])
@permission_classes([AllowAny])
def login(request):
    user = request.user
    data = request.data
    username = data['username']
    password = data['password']

    try:
        user = authenticate(request, username=username, password=password)
        if user is not None:
            refreshToken = RefreshToken.for_user(user)
            return JsonResponse({"access": str(refreshToken.access_token), "refresh": str(refreshToken)}, status=200, safe=False)
        else: 
            return JsonResponse({"error": "Invalid username or password, please try again."}, status=401, safe=False)
    except:
        return JsonResponse({"error": "Something went wrong logging in."}, status=400, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_credit_cards(request):
    data = request.data
    userId = data['userId']
    creditCard = list(creditCardCollection.find({"userId": str(userId)}, {"_id": 0, "accountId": 0, "userId": 0}))
    details = {
        "Credit-Cards": creditCard,
    }
    return JsonResponse({"success": "Successfully retrieved credit card details.", "details": details}, status=200, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_credit_card_summary(request):
    data = request.data
    userId = data['userId']
    creditCardList = []

    creditCards= list(creditCardCollection.find({"userId": str(userId)}, {"accountId": 0, "userId": 0}))
    for creditCard in creditCards:
        cardId = creditCard['_id']
        creditCard.pop('_id')
        cardTransactions = list(creditCardTransCollection.find({"cardId": str(cardId)}, {"_id": 0, "cardId": 0}).sort("timestamp", -1))
        creditCard = {
            "credit-card-details": creditCard,
            "card-transactions": cardTransactions
        }
        creditCardList.append(creditCard)
    details = {
        "Credit-Cards": creditCardList
    }
    print(details)
    return JsonResponse({"success": "Successfully retrieved credit card details.", "details": details}, status=200, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payees(request):
    data = request.data
    userAccountId = data['userAccountId']
    payees = list(payeeCollection.find({"accountId": str(userAccountId)}, {"_id": 0, "accountId": 0}))
    details = {
        "Payee-Details": payees
    }
    return JsonResponse({"success": "Successfully retrieved saved payee details.", "details": details}, status=200, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_payee(request):
    data = request.data
    payee = payeeCollection.find_one({"bankAccountNumber": data['accountNumber']}, {"_id": 0})
    if payee == None:
        payeeDetails = {
            "name": data['name'], 
            "bankName": data['bankName'], 
            "bankAccountNumber": data['accountNumber'], 
            "type": data['type'], 
            "accountId": data['accountId']}
        payeeCollection.insert_one(payeeDetails)
        return JsonResponse({"success": "Successfully added payee details."}, status=200, safe=False)
    else:
        return JsonResponse({"error": "Payee already added."}, status=200, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_payee(request):
    user = request.user
    data = request.data
    user = User.objects.get(id=user.id)
    if user is not None:
        accountNumber = data['bankAccountNumber']
        payeeCollection.delete_one({"bankAccountNumber": accountNumber})
        # print(details)
        return JsonResponse({"success": "Successfully deleted payee details."}, status=200, safe=False)
    else:
        return JsonResponse({"error": "No such user found."}, status=404, safe=False)


from django.urls import path
from .views import (
    ChatRoomListView,
    ChatRoomDetailView,
    MarkAllMessagesAsReadView,
    SendMessageView,
    TypingStatusView,
    RoomManagementView,
    UnreadNotificationsView,
    SearchChatRoomView,
    DetailedUserChatRoomView
)

urlpatterns = [
    path('rooms/', ChatRoomListView.as_view(), name='chat-room-list'),
    path('rooms/<str:room_name>/', ChatRoomDetailView.as_view(), name='chat-room-detail'),
    path('rooms/<str:room_name>/send-message/', SendMessageView.as_view(), name='send-message'),
    path('rooms/<str:room_name>/typing-status/', TypingStatusView.as_view(), name='typing-status'),
    path('rooms/mark-all-read/', MarkAllMessagesAsReadView.as_view(), name='mark-all-read'),
    path('rooms/manage/<str:room_name>/', RoomManagementView.as_view(), name='manage-room'),
    path('rooms/manage/', RoomManagementView.as_view(), name='create-room'),
    path('notifications/unread/', UnreadNotificationsView.as_view(), name='unread-notifications'),
    path('rooms/search/', SearchChatRoomView.as_view(), name='search-chat-room'),
    path('rooms/<str:room_name>/details/', DetailedUserChatRoomView.as_view(), name='detailed-user-chat-room'),
]

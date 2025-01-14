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
    DetailedUserChatRoomView,
    AuthorizedUserListView,
    SearchUserView,
    ChatSidebarView,
    ChatWithUserDetailView
)

urlpatterns = [
    path('rooms/sidebar-info/', view=ChatSidebarView.as_view(), name='chat-sidebar-info'),
    path('rooms/search-list/', view=SearchUserView.as_view(), name='seach-user-list'),
    path('rooms/users-list/', view=AuthorizedUserListView.as_view(), name='user-list'),
    path('rooms/mark-all-read/', view=MarkAllMessagesAsReadView.as_view(), name='mark-all-read'),
    path('rooms/manage/', view=RoomManagementView.as_view(), name='create-room'),
    path('notifications/unread/', view=UnreadNotificationsView.as_view(), name='unread-notifications'),
    path('rooms/lists/', view=ChatRoomListView.as_view(), name='chat-room-list'),
    path('rooms/search/', view=SearchChatRoomView.as_view(), name='search-chat-room'),
    path('rooms/detail-rooms-info/', view=ChatRoomDetailView.as_view(), name='chat-room-detail'),
    path('rooms/user-chat-info/', view=ChatWithUserDetailView.as_view(), name='user-chat-info'),
    path('rooms/<str:room_name>/send-message/', view=SendMessageView.as_view(), name='send-message'),
    path('rooms/<str:room_name>/typing-status/', view=TypingStatusView.as_view(), name='typing-status'),
    # path('rooms/manage/<str:room_name>/', view=RoomManagementView.as_view(), name='manage-room'),
    path('rooms/<str:room_name>/details/', view=DetailedUserChatRoomView.as_view(), name='detailed-user-chat-room'),
]

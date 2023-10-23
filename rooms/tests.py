from datetime import datetime

from django.test import TestCase

from .models import GroupChat
from users.models import CustomUser
from .forms import GroupChatCreateForm

# Create your tests here.
class GroupChatModelTests(TestCase):
    def setUp(self):
        self.owner = CustomUser.objects.create(username="owner_username", birthday=datetime.now())
        self.group_chat = GroupChatCreateForm({'name': 'Test Group Chat'}).save(commit=False)
        self.group_chat.owner = self.owner
        self.group_chat.save()

    def test_create_group_chat(self):
        self.assertEqual(self.group_chat.name, "Test Group Chat")
        self.assertEqual(self.group_chat.owner, self.owner)
        self.assertFalse(self.group_chat.public)

    def test_base_role(self):        
        self.assertTrue(self.group_chat.base_role is not None)
        self.assertEqual(self.group_chat.base_role.name, "all")
        self.assertEqual(self.group_chat.base_role.chat, self.group_chat)

        owner_membership = self.group_chat.get_member(user=self.owner)
        self.assertEqual(owner_membership.user, self.owner)
        self.assertEqual(owner_membership.chat, self.group_chat)
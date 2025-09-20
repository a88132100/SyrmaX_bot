from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = '創建測試用戶'

    def handle(self, *args, **options):
        username = 'test'
        password = 'test123'
        email = 'test@example.com'
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'用戶 {username} 已存在')
            )
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            self.stdout.write(
                self.style.SUCCESS(f'成功創建測試用戶: {username}')
            )
            self.stdout.write(f'用戶名: {username}')
            self.stdout.write(f'密碼: {password}')
            self.stdout.write(f'Email: {email}')

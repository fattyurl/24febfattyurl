from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Promote an existing user to superuser with admin access by email."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email of the user to promote.")

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"No user found with email: {email}")

        user.is_superuser = True
        user.is_staff = True
        user.save(update_fields=["is_superuser", "is_staff"])

        self.stdout.write(
            self.style.SUCCESS(
                f"User '{user.username or user.email}' is now a superuser with admin access."
            )
        )

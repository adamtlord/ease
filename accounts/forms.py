from registration.forms import RegistrationForm

from accounts.models import CustomUser


class CustomUserRegistrationForm(RegistrationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from accounts.models import CustomUser, Customer, LovedOne, UserProfile, Rider
from rides.models import Destination


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = CustomUser
        fields = '__all__'

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserProfileInlineForm(forms.ModelForm):
    source = forms.CharField(required=False)

    class Meta:
        model = UserProfile
        fields = '__all__'

    def clean_source(self):
        data = self.cleaned_data['source']
        return data


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    form = UserProfileInlineForm
    verbose_name_plural = 'user profile'


class UserAdmin(BaseUserAdmin):
    # https://docs.djangoproject.com/en/1.10/topics/auth/customizing/#django.contrib.auth.models.AbstractBaseUser
    # https://github.com/django/django/blob/master/django/contrib/auth/admin.py
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')
        }),
    )

    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email',)
    inlines = (UserProfileInline, )


class DestinationInline(admin.StackedInline):
    model = Destination


class LovedOneInline(admin.StackedInline):
    model = LovedOne


class RiderInline(admin.StackedInline):
    model = Rider


class CustomerAdmin(admin.ModelAdmin):
    inlines = [
        RiderInline,
        DestinationInline,
    ]
    raw_id_fields = ("subscription_account", "ride_account",)


admin.site.register(CustomUser, UserAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Rider)

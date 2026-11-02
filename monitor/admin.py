
from django.contrib import admin
from django import forms
from .models import AccessConcentrator, PPPoESession, PPPoEEvent
from .crypto import encrypt_password


class AccessConcentratorAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["password"].required = True
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={"autocomplete": "new-password"}
        ),
        help_text="Enter a new password only if you want to change the existing one."
    )

    class Meta:
        model = AccessConcentrator
        fields = ("name", "ip_address", "username", "password", "enabled")

    def save(self, commit=True):
        instance = super().save(commit=False)
        new_password = self.cleaned_data.get("password")

        if new_password:
            instance.encrypted_password = encrypt_password(new_password)

        # Never store the plaintext password in the database.
        instance.password = ""

        if commit:
            instance.save()
            self.save_m2m()

        return instance


@admin.register(AccessConcentrator)
class AccessConcentratorAdmin(admin.ModelAdmin):
    form = AccessConcentratorAdminForm

    list_display = ("name", "ip_address", "username", "enabled")
    list_filter = ("enabled",)
    search_fields = ("name", "ip_address", "username")
    readonly_fields = ()

    fieldsets = (
        ("AC Configuration", {
            "fields": (
                "name",
                "ip_address",
                "username",
                "password",
                "enabled",
            )
        }),
    )


admin.site.register(PPPoESession)
admin.site.register(PPPoEEvent)

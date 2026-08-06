from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class EmailAuthenticationForm(AuthenticationForm):
	username = forms.EmailField(
		label="Email",
		required=True,
		widget=forms.EmailInput(attrs={"class": "task_input full_width", "autofocus": True}),
	)


class EmailUpdateRequestForm(forms.Form):
	email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "task_input full_width"}))

	def clean_email(self):
		email = self.cleaned_data["email"]
		if User.objects.filter(email__iexact=email).exists():
			raise forms.ValidationError("That email address is already in use.")
		return email


class RegistrationIdentityForm(forms.Form):
	email = forms.EmailField(
		required=True,
		widget=forms.EmailInput(attrs={"class": "task_input full_width", "autofocus": True}),
	)

	def clean_email(self):
		email = self.cleaned_data["email"]
		if User.objects.filter(email__iexact=email).exists():
			raise forms.ValidationError("That email address is already in use.")
		return email


class RegistrationPasswordForm(forms.Form):
	password1 = forms.CharField(
		label="Enter Password",
		required=True,
		strip=False,
		widget=forms.PasswordInput(attrs={"class": "task_input full_width", "autofocus": True}),
	)
	password2 = forms.CharField(
		label="Confirm Password",
		required=True,
		strip=False,
		widget=forms.PasswordInput(attrs={"class": "task_input full_width"}),
	)

	def clean(self):
		cleaned_data = super().clean()
		password1 = cleaned_data.get("password1")
		password2 = cleaned_data.get("password2")

		if password1 and password2 and password1 != password2:
			self.add_error("password2", "Passwords do not match.")
			return cleaned_data

		if password1:
			try:
				validate_password(password1)
			except ValidationError as exc:
				self.add_error("password1", exc)

		return cleaned_data
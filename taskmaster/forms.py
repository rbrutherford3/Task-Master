from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


# Create your forms here.

class NewUserForm(UserCreationForm):
	email = forms.EmailField(required=True)

	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2")

	def save(self, commit=True):
		user = super(NewUserForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		if commit:
			user.save()
		return user


class UsernameUpdateForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ("username",)
		widgets = {
			"username": forms.TextInput(attrs={"class": "task_input full_width", "required": True}),
		}


class EmailUpdateRequestForm(forms.Form):
	email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "task_input full_width"}))


class RegistrationIdentityForm(forms.Form):
	username = forms.CharField(
		max_length=150,
		required=True,
		widget=forms.TextInput(attrs={"class": "task_input full_width"}),
	)
	email = forms.EmailField(
		required=True,
		widget=forms.EmailInput(attrs={"class": "task_input full_width"}),
	)

	def clean(self):
		cleaned_data = super().clean()
		username = cleaned_data.get("username")
		email = cleaned_data.get("email")

		# Enforce required validation order: username first, then email.
		if username and User.objects.filter(username__iexact=username).exists():
			self.add_error("username", "That username is already taken.")
			return cleaned_data

		if email and User.objects.filter(email__iexact=email).exists():
			self.add_error("email", "That email address is already in use.")

		return cleaned_data


class RegistrationPasswordForm(forms.Form):
	password1 = forms.CharField(
		label="Enter Password",
		required=True,
		strip=False,
		widget=forms.PasswordInput(attrs={"class": "task_input full_width"}),
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
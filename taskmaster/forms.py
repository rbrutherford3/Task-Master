from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


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
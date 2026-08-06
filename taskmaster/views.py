from django.shortcuts import render, redirect
from django.views import generic
from .models import Task
from .forms import (
    EmailAuthenticationForm,
    EmailUpdateRequestForm,
    RegistrationIdentityForm,
    RegistrationPasswordForm,
)
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.contrib.sites.shortcuts import get_current_site
from django.core import signing
import requests

RESEND_API_URL = "https://api.resend.com/emails"
SETTINGS_CONFIRM_SALT = "taskmaster.settings.confirm"
SETTINGS_CONFIRM_MAX_AGE = 60 * 60 * 24
REGISTER_IDENTITY_SESSION_KEY = "register_identity"
LOGIN_PENDING_ACTIVATION_SESSION_KEY = "login_pending_activation_uid"


def resend_send_email(subject, to, text=None, html=None):
    payload = {
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": to,
        "subject": subject,
    }
    if html is not None:
        payload["html"] = html
    if text is not None:
        payload["text"] = text

    response = requests.post(
        RESEND_API_URL,
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=10,
    )
    if not response.ok:
        raise RuntimeError(f"Resend API error {response.status_code}: {response.text}")
    return response.json()


def send_password_reset_email(request, user):
    subject = "Password Reset Requested"
    email_template_name = "taskmaster/password/password_reset_email.txt"
    context = {
        'user': user.email,
        'email': user.email,
        'domain': get_current_site(request).domain,
        'site_name': 'Spiff Industries',
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    }
    email = render_to_string(email_template_name, context)
    resend_send_email(subject, user.email, text=email)


def send_settings_confirmation_email(request, to_email, subject, payload, template_name):
    signed_payload = signing.dumps(payload, salt=SETTINGS_CONFIRM_SALT)
    confirm_url = (
        f"{'https' if request.is_secure() else 'http'}://"
        f"{get_current_site(request).domain}"
        f"{reverse('taskmaster:settings_confirm', args=[signed_payload])}"
    )
    message = render_to_string(template_name, {'confirm_url': confirm_url, 'user': request.user})
    resend_send_email(subject, to_email, text=message)

from .recaptchav3 import verify_recaptcha

# Show all tasks and group by urgency (hence the three queries)
class IndexView(generic.ListView):
    model = Task
    template_name = 'taskmaster/graphic.html'
    def get_context_data(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            context = super(IndexView, self).get_context_data(*args, **kwargs)
            context['low_urgency'] = Task.objects.filter(user=self.request.user.email).filter(urgency=0).order_by('-importance')
            context['med_urgency'] = Task.objects.filter(user=self.request.user.email).filter(urgency=1).order_by('-importance')
            context['high_urgency'] = Task.objects.filter(user=self.request.user.email).filter(urgency=2).order_by('-importance')
            context['all_tasks'] = Task.objects.filter(user=self.request.user.email)
        else:
            context = None
        return context

# Edit an existing task
class TaskFormView(generic.DetailView):
     model = Task
     template_name = 'taskmaster/graphic.html'

# Create new task
def new_task(request):
    return render(request, 'taskmaster/graphic.html')

# Save new task, save edited task, or delete a task
# (note that some fields require completion validation)
def save_task(self, *args, **kwargs):
    # If the save buton was pressed...
    if (self.POST.get('action') == "Save"):
        if (self.POST.get('pk')):
            task = Task.objects.filter(pk=self.POST.get('pk'))[0]
        else:
            task = Task()
        task.short_desc = self.POST.get('short_desc')
        if (len(self.POST.get('due_date')) > 0):
            task.due_date = self.POST.get('due_date')
        if (len(self.POST.get('due_time')) > 0):
            task.due_time = self.POST.get('due_time')
        task.importance = self.POST.get('importance')
        task.urgency = self.POST.get('urgency')
        if (len(self.POST.get('long_desc')) > 0):
            task.long_desc = self.POST.get('long_desc')
        task.user = self.user.email
        task.save()
    # Otherwise the delete button was pressed...
    else:
        Task.objects.get(id=self.POST.get('pk')).delete()
    return redirect('taskmaster:index')

# Toggle an existing task as complete or incomplete
def toggle(request, pk):
    task = Task.objects.filter(pk=pk)[0]
    task.completed = not task.completed
    task.save()
    return redirect('taskmaster:index')

# Delete all completed tasks (at user's discretion)
def purge(request):
    tasks = Task.objects.filter(user=request.user.email).filter(completed=True)
    for task in tasks:
        task.delete()
    return redirect('taskmaster:index')

def activateEmail(request, user, to_email):
    mail_subject = 'Activate your user account.'
    message = render_to_string('taskmaster/activate_account_email.txt', {
        'user': user.email,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    try:
        resend_send_email(mail_subject, to_email, text=message)
        messages.success(request, "Please go to your email inbox and click on \
            the received activation link to confirm and complete the registration. Note: Check your spam folder.")
    except Exception:
        messages.error(request, "Problem sending confirmation email, check if you typed it correctly.")

# Register a user account
def register_request(request):
    if request.method == "POST":
        secret_key = settings.RECAPTCHA_SECRET_KEY
        try:
            result_json = verify_recaptcha(request.POST.get('g-recaptcha-response'), secret_key=secret_key)
        except requests.RequestException:
            messages.error(request, "reCAPTCHA verification could not be completed.")
            form = RegistrationIdentityForm(request.POST)
            return render(request=request, template_name="taskmaster/register.html", context={"register_form": form, 'reCAPTCHA_site_key': settings.RECAPTCHA_SITE_KEY})

        form = RegistrationIdentityForm(request.POST)
        if not result_json.get('success'):
            messages.error(request, "If you identify as a robot, we have somewhere else for you to go")
            return render(request=request, template_name="taskmaster/register.html", context={"register_form": form, 'reCAPTCHA_site_key': settings.RECAPTCHA_SITE_KEY})

        if form.is_valid():
            request.session[REGISTER_IDENTITY_SESSION_KEY] = {
                'email': form.cleaned_data['email'],
            }
            return redirect('taskmaster:register_password')

        messages.error(request, "Please correct the highlighted fields.")
        return render(request=request, template_name="taskmaster/register.html", context={"register_form": form, 'reCAPTCHA_site_key': settings.RECAPTCHA_SITE_KEY})

    form = RegistrationIdentityForm()
    return render(request=request, template_name="taskmaster/register.html", context={"register_form": form, 'reCAPTCHA_site_key': settings.RECAPTCHA_SITE_KEY})


def register_password_request(request):
    identity = request.session.get(REGISTER_IDENTITY_SESSION_KEY)
    if not identity:
        messages.error(request, "Please complete step 1 (email address) first.")
        return redirect('taskmaster:register')

    if request.method == "POST":
        form = RegistrationPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.create_user(
                    username=identity['email'],
                    email=identity['email'],
                    password=form.cleaned_data['password1'],
                )
            except IntegrityError:
                messages.error(request, "Email became unavailable. Please try again.")
                request.session.pop(REGISTER_IDENTITY_SESSION_KEY, None)
                return redirect('taskmaster:register')

            user.is_active = False
            user.save()
            activateEmail(request, user, identity['email'])
            request.session.pop(REGISTER_IDENTITY_SESSION_KEY, None)
            return redirect('taskmaster:index')

        messages.error(request, "Please correct the password errors below.")
    else:
        form = RegistrationPasswordForm()

    return render(request=request, template_name="taskmaster/register_password.html", context={"password_form": form})

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Thank you for your email confirmation. Now you can log in your account.')
        return redirect('taskmaster:login')
    else:
        messages.error(request, 'Activation link is invalid!')
    
    return redirect('taskmaster:index')

# Log into a user account
def login_request(request):
    activation_message = "Please go to your email inbox and click on the received activation link to confirm and complete the registration. Note: Check your spam folder."
    resend_prompt = "Would you like to be resent the confirmation email?"

    if request.method == "GET":
        request.session.pop(LOGIN_PENDING_ACTIVATION_SESSION_KEY, None)

    if request.method == "POST" and request.POST.get('action') == 'resend_activation':
        pending_uid = request.session.get(LOGIN_PENDING_ACTIVATION_SESSION_KEY)
        if pending_uid:
            pending_user = User.objects.filter(pk=pending_uid, is_active=False).first()
            if pending_user:
                # Rotate the token seed so previously-issued activation links become invalid.
                pending_user.last_login = timezone.now()
                pending_user.save(update_fields=["last_login"])
                activateEmail(request, pending_user, pending_user.email)
                messages.success(request, "A new confirmation email has been sent.")
            else:
                messages.error(request, "No inactive account found for resending confirmation.")
        else:
            messages.error(request, "Please attempt login first so we can verify your account.")

        return render(
            request=request,
            template_name='taskmaster/login.html',
            context={
                "login_form": EmailAuthenticationForm(),
                'reCAPTCHA_site_key': settings.RECAPTCHA_SITE_KEY,
                'show_resend_activation': False,
                'resend_prompt': resend_prompt,
            }
        )

    if request.method == "POST":
        secret_key = settings.RECAPTCHA_SECRET_KEY
        try:
            result_json = verify_recaptcha(request.POST.get('g-recaptcha-response'), secret_key=secret_key)
        except requests.RequestException:
            messages.error(request, "reCAPTCHA verification could not be completed.")
            form = EmailAuthenticationForm()
            return render(request=request, template_name='taskmaster/login.html', context={"login_form": form, 'reCAPTCHA_site_key': settings.RECAPTCHA_SITE_KEY})
        if result_json.get('success'):
            form = EmailAuthenticationForm(request, data=request.POST)
            if form.is_valid():
                email = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(username=email, password=password)
                if user is not None:
                    request.session.pop(LOGIN_PENDING_ACTIVATION_SESSION_KEY, None)
                    login(request, user)
                    messages.info(request, f"You are now logged in as {email}.")
                    return redirect('taskmaster:index')
                else:
                    pending_user = User.objects.filter(email__iexact=email, is_active=False).first()
                    if pending_user and pending_user.check_password(password):
                        request.session[LOGIN_PENDING_ACTIVATION_SESSION_KEY] = pending_user.pk
                        messages.error(request, activation_message)
                    else:
                        request.session.pop(LOGIN_PENDING_ACTIVATION_SESSION_KEY, None)
                        messages.error(request,"Invalid email or password.")
            else:
                email = request.POST.get('username', '').strip()
                password = request.POST.get('password', '')
                pending_user = User.objects.filter(email__iexact=email, is_active=False).first()
                if pending_user and password and pending_user.check_password(password):
                    request.session[LOGIN_PENDING_ACTIVATION_SESSION_KEY] = pending_user.pk
                    messages.error(request, activation_message)
                else:
                    request.session.pop(LOGIN_PENDING_ACTIVATION_SESSION_KEY, None)
                    messages.error(request,"Invalid email or password.")
        else:
            messages.error(request,"Would you real homo-sapien please stand up?")
    form = EmailAuthenticationForm()
    return render(
        request=request,
        template_name='taskmaster/login.html',
        context={
            "login_form": form,
            'reCAPTCHA_site_key': settings.RECAPTCHA_SITE_KEY,
            'show_resend_activation': bool(request.session.get(LOGIN_PENDING_ACTIVATION_SESSION_KEY)),
            'resend_prompt': resend_prompt,
        }
    )

# Log out of a user account
def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.") 
	return redirect('taskmaster:index')


@login_required
def settings_view(request):
    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'password':
            try:
                send_password_reset_email(request, request.user)
                messages.success(request, "A password reset email has been sent to your inbox.")
            except Exception:
                messages.error(request, "Problem sending reset password email.")

        elif action == 'email':
            email_form = EmailUpdateRequestForm(request.POST)
            if email_form.is_valid():
                new_email = email_form.cleaned_data['email']
                payload = {
                    'action': 'email_change',
                    'uid': request.user.pk,
                    'new_email': new_email,
                }
                try:
                    send_settings_confirmation_email(
                        request,
                        new_email,
                        "Confirm your Task Master email change",
                        payload,
                        "taskmaster/settings_confirm_email_change.txt",
                    )
                    messages.success(request, "Check your new email for a confirmation link.")
                except Exception:
                    messages.error(request, "Problem sending email confirmation.")
            else:
                email_errors = email_form.errors.get('email')
                if email_errors:
                    messages.error(request, email_errors[0])
                else:
                    messages.error(request, "Please provide a valid email address.")
                return render(
                    request,
                    "taskmaster/settings.html",
                    {
                        'email_form': email_form,
                        'reCAPTCHA_site_key': settings.RECAPTCHA_SITE_KEY,
                    }
                )

        elif action == 'delete':
            payload = {
                'action': 'delete_account',
                'uid': request.user.pk,
            }
            try:
                send_settings_confirmation_email(
                    request,
                    request.user.email,
                    "Confirm your Task Master account deletion",
                    payload,
                    "taskmaster/settings_confirm_delete.txt",
                )
                messages.success(request, "Check your email for the account deletion confirmation link.")
            except Exception:
                messages.error(request, "Problem sending account deletion confirmation email.")

        return redirect('taskmaster:settings')

    return render(
        request,
        "taskmaster/settings.html",
        {
            'email_form': EmailUpdateRequestForm(initial={'email': request.user.email}),
            'reCAPTCHA_site_key': settings.RECAPTCHA_SITE_KEY,
        }
    )


def settings_confirm(request, signed_payload):
    try:
        data = signing.loads(signed_payload, salt=SETTINGS_CONFIRM_SALT, max_age=SETTINGS_CONFIRM_MAX_AGE)
    except signing.BadSignature:
        messages.error(request, "This confirmation link is invalid or has expired.")
        return redirect('taskmaster:index')

    action = data.get('action')
    uid = data.get('uid')

    try:
        user = User.objects.get(pk=uid)
    except User.DoesNotExist:
        messages.error(request, "The requested account no longer exists.")
        return redirect('taskmaster:index')

    if action == 'email_change':
        new_email = data.get('new_email')
        if not new_email:
            messages.error(request, "Invalid email change request.")
            return redirect('taskmaster:index')
        if User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
            messages.error(request, "That email address is already in use.")
            return redirect('taskmaster:settings')
        old_identity = user.username
        user.email = new_email
        user.username = new_email
        user.save()
        Task.objects.filter(user=old_identity).update(user=new_email)
        messages.success(request, "Email address updated successfully.")
        return redirect('taskmaster:settings')

    if action == 'delete_account':
        username = user.username
        Task.objects.filter(user=username).delete()
        if request.user.is_authenticated and request.user.pk == user.pk:
            logout(request)
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect('taskmaster:index')

    messages.error(request, "Unknown account action.")
    return redirect('taskmaster:index')

def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    try:
                        send_password_reset_email(request, user)
                    except Exception:
                        return HttpResponse('Problem sending reset password email.')
                    messages.success(request, 'A message with reset password instructions has been sent to your inbox.')
                    return redirect ("taskmaster:index")
            else:
                messages.error(request, 'There is no account associated with that email address.')
        else:
            messages.error(request, 'An invalid email has been entered.')
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="taskmaster/password/password_reset.html", context={"password_reset_form":password_reset_form,'reCAPTCHA_site_key':settings.RECAPTCHA_SITE_KEY})

def password_reset_complete(request):
    messages.success(request, "Your password has been successfully reset, you may now log in")
    return redirect('taskmaster:login')

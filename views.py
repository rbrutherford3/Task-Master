from django.shortcuts import render, redirect
from django.views import generic
from .models import Task
from .forms import NewUserForm
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm #add this
from django.conf import settings
from django.shortcuts import render, redirect
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
import requests

# Show all tasks and group by urgency (hence the three queries)
class IndexView(generic.ListView):
    model = Task
    template_name = 'taskmaster/graphic.html'
    def get_context_data(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            context = super(IndexView, self).get_context_data(*args, **kwargs)
            context['low_urgency'] = Task.objects.filter(user=self.request.user.username).filter(urgency=0).order_by('-importance')
            context['med_urgency'] = Task.objects.filter(user=self.request.user.username).filter(urgency=1).order_by('-importance')
            context['high_urgency'] = Task.objects.filter(user=self.request.user.username).filter(urgency=2).order_by('-importance')
            context['all_tasks'] = Task.objects.filter(user=self.request.user.username)
        else:
            context = None
        return context

# Edit an existing task
class TaskFormView(generic.DetailView):
     model = Task
     template_name = 'taskmaster/form.html'

# Create new task
def new_task(request):
    return render(request, 'taskmaster/form.html')

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
        task.user = self.user.username
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
    tasks = Task.objects.filter(user=request.user).filter(completed=True)
    for task in tasks:
        task.delete()
    return redirect('taskmaster:index')

def activateEmail(request, user, to_email):
    mail_subject = 'Activate your user account.'
    message = render_to_string('taskmaster/activate_account_email.txt', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email], from_email="no-reply@spiffindustries.com")
    if email.send():
        messages.success(request, "Please go to you email inbox and click on \
            received activation link to confirm and complete the registration. Note: Check your spam folder.")
    else:
        messages.error(request, "Problem sending confirmation email, check if you typed it correctly.")

# Register a user account
def register_request(request):
    if request.method == "POST":
        secret_key = settings.RECAPTCHA_SECRET_KEY
        # captcha verification
        data = {
            'response': request.POST['g-recaptcha-response'],
            'secret': secret_key
        }
        resp = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result_json = resp.json()
        print(result_json)
        if result_json.get('success'):
            form = NewUserForm(request.POST)
            if form.is_valid():
                user = form.save()
                user.is_active=False
                user.save()
                activateEmail(request, user, form.cleaned_data.get('email'))
                return redirect('taskmaster:index')
            messages.error(request, "Unsuccessful registration. Invalid information.")
        else:
            messages.error(request, "If you identify as a robot, we have somewhere else for you to go")
    form = NewUserForm()
    return render (request=request, template_name="taskmaster/register.html", context={"register_form":form,'reCAPTCHA_site_key':settings.RECAPTCHA_SITE_KEY})

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
    if request.method == "POST":
        secret_key = settings.RECAPTCHA_SECRET_KEY
        # captcha verification
        data = {
            'response': request.POST['g-recaptcha-response'],
            'secret': secret_key
        }
        resp = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result_json = resp.json()
        print(result_json)
        if result_json.get('success'):
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.info(request, f"You are now logged in as {username}.")
                    return redirect('taskmaster:index')
                else:
                    messages.error(request,"Invalid username or password.")
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Would you real homo-sapien please stand up?")
    form = AuthenticationForm()
    return render(request=request, template_name='taskmaster/login.html', context={"login_form":form,'reCAPTCHA_site_key':settings.RECAPTCHA_SITE_KEY})

# Log out of a user account
def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.") 
	return redirect('taskmaster:index')

def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "taskmaster/password/password_reset_email.txt"
                    c = {
                    'email':user.email,
                    'domain': get_current_site(request).domain,
                    'site_name': 'Spiff Industries',
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                    'protocol': 'https' if request.is_secure() else 'http'
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email, 'no-reply@spiffindustries.com' , [user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    messages.success(request, 'A message with reset password instructions has been sent to your inbox.')
                    return redirect ("taskmaster:index")
            else:
                messages.error(request, 'There is no account associated with that email address.')
        else:
            messages.error(request, 'An invalid email has been entered.')
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="taskmaster/password/password_reset.html", context={"password_reset_form":password_reset_form})

def password_reset_complete(request):
    messages.success(request, "Your password has been successfully reset, you may now log in")
    return redirect('taskmaster:login')

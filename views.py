from django.shortcuts import render, redirect
from django.views import generic
from .models import Task
from .forms import NewUserForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm #add this

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

# Register a user account
def register_request(request):
	if request.method == "POST":
		form = NewUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, "Registration successful." )
			return redirect('taskmaster:login')
		messages.error(request, "Unsuccessful registration. Invalid information.")
	form = NewUserForm()
	return render (request=request, template_name="taskmaster/register.html", context={"register_form":form})

# Log into a user account
def login_request(request):
	if request.method == "POST":
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
	form = AuthenticationForm()
	return render(request=request, template_name='taskmaster/login.html', context={"login_form":form})

# Log out of a user account
def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.") 
	return redirect('taskmaster:index')
from django.shortcuts import render, redirect
from django.views import generic
from .models import Task

# Show all tasks and group by urgency (hence the three queries)
class IndexView(generic.ListView):
     model = Task
     template_name = 'taskmaster/graphic.html'
     def get_context_data(self, *args, **kwargs):
         context = super(IndexView, self).get_context_data(*args, **kwargs)
         context['low_urgency'] = Task.objects.filter(urgency=0).order_by('-importance')
         context['med_urgency'] = Task.objects.filter(urgency=1).order_by('-importance')
         context['high_urgency'] = Task.objects.filter(urgency=2).order_by('-importance')
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
def save_task(request):
    # If the save buton was pressed...
    if (request.POST.get('action') == "Save"):
        if (request.POST.get('pk')):
            task = Task.objects.filter(pk=request.POST.get('pk'))[0]
        else:
            task = Task()
        task.short_desc = request.POST.get('short_desc')
        if (len(request.POST.get('due_date')) > 0):
            task.due_date = request.POST.get('due_date')
        if (len(request.POST.get('due_time')) > 0):
            task.due_time = request.POST.get('due_time')
        task.importance = request.POST.get('importance')
        task.urgency = request.POST.get('urgency')
        if (len(request.POST.get('long_desc')) > 0):
            task.long_desc = request.POST.get('long_desc')
        task.save()
    # Otherwise the delete button was pressed...
    else:
        Task.objects.get(id=request.POST.get('pk')).delete()
    return redirect('taskmaster:index')

# Toggle an existing task as complete or incomplete
def toggle(request, pk):
    task = Task.objects.filter(pk=pk)[0]
    task.completed = not task.completed
    task.save()
    return redirect('taskmaster:index')

# Delete all completed tasks (at user's discretion)
def purge(request):
    tasks = Task.objects.filter(completed=True)
    for task in tasks:
        task.delete()
    return redirect('taskmaster:index')

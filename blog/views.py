from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from urllib.parse import urlencode

from .models import Blog_Post,Category,Comment
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.db.models import Count,Q
from .forms import CommentForm, ReplyForm
# Create your views here.

    
def get_category_count():
  queryset = Blog_Post\
    .objects\
    .values('categories__title') \
    .annotate(Count('categories__title'))
  return queryset

 
def search(request):
  category_count = get_category_count()
  category_list = Category.objects.all()
  bloglist = Blog_Post.objects.all().order_by('-Timestamp')
  query = request.GET.get('q')

  if query:
    bloglist = bloglist.filter(
      Q(title__icontains = query) |
      Q(overview__icontains = query) |
      Q(meta_description__icontains = query) |       
      Q(meta_keywords__icontains = query) |      
      Q(meta_title__icontains = query) |      
      Q(meta_author__icontains = query)|        
      Q(categories__title__icontains = query)     
    ).distinct()

  paginator = Paginator(bloglist,1)
  page_request_variable = 'page'
  page = request.GET.get(page_request_variable)
  try:
    paginated_queryset = paginator.page(page)
  except EmptyPage:
    paginated_queryset = paginator.page(2)
  except PageNotAnInteger:
    paginated_queryset = paginator.page(1)

  latest = Blog_Post.objects.order_by('-Timestamp')[0:3]
  context = {   
    'category_count' : category_count,
    'bloglist' : paginated_queryset,
    'page_request_variable' : page_request_variable,
    'latest':latest,
    'query':query,
    'category_list':category_list,
  }


  return render(request,'search_result.html',context)


def blog(request):
  category_list = Category.objects.all()
  category_count = get_category_count()
  bloglist = Blog_Post.objects.all().order_by('-Timestamp')
  paginator = Paginator(bloglist,2)
  page_request_variable = 'page'
  page = request.GET.get(page_request_variable)
  try:
    paginated_queryset = paginator.page(page)
  except EmptyPage:
    paginated_queryset = paginator.page(paginator.num_pages)
  except PageNotAnInteger:
    paginated_queryset = paginator.page(1)
  
  latest = Blog_Post.objects.order_by ('-Timestamp')[0:3]


  context = {
    'category_list' : category_list,
    'category_count' : category_count,
    'bloglist' : paginated_queryset,
    'page_request_variable' : page_request_variable,
    'latest':latest,
  }
  return render(request,'blog-grid.html',context)


def post(request, slug):
    post = get_object_or_404(Blog_Post, new_blog_slug=slug)

    if request.method == 'POST':
        if request.user.is_authenticated:
            parent_id = request.POST.get('parent_id')
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                form = ReplyForm(request.POST)
                if form.is_valid():
                    reply = form.save(commit=False)
                    reply.post = post
                    reply.author = request.user
                    reply.parent = parent_comment
                    reply.save()
                    return redirect(request.path_info)
            else:
                form = CommentForm(request.POST)
                if form.is_valid():
                    comment = form.save(commit=False)
                    comment.post = post
                    comment.author = request.user
                    comment.save()
                    return redirect(request.path_info)
        else:
            # Redirect to login with the next parameter
            login_url = reverse('account_login')
            next_url = request.get_full_path()
            encoded_next_url = urlencode({'next': next_url})
            print(f"Redirecting to login URL: {login_url}?{encoded_next_url}")
            return redirect(f'{login_url}?{encoded_next_url}')
    else:
        form = CommentForm()
        reply_form = ReplyForm()

    latest = Blog_Post.objects.order_by('-Timestamp')[:3]
    comments = post.comments.filter(parent__isnull=True).order_by('-created_at')

    context = {
        'post': post,
        'latest': latest,
        'comments': comments,
        'form': form,
        'reply_form': reply_form,
    }
    return render(request, 'blog-details.html', context)
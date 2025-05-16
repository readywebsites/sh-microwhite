
from enum import unique
from django.urls import reverse
from django.db import models
from django.contrib.auth import get_user_model
from tinymce.models import HTMLField
from autoslug import AutoSlugField
from django.conf import settings



class Team(models.Model):
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=100)
    description = models.TextField()
    pic = models.ImageField(upload_to='new_media/')
    
    def __str__(self):
      return self.name

class Category (models.Model):
  title = models.CharField(max_length=20)

  def __str__(self):
    return self.title

class Hashtags (models.Model):
  tag = models.CharField(max_length=20)
  def __str__(self):
    return self.tag

class Blog_Post(models.Model):
  title = models.CharField(max_length=100)
  Description =HTMLField()
  Timestamp = models.DateTimeField(auto_now_add= True)
  author = models.ForeignKey(Team, on_delete=models.CASCADE)
  thumbnail_800_563 = models.ImageField(upload_to='new_media/')
  categories = models.ManyToManyField(Category)
  hashtags = models.ManyToManyField(Hashtags,blank=True)
  # project = models.BooleanField()
  meta_description = models.CharField(max_length=100, blank=True)
  meta_keywords = models.CharField(max_length=1000,blank=True)
  meta_title = models.CharField(max_length=100, blank=True)
  meta_author = models.CharField(max_length=100, blank=True)
  new_blog_slug = AutoSlugField(populate_from='title',unique=True, null=True, default=None )
  def __str__(self):
    return self.title

  def get_absolute_url(self):
    return reverse('post',kwargs={
      'slug':self.new_blog_slug
    })
  def __str__(self):
    return self.title

class Comment(models.Model):
    post = models.ForeignKey(Blog_Post, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    
    def __str__(self):
        return f'Comment by {self.author} on {self.post}'
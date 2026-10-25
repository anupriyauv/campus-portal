from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count

from .models import Club, ClubMembership
from .forms import ClubForm, ClubMembershipForm
from apps.events.models import Event
from apps.accounts.models import User
from apps.accounts.utils import log_audit_event


class ClubListView(ListView):
    model = Club
    template_name = 'clubs/club_list.html'
    context_object_name = 'clubs'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Club.objects.filter(is_active=True).annotate(
            member_count=Count('members')
        )
        
        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Club.CATEGORY_CHOICES
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class ClubDetailView(DetailView):
    model = Club
    template_name = 'clubs/club_detail.html'
    context_object_name = 'club'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        club = self.get_object()
        
        # Check if user is a member
        if self.request.user.is_authenticated:
            context['is_member'] = club.members.filter(id=self.request.user.id).exists()
            if context['is_member']:
                context['membership'] = ClubMembership.objects.get(
                    club=club,
                    user=self.request.user
                )
            context['is_coordinator_user'] = (club.coordinator == self.request.user)
        
        # Get club events
        context['upcoming_events'] = Event.objects.filter(
            club=club,
            status='PUBLISHED'
        ).order_by('start_datetime')[:5]
        
        # Get club members
        context['members'] = club.clubmembership_set.select_related('user').filter(
            is_active=True
        ).order_by('-role', 'joined_date')
        
        context['member_count'] = context['members'].count()
        
        return context


class ClubCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Club
    form_class = ClubForm
    template_name = 'clubs/club_form.html'
    success_url = reverse_lazy('clubs:club_list')
    
    def test_func(self):
        return self.request.user.is_admin()
    
    def form_valid(self, form):
        form.instance.coordinator = self.request.user
        response = super().form_valid(form)
        log_audit_event(self.request.user, 'CREATE', model_name='Club', object_id=self.object.id, object_repr=self.object.name, ip_address=self.request.META.get('REMOTE_ADDR'))
        messages.success(self.request, 'Club created successfully!')
        return response


class ClubUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Club
    form_class = ClubForm
    template_name = 'clubs/club_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def test_func(self):
        club = self.get_object()
        return club.coordinator == self.request.user
    
    def get_success_url(self):
        return reverse_lazy('clubs:club_detail', kwargs={'slug': self.object.slug})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit_event(self.request.user, 'UPDATE', model_name='Club', object_id=self.object.id, object_repr=self.object.name, change_message='Club details updated', ip_address=self.request.META.get('REMOTE_ADDR'))
        messages.success(self.request, 'Club updated successfully!')
        return response


@login_required
def join_club(request, slug):
    if request.user.is_admin():
        messages.error(request, 'Administrators cannot join clubs.')
        return redirect('clubs:club_detail', slug=slug)

    club = get_object_or_404(Club, slug=slug)
    
    if not club.is_active:
        messages.error(request, 'This club is currently inactive and cannot be joined.')
        return redirect('clubs:club_detail', slug=slug)

    # Check if the user is already a member of any club
    if ClubMembership.objects.filter(user=request.user).exists():
        messages.error(request, 'You can only be a member of one club at a time.')
        return redirect('clubs:club_detail', slug=slug)

    if club.members.filter(id=request.user.id).exists():
        messages.warning(request, 'You are already a member of this club.')
    else:
        ClubMembership.objects.create(
            club=club,
            user=request.user,
            role='MEMBER'
        )
        log_audit_event(request.user, 'JOIN_CLUB', model_name='ClubMembership', object_id=club.id, object_repr=club.name, change_message=f'Joined club {club.name}', ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f'You have successfully joined {club.name}!')
    
    return redirect('clubs:club_detail', slug=slug)


@login_required
def leave_club(request, slug):
    if request.user.is_admin():
        messages.error(request, 'Administrators cannot leave clubs.')
        return redirect('clubs:club_detail', slug=slug)

    club = get_object_or_404(Club, slug=slug)
    
    if not club.is_active:
        messages.error(request, 'This club is currently inactive and cannot be left.')
        return redirect('clubs:club_detail', slug=slug)

    try:
        membership = ClubMembership.objects.get(club=club, user=request.user)
        membership.delete()
        log_audit_event(request.user, 'LEAVE_CLUB', model_name='ClubMembership', object_id=club.id, object_repr=club.name, change_message=f'Left club {club.name}', ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f'You have left {club.name}.')
    except ClubMembership.DoesNotExist:
        messages.error(request, 'You are not a member of this club.')
    
    return redirect('clubs:club_detail', slug=slug)


@login_required
def my_clubs(request):
    memberships = ClubMembership.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('club').order_by('-joined_date')
    
    context = {
        'memberships': memberships,
    }
    
    return render(request, 'clubs/my_clubs.html', context)
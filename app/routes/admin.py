from flask import render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.routes import admin_bp
from app.models import User, Member, Leader, News, Event, Project, Gallery, Topic, Newsletter, Blog
from app import db
from datetime import datetime
import os
import json

def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Get statistics
    total_members = Member.query.join(Member.user).filter(Member.user.has(is_approved=True)).count()
    pending_approvals = User.query.filter_by(role='student', is_approved=False).count()
    upcoming_events = Event.query.filter(Event.event_date >= datetime.utcnow()).count()
    newsletter_subscribers = Newsletter.query.filter_by(is_active=True).count()
    
    # Get recent activity
    recent_news = News.query.order_by(News.published_date.desc()).limit(5).all()
    pending_users = User.query.filter_by(role='student', is_approved=False).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_members=total_members,
                         pending_approvals=pending_approvals,
                         upcoming_events=upcoming_events,
                         newsletter_subscribers=newsletter_subscribers,
                         recent_news=recent_news,
                         pending_users=pending_users)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    pending_users = User.query.filter_by(role='student', is_approved=False).all()
    return render_template('admin/users.html', pending_users=pending_users)

@admin_bp.route('/approve-user/<int:user_id>')
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'User {user.email} has been approved.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/reject-user/<int:user_id>')
@login_required
@admin_required
def reject_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.email} has been rejected and removed.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/news')
@login_required
@admin_required
def news():
    news_items = News.query.order_by(News.published_date.desc()).all()
    return render_template('admin/news.html', news_items=news_items)

@admin_bp.route('/news/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_news():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        
        news_item = News(
            title=title,
            content=content,
            category=category,
            author_id=current_user.id
        )
        db.session.add(news_item)
        db.session.commit()
        
        flash('News article added successfully.', 'success')
        return redirect(url_for('admin.news'))
    
    return render_template('admin/add_news.html')

@admin_bp.route('/news/edit/<int:news_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_news(news_id):
    news_item = News.query.get_or_404(news_id)
    
    if request.method == 'POST':
        news_item.title = request.form.get('title')
        news_item.content = request.form.get('content')
        news_item.category = request.form.get('category')
        db.session.commit()
        
        flash('News article updated successfully.', 'success')
        return redirect(url_for('admin.news'))
    
    return render_template('admin/edit_news.html', news_item=news_item)

@admin_bp.route('/news/delete/<int:news_id>')
@login_required
@admin_required
def delete_news(news_id):
    news_item = News.query.get_or_404(news_id)
    db.session.delete(news_item)
    db.session.commit()
    
    flash('News article deleted successfully.', 'success')
    return redirect(url_for('admin.news'))

@admin_bp.route('/events')
@login_required
@admin_required
def events():
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('admin/events.html', events=events)

@admin_bp.route('/events/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_event():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_date = datetime.strptime(request.form.get('event_date'), '%Y-%m-%dT%H:%M')
        location = request.form.get('location')
        
        event = Event(
            title=title,
            description=description,
            event_date=event_date,
            location=location
        )
        db.session.add(event)
        db.session.commit()
        
        flash('Event added successfully.', 'success')
        return redirect(url_for('admin.events'))
    
    return render_template('admin/add_event.html')

@admin_bp.route('/projects')
@login_required
@admin_required
def projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('admin/projects.html', projects=projects)

@admin_bp.route('/projects/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_project():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        github_link = request.form.get('github_link')
        demo_link = request.form.get('demo_link')
        technologies = request.form.get('technologies')
        team_members = request.form.get('team_members')
        
        project = Project(
            title=title,
            description=description,
            github_link=github_link,
            demo_link=demo_link,
            technologies=technologies,
            team_members=team_members
        )
        db.session.add(project)
        db.session.commit()
        
        flash('Project added successfully.', 'success')
        return redirect(url_for('admin.projects'))
    
    return render_template('admin/add_project.html')

@admin_bp.route('/gallery')
@login_required
@admin_required
def gallery():
    gallery_items = Gallery.query.order_by(Gallery.uploaded_at.desc()).all()
    return render_template('admin/gallery.html', gallery_items=gallery_items)

@admin_bp.route('/gallery/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_gallery_item():
    if request.method == 'POST':
        item_type = request.form.get('type')
        url = request.form.get('url')
        caption = request.form.get('caption')
        
        gallery_item = Gallery(
            type=item_type,
            url=url,
            caption=caption
        )
        db.session.add(gallery_item)
        db.session.commit()
        
        flash('Gallery item added successfully.', 'success')
        return redirect(url_for('admin.gallery'))
    
    return render_template('admin/add_gallery_item.html')

@admin_bp.route('/newsletter')
@login_required
@admin_required
def newsletter():
    subscribers = Newsletter.query.filter_by(is_active=True).order_by(Newsletter.subscribed_at.desc()).all()
    return render_template('admin/newsletter.html', subscribers=subscribers)

# Missing routes for edit/delete operations
@admin_bp.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    if request.method == 'POST':
        event.title = request.form.get('title')
        event.description = request.form.get('description')
        event.event_date = datetime.strptime(request.form.get('event_date'), '%Y-%m-%dT%H:%M')
        event.location = request.form.get('location')
        db.session.commit()
        
        flash('Event updated successfully.', 'success')
        return redirect(url_for('admin.events'))
    
    return render_template('admin/edit_event.html', event=event)

@admin_bp.route('/events/delete/<int:event_id>')
@login_required
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('admin.events'))

@admin_bp.route('/projects/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        project.github_link = request.form.get('github_link')
        project.demo_link = request.form.get('demo_link')
        project.technologies = request.form.get('technologies')
        project.team_members = request.form.get('team_members')
        db.session.commit()
        
        flash('Project updated successfully.', 'success')
        return redirect(url_for('admin.projects'))
    
    return render_template('admin/edit_project.html', project=project)

@admin_bp.route('/projects/delete/<int:project_id>')
@login_required
@admin_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    
    flash('Project deleted successfully.', 'success')
    return redirect(url_for('admin.projects'))

@admin_bp.route('/gallery/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_gallery_item(item_id):
    item = Gallery.query.get_or_404(item_id)
    
    if request.method == 'POST':
        item.type = request.form.get('type')
        item.url = request.form.get('url')
        item.caption = request.form.get('caption')
        db.session.commit()
        
        flash('Gallery item updated successfully.', 'success')
        return redirect(url_for('admin.gallery'))
    
    return render_template('admin/edit_gallery_item.html', item=item)

@admin_bp.route('/gallery/delete/<int:item_id>')
@login_required
@admin_required
def delete_gallery_item(item_id):
    item = Gallery.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    
    flash('Gallery item deleted successfully.', 'success')
    return redirect(url_for('admin.gallery'))

# Leader Management Routes
@admin_bp.route('/leaders')
@login_required
@admin_required
def leaders():
    leaders = Leader.query.join(Member).order_by(Leader.display_order.asc()).all()
    return render_template('admin/leaders.html', leaders=leaders)

@admin_bp.route('/leaders/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_leader():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        position = request.form.get('position')
        display_order = request.form.get('display_order', 0, type=int)
        
        # Check if user already has a leadership position
        existing_leader = Leader.query.filter_by(user_id=user_id).first()
        if existing_leader:
            flash('This user already has a leadership position.', 'warning')
            return redirect(url_for('admin.add_leader'))
        
        leader = Leader(
            user_id=user_id,
            position=position,
            display_order=display_order
        )
        
        db.session.add(leader)
        db.session.commit()
        
        flash('Leader added successfully.', 'success')
        return redirect(url_for('admin.leaders'))
    
    # Get all approved members who are not already leaders
    existing_leader_ids = [l.user_id for l in Leader.query.all()]
    members = Member.query.join(Member.user).filter(
        Member.user.has(is_approved=True),
        ~Member.user_id.in_(existing_leader_ids)
    ).all()
    
    return render_template('admin/add_leader.html', members=members)

@admin_bp.route('/leaders/edit/<int:leader_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_leader(leader_id):
    leader = Leader.query.get_or_404(leader_id)
    
    if request.method == 'POST':
        leader.position = request.form.get('position')
        leader.display_order = request.form.get('display_order', 0, type=int)
        
        db.session.commit()
        
        flash('Leader updated successfully.', 'success')
        return redirect(url_for('admin.leaders'))
    
    return render_template('admin/edit_leader.html', leader=leader)

@admin_bp.route('/leaders/delete/<int:leader_id>')
@login_required
@admin_required
def delete_leader(leader_id):
    leader = Leader.query.get_or_404(leader_id)
    db.session.delete(leader)
    db.session.commit()
    
    flash('Leader removed successfully.', 'success')
    return redirect(url_for('admin.leaders'))

# Blog Management Routes
@admin_bp.route('/blogs')
@login_required
@admin_required
def blogs():
    blogs = Blog.query.order_by(Blog.created_at.desc()).all()
    return render_template('admin/blogs.html', blogs=blogs)

@admin_bp.route('/blogs/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_blog():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt')
        category = request.form.get('category')
        tags = request.form.get('tags')
        is_published = 'is_published' in request.form
        
        # Generate slug from title
        slug = title.lower().replace(' ', '-').replace('&', 'and')
        slug = ''.join(c for c in slug if c.isalnum() or c in '-')
        
        # Ensure unique slug
        original_slug = slug
        counter = 1
        while Blog.query.filter_by(slug=slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        blog = Blog(
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt,
            author_id=current_user.id,
            category=category,
            tags=tags,
            is_published=is_published,
            published_date=datetime.utcnow() if is_published else None
        )
        
        db.session.add(blog)
        db.session.commit()
        
        flash('Blog post created successfully.', 'success')
        return redirect(url_for('admin.blogs'))
    
    return render_template('admin/add_blog.html')

@admin_bp.route('/blogs/edit/<int:blog_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    
    if request.method == 'POST':
        blog.title = request.form.get('title')
        blog.content = request.form.get('content')
        blog.excerpt = request.form.get('excerpt')
        blog.category = request.form.get('category')
        blog.tags = request.form.get('tags')
        blog.is_published = 'is_published' in request.form
        
        if blog.is_published and not blog.published_date:
            blog.published_date = datetime.utcnow()
        
        db.session.commit()
        
        flash('Blog post updated successfully.', 'success')
        return redirect(url_for('admin.blogs'))
    
    return render_template('admin/edit_blog.html', blog=blog)

@admin_bp.route('/blogs/delete/<int:blog_id>')
@login_required
@admin_required
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    db.session.delete(blog)
    db.session.commit()
    
    flash('Blog post deleted successfully.', 'success')
    return redirect(url_for('admin.blogs'))
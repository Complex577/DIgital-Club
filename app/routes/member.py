from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.routes import member_bp
from app.models import Member, Project
from app import db
import os
import json

@member_bp.route('/')
@login_required
def dashboard():
    if not current_user.member:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('member.edit_profile'))
    
    return render_template('member/dashboard.html', member=current_user.member)

@member_bp.route('/profile')
@login_required
def profile():
    if not current_user.member:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('member.edit_profile'))
    
    return render_template('member/profile.html', member=current_user.member)

@member_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    member = current_user.member
    
    if request.method == 'POST':
        # Update member information
        if not member:
            member = Member(user_id=current_user.id)
            db.session.add(member)
        
        member.full_name = request.form.get('full_name')
        member.title = request.form.get('title')
        member.bio = request.form.get('bio')
        member.course = request.form.get('course')
        member.year = request.form.get('year')
        member.status = request.form.get('status')
        member.phone = request.form.get('phone')
        member.github = request.form.get('github')
        member.linkedin = request.form.get('linkedin')
        member.areas_of_interest = request.form.get('areas_of_interest')
        
        # Handle projects (JSON format)
        projects_text = request.form.get('projects')
        if projects_text:
            try:
                projects_list = json.loads(projects_text)
                member.set_projects(projects_list)
            except:
                flash('Invalid projects format. Please use valid JSON.', 'error')
                return render_template('member/edit_profile.html', member=member)
        
        # Handle profile image upload
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    # Create unique filename
                    timestamp = str(int(datetime.utcnow().timestamp()))
                    filename = f"{current_user.id}_{timestamp}_{filename}"
                    
                    # Save file
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', filename)
                    file.save(upload_path)
                    
                    # Delete old image if exists
                    if member.profile_image:
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', member.profile_image)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    
                    member.profile_image = filename
                else:
                    flash('Invalid file type. Please upload PNG, JPG, JPEG, or GIF.', 'error')
                    return render_template('member/edit_profile.html', member=member)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('member.dashboard'))
    
    return render_template('member/edit_profile.html', member=member)

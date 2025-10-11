from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='student')  # admin or student
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to member profile
    member = db.relationship('Member', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100))  # e.g., "Software Developer", "Data Scientist"
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(200))
    course = db.Column(db.String(100))  # e.g., "Computer Science", "IT"
    year = db.Column(db.String(20))  # e.g., "Year 2", "Graduate"
    status = db.Column(db.String(20), default='student')  # student or alumni
    phone = db.Column(db.String(20))
    github = db.Column(db.String(200))
    linkedin = db.Column(db.String(200))
    projects_json = db.Column(db.Text)  # JSON string of projects
    areas_of_interest = db.Column(db.Text)  # Comma-separated areas
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_projects(self):
        if self.projects_json:
            try:
                return json.loads(self.projects_json)
            except:
                return []
        return []
    
    def set_projects(self, projects_list):
        self.projects_json = json.dumps(projects_list)
    
    def get_areas_list(self):
        if self.areas_of_interest:
            return [area.strip() for area in self.areas_of_interest.split(',')]
        return []
    
    def __repr__(self):
        return f'<Member {self.full_name}>'

class Leader(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    position = db.Column(db.String(100), nullable=False)  # e.g., "President", "Vice President"
    display_order = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Leader {self.position}>'

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))
    category = db.Column(db.String(50), default='general')  # hackathon, achievement, general
    published_date = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<News {self.title}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Event {self.title}>'

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(200))
    github_link = db.Column(db.String(200))
    demo_link = db.Column(db.String(200))
    technologies = db.Column(db.String(200))  # Comma-separated tech stack
    team_members = db.Column(db.String(200))  # Comma-separated member names
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_technologies_list(self):
        if self.technologies:
            return [tech.strip() for tech in self.technologies.split(',')]
        return []
    
    def get_team_list(self):
        if self.team_members:
            return [member.strip() for member in self.team_members.split(',')]
        return []
    
    def __repr__(self):
        return f'<Project {self.title}>'

class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # image or video
    url = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(200))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Gallery {self.type}>'

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))  # Font Awesome icon class
    
    def __repr__(self):
        return f'<Topic {self.name}>'

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Newsletter {self.email or self.phone}>'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), default='general')
    featured_image = db.Column(db.String(200))
    tags = db.Column(db.String(200))  # Comma-separated tags
    is_published = db.Column(db.Boolean, default=False)
    published_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    
    # Relationship
    author = db.relationship('User', backref='blog_posts')
    
    def get_tags_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def set_tags_list(self, tags_list):
        self.tags = ', '.join(tags_list)
    
    def __repr__(self):
        return f'<Blog {self.title}>'
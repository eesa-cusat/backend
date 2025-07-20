from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import random

from academics.models import Scheme, Subject, AcademicCategory, AcademicResource
from events.models import Event, EventRegistration
from gallery.models import GalleryCategory, GalleryAlbum, GalleryImage
from projects.models import Project, TeamMember, ProjectImage
from placements.models import Company, PlacementDrive, PlacementStatistics, PlacedStudent
from alumni.models import Alumni
from accounts.models import TeamMember as AccountTeamMember

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate backend with comprehensive test data for development/testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create',
        )
        parser.add_argument(
            '--resources',
            type=int,
            default=50,
            help='Number of academic resources to create',
        )
        parser.add_argument(
            '--events',
            type=int,
            default=10,
            help='Number of events to create',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_data()
        
        self.stdout.write(self.style.SUCCESS('🚀 Starting test data population...'))
        
        with transaction.atomic():
            # Create core data
            self.create_academic_categories()
            self.create_schemes()
            self.create_subjects()
            self.create_users(options['users'])
            self.create_academic_resources(options['resources'])
            self.create_events(options['events'])
            self.create_gallery_data()
            self.create_projects()
            self.create_placement_data()
            self.create_alumni_data()
            self.create_team_members()
        
        self.stdout.write(self.style.SUCCESS('✅ Test data population completed!'))

    def clear_data(self):
        """Clear existing test data"""
        self.stdout.write('🗑️  Clearing existing data...')
        
        # Clear in reverse dependency order
        AcademicResource.objects.all().delete()
        EventRegistration.objects.all().delete()
        Event.objects.all().delete()
        GalleryImage.objects.all().delete()
        GalleryAlbum.objects.all().delete()
        GalleryCategory.objects.all().delete()
        ProjectImage.objects.all().delete()
        TeamMember.objects.all().delete()
        Project.objects.all().delete()
        PlacedStudent.objects.all().delete()
        PlacementStatistics.objects.all().delete()
        PlacementDrive.objects.all().delete()
        Company.objects.all().delete()
        Alumni.objects.all().delete()
        AccountTeamMember.objects.all().delete()
        Subject.objects.all().delete()
        Scheme.objects.all().delete()
        
        # Keep admin user, delete others
        User.objects.exclude(is_superuser=True).delete()
        
        self.stdout.write(self.style.SUCCESS('✅ Data cleared!'))

    def create_academic_categories(self):
        """Create the 5 fixed academic categories"""
        categories_data = [
            {
                'name': 'Notes',
                'slug': 'notes',
                'category_type': 'notes',
                'description': 'Study notes and materials',
                'icon': 'fas fa-book',
                'display_order': 1
            },
            {
                'name': 'Textbooks',
                'slug': 'textbooks',
                'category_type': 'textbook',
                'description': 'Textbooks and reference materials',
                'icon': 'fas fa-graduation-cap',
                'display_order': 2
            },
            {
                'name': 'Previous Year Questions',
                'slug': 'pyq',
                'category_type': 'pyq',
                'description': 'Previous year question papers',
                'icon': 'fas fa-question-circle',
                'display_order': 3
            },
            {
                'name': 'Regulations',
                'slug': 'regulations',
                'category_type': 'regulations',
                'description': 'Academic regulations and rules',
                'icon': 'fas fa-gavel',
                'display_order': 4
            },
            {
                'name': 'Syllabus',
                'slug': 'syllabus',
                'category_type': 'syllabus',
                'description': 'Course syllabus and curriculum',
                'icon': 'fas fa-list-alt',
                'display_order': 5
            }
        ]
        
        for cat_data in categories_data:
            category, created = AcademicCategory.objects.get_or_create(
                category_type=cat_data['category_type'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'✅ Created category: {category.name}')

    def create_schemes(self):
        """Create academic schemes"""
        schemes_data = [
            {'name': 'S2021', 'year': 2021, 'description': 'Scheme 2021'},
            {'name': 'S2022', 'year': 2022, 'description': 'Scheme 2022'},
            {'name': 'S2023', 'year': 2023, 'description': 'Scheme 2023'},
        ]
        
        for scheme_data in schemes_data:
            scheme, created = Scheme.objects.get_or_create(
                year=scheme_data['year'],
                defaults=scheme_data
            )
            if created:
                self.stdout.write(f'✅ Created scheme: {scheme.name}')

    def create_subjects(self):
        """Create subjects for each scheme"""
        subjects_data = [
            # S2021 subjects
            {'name': 'Digital Electronics', 'code': 'DE101', 'semester': 3, 'credits': 4},
            {'name': 'Analog Electronics', 'code': 'AE101', 'semester': 3, 'credits': 4},
            {'name': 'Electromagnetic Theory', 'code': 'EM101', 'semester': 4, 'credits': 4},
            {'name': 'Control Systems', 'code': 'CS101', 'semester': 5, 'credits': 4},
            {'name': 'Power Electronics', 'code': 'PE101', 'semester': 6, 'credits': 4},
            
            # S2022 subjects
            {'name': 'Microprocessors', 'code': 'MP201', 'semester': 4, 'credits': 4},
            {'name': 'Communication Systems', 'code': 'CM201', 'semester': 5, 'credits': 4},
            {'name': 'VLSI Design', 'code': 'VL201', 'semester': 6, 'credits': 4},
            
            # S2023 subjects
            {'name': 'Machine Learning', 'code': 'ML301', 'semester': 5, 'credits': 4},
            {'name': 'IoT Systems', 'code': 'IO301', 'semester': 6, 'credits': 4},
        ]
        
        schemes = list(Scheme.objects.all())
        for i, subject_data in enumerate(subjects_data):
            scheme = schemes[i % len(schemes)]
            subject, created = Subject.objects.get_or_create(
                code=subject_data['code'],
                scheme=scheme,
                defaults=subject_data
            )
            if created:
                self.stdout.write(f'✅ Created subject: {subject.name} ({subject.code})')

    def create_users(self, count):
        """Create test users with different groups"""
        from django.contrib.auth.models import Group
        
        # Create groups if they don't exist
        groups_data = [
            'Faculty Coordinators',
            'Events Heads', 
            'Placement Coordinators',
            'Alumni Heads',
            'Tech Heads'
        ]
        
        groups = {}
        for group_name in groups_data:
            group, created = Group.objects.get_or_create(name=group_name)
            groups[group_name] = group
            if created:
                self.stdout.write(f'✅ Created group: {group_name}')
        
        for i in range(count):
            username = f'test_user_{i+1}'
            email = f'test{i+1}@example.com'
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'Test{i+1}',
                    'last_name': f'User{i+1}',
                    'is_staff': True,
                    'is_active': True
                }
            )
            
            if created:
                user.set_password('test123')
                user.save()
                
                # Assign group based on index
                group_names = list(groups.keys())
                group_name = group_names[i % len(group_names)]
                user.groups.add(groups[group_name])
                
                self.stdout.write(f'✅ Created user: {username} (Group: {group_name})')

    def create_academic_resources(self, count):
        """Create academic resources"""
        categories = list(AcademicCategory.objects.all())
        subjects = list(Subject.objects.all())
        users = list(User.objects.filter(is_staff=True))
        
        resource_titles = [
            'Introduction to Digital Electronics', 'Analog Circuit Design', 'EM Theory Notes',
            'Control Systems Fundamentals', 'Power Electronics Basics', 'Microprocessor Architecture',
            'Communication Systems Design', 'VLSI Design Principles', 'Machine Learning Basics',
            'IoT System Design', 'Advanced Electronics', 'Circuit Analysis', 'Signal Processing',
            'Digital Signal Processing', 'Embedded Systems', 'Computer Architecture',
            'Network Theory', 'Electromagnetic Fields', 'Antenna Theory', 'Satellite Communications'
        ]
        
        for i in range(count):
            category = random.choice(categories)
            subject = random.choice(subjects)
            user = random.choice(users)
            title = f"{random.choice(resource_titles)} - Part {i+1}"
            
            # Create resource without file (for testing)
            resource = AcademicResource.objects.create(
                title=title,
                description=f'Test description for {title}',
                category=category,
                subject=subject,
                uploaded_by=user,
                module_number=random.randint(1, 5),
                exam_type=random.choice(['internal', 'sem', 'other']) if category.category_type == 'pyq' else '',
                exam_year=random.randint(2020, 2024) if category.category_type == 'pyq' else None,
                author=f'Author {i+1}',
                is_approved=random.choice([True, False]),
                is_featured=random.choice([True, False]),
                download_count=random.randint(0, 100),
                view_count=random.randint(0, 500)
            )
            
            if i % 10 == 0:
                self.stdout.write(f'✅ Created {i+1} academic resources...')

    def create_events(self, count):
        """Create test events"""
        event_types = ['workshop', 'seminar', 'conference', 'hackathon', 'webinar']
        users = list(User.objects.filter(is_staff=True))
        
        for i in range(count):
            start_date = timezone.now() + timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(hours=random.randint(2, 8))
            
            event = Event.objects.create(
                title=f'Test Event {i+1}',
                description=f'Description for test event {i+1}',
                event_type=random.choice(event_types),
                status=random.choice(['draft', 'published']),
                start_date=start_date,
                end_date=end_date,
                location=f'Location {i+1}',
                venue=f'Venue {i+1}',
                registration_required=True,
                max_participants=random.randint(50, 200),
                registration_fee=random.choice([0, 100, 200, 500]),
                payment_required=random.choice([True, False]),
                contact_person=f'Contact Person {i+1}',
                contact_email=f'contact{i+1}@example.com',
                created_by=random.choice(users),
                is_active=True,
                is_featured=random.choice([True, False])
            )
            
            # Create some registrations
            for j in range(random.randint(0, 5)):
                EventRegistration.objects.create(
                    event=event,
                    name=f'Participant {j+1}',
                    email=f'participant{j+1}@example.com',
                    mobile_number=f'+91{random.randint(7000000000, 9999999999)}',
                    institution='Test University',
                    department='Electrical Engineering',
                    year_of_study=f'Year {random.randint(1, 4)}',
                    payment_status=random.choice(['pending', 'paid', 'exempted'])
                )
            
            self.stdout.write(f'✅ Created event: {event.title}')

    def create_gallery_data(self):
        """Create gallery categories and albums"""
        categories_data = [
            {'name': 'Events Photos', 'description': 'Photos from various events'},
            {'name': 'IV Photos', 'description': 'Industrial visit photos'},
            {'name': 'Tech Fest Photos', 'description': 'Technical festival photos'},
            {'name': 'Alumni Photos', 'description': 'Alumni meet photos'},
            {'name': 'Department Photos', 'description': 'Department activities'},
        ]
        
        for cat_data in categories_data:
            category, created = GalleryCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            
            if created:
                # Create albums for each category
                for i in range(random.randint(2, 4)):
                    album = GalleryAlbum.objects.create(
                        name=f'{category.name} Album {i+1}',
                        description=f'Album {i+1} for {category.name}',
                        category=category
                    )
                    
                    # Create some images (without actual files)
                    for j in range(random.randint(3, 8)):
                        GalleryImage.objects.create(
                            title=f'Image {j+1}',
                            description=f'Description for image {j+1}',
                            album=album,
                            uploaded_by=User.objects.filter(is_staff=True).first()
                        )
                
                self.stdout.write(f'✅ Created gallery category: {category.name}')

    def create_projects(self):
        """Create test projects"""
        project_categories = ['web', 'mobile', 'ml', 'iot', 'robotics', 'other']
        users = list(User.objects.filter(is_staff=True))
        
        project_titles = [
            'Smart Home Automation', 'IoT Weather Station', 'ML Image Classifier',
            'E-commerce Platform', 'Mobile Health App', 'Robot Arm Controller',
            'Blockchain Voting System', 'AI Chatbot', 'Smart Agriculture System',
            'Electric Vehicle Charging Station', 'Solar Power Monitor', 'Drone Controller'
        ]
        
        for i in range(15):
            project = Project.objects.create(
                title=f'{random.choice(project_titles)} - Version {i+1}',
                description=f'Description for project {i+1}',
                category=random.choice(project_categories),
                student_batch=f'{random.randint(2020, 2024)}-{random.randint(2024, 2028)}',
                github_url=f'https://github.com/test/project{i+1}',
                demo_url=f'https://project{i+1}.com',
                created_by=random.choice(users),
                is_featured=random.choice([True, False]),
                is_published=True
            )
            
            # Create team members
            for j in range(random.randint(1, 4)):
                TeamMember.objects.create(
                    project=project,
                    name=f'Team Member {j+1}',
                    role=f'Role {j+1}',
                    linkedin_url=f'https://linkedin.com/in/member{j+1}'
                )
            
            if i % 5 == 0:
                self.stdout.write(f'✅ Created {i+1} projects...')

    def create_placement_data(self):
        """Create placement test data"""
        # Create companies
        companies_data = [
            {'name': 'TechCorp', 'description': 'Technology company'},
            {'name': 'ElectroTech', 'description': 'Electronics company'},
            {'name': 'PowerSystems', 'description': 'Power systems company'},
            {'name': 'InnovateLabs', 'description': 'Innovation lab'},
            {'name': 'SmartGrid', 'description': 'Smart grid solutions'},
        ]
        
        for company_data in companies_data:
            company, created = Company.objects.get_or_create(
                name=company_data['name'],
                defaults=company_data
            )
            
            if created:
                # Create placement drives
                for i in range(random.randint(1, 3)):
                    drive = PlacementDrive.objects.create(
                        title=f'{company.name} Drive {i+1}',
                        description=f'Placement drive {i+1} for {company.name}',
                        company=company,
                        drive_date=timezone.now() + timedelta(days=random.randint(30, 90)),
                        package_range=f'{random.randint(3, 8)}-{random.randint(8, 15)} LPA',
                        eligibility_criteria='B.Tech in Electrical Engineering',
                        is_active=True
                    )
                
                # Create placed students
                for i in range(random.randint(2, 5)):
                    PlacedStudent.objects.create(
                        student_name=f'Student {i+1}',
                        student_email=f'student{i+1}@example.com',
                        roll_number=f'EE{random.randint(2019, 2023)}{random.randint(100, 999)}',
                        batch_year=random.randint(2020, 2024),
                        cgpa=round(random.uniform(7.0, 9.5), 2),
                        company=company,
                        job_title=f'Software Engineer {i+1}',
                        package_lpa=round(random.uniform(4.0, 12.0), 2),
                        work_location=f'Location {i+1}',
                        offer_date=timezone.now().date() - timedelta(days=random.randint(30, 365)),
                        is_verified=True,
                        is_active=True
                    )
                
                self.stdout.write(f'✅ Created company: {company.name}')

    def create_alumni_data(self):
        """Create alumni test data"""
        schemes = list(Scheme.objects.all())
        
        for i in range(20):
            scheme = random.choice(schemes)
            year_of_joining = scheme.year
            year_of_passout = year_of_joining + 4
            
            alumni, created = Alumni.objects.get_or_create(
                email=f'alumni{i+1}@example.com',
                defaults={
                    'full_name': f'Alumni {i+1}',
                    'phone_number': f'+91{random.randint(7000000000, 9999999999)}',
                    'student_id': f'EE{year_of_joining}{random.randint(100, 999)}',
                    'scheme': scheme.year,
                    'year_of_joining': year_of_joining,
                    'year_of_passout': year_of_passout,
                    'department': 'Electrical & Electronics Engineering',
                    'specialization': random.choice(['Power Systems', 'Control Systems', 'VLSI', 'Communication']),
                    'cgpa': round(random.uniform(7.0, 9.5), 2),
                    'employment_status': random.choice(['employed', 'self_employed', 'higher_studies']),
                    'job_title': f'Job Title {i+1}',
                    'current_company': f'Company {i+1}',
                    'current_location': f'Location {i+1}',
                    'linkedin_profile': f'https://linkedin.com/in/alumni{i+1}',
                    'is_verified': True,
                    'is_active': True
                }
            )
            
            if i % 5 == 0:
                self.stdout.write(f'✅ Created {i+1} alumni records...')

    def create_team_members(self):
        """Create team members for accounts app"""
        team_data = [
            {'name': 'John Doe', 'position': 'President', 'team_type': 'eesa'},
            {'name': 'Jane Smith', 'position': 'Vice President', 'team_type': 'eesa'},
            {'name': 'Bob Johnson', 'position': 'Secretary', 'team_type': 'eesa'},
            {'name': 'Alice Brown', 'position': 'Treasurer', 'team_type': 'eesa'},
            {'name': 'Charlie Wilson', 'position': 'Tech Lead', 'team_type': 'tech'},
            {'name': 'Diana Davis', 'position': 'Developer', 'team_type': 'tech'},
            {'name': 'Eve Miller', 'position': 'Designer', 'team_type': 'tech'},
        ]
        
        for member_data in team_data:
            member, created = AccountTeamMember.objects.get_or_create(
                name=member_data['name'],
                defaults={
                    **member_data,
                    'bio': f'Bio for {member_data["name"]}',
                    'email': f'{member_data["name"].lower().replace(" ", ".")}@example.com',
                    'is_active': True,
                    'order': random.randint(1, 10)
                }
            )
            
            if created:
                self.stdout.write(f'✅ Created team member: {member.name} ({member.position})') 
from django.core.management.base import BaseCommand
from django.db import transaction
from student.models import Region, Department, Course
from content.models import ContentCategory, Tag


class Command(BaseCommand):
    help = 'Setup initial data for the Examify application'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up initial data...'))
        
        with transaction.atomic():
            self.create_regions()
            self.create_departments()
            self.create_courses()
            self.create_content_categories()
            self.create_tags()
        
        self.stdout.write(self.style.SUCCESS('Initial data setup completed!'))

    def create_regions(self):
        """Create initial regions (Indian states)"""
        regions_data = [
            {'name': 'Andhra Pradesh', 'code': 'AP'},
            {'name': 'Arunachal Pradesh', 'code': 'AR'},
            {'name': 'Assam', 'code': 'AS'},
            {'name': 'Bihar', 'code': 'BR'},
            {'name': 'Chhattisgarh', 'code': 'CG'},
            {'name': 'Goa', 'code': 'GA'},
            {'name': 'Gujarat', 'code': 'GJ'},
            {'name': 'Haryana', 'code': 'HR'},
            {'name': 'Himachal Pradesh', 'code': 'HP'},
            {'name': 'Jharkhand', 'code': 'JH'},
            {'name': 'Karnataka', 'code': 'KA'},
            {'name': 'Kerala', 'code': 'KL'},
            {'name': 'Madhya Pradesh', 'code': 'MP'},
            {'name': 'Maharashtra', 'code': 'MH'},
            {'name': 'Manipur', 'code': 'MN'},
            {'name': 'Meghalaya', 'code': 'ML'},
            {'name': 'Mizoram', 'code': 'MZ'},
            {'name': 'Nagaland', 'code': 'NL'},
            {'name': 'Odisha', 'code': 'OR'},
            {'name': 'Punjab', 'code': 'PB'},
            {'name': 'Rajasthan', 'code': 'RJ'},
            {'name': 'Sikkim', 'code': 'SK'},
            {'name': 'Tamil Nadu', 'code': 'TN'},
            {'name': 'Telangana', 'code': 'TG'},
            {'name': 'Tripura', 'code': 'TR'},
            {'name': 'Uttar Pradesh', 'code': 'UP'},
            {'name': 'Uttarakhand', 'code': 'UK'},
            {'name': 'West Bengal', 'code': 'WB'},
            {'name': 'Delhi', 'code': 'DL'},
        ]
        
        for region_data in regions_data:
            region, created = Region.objects.get_or_create(
                code=region_data['code'],
                defaults=region_data
            )
            if created:
                self.stdout.write(f'Created region: {region.name}')

    def create_departments(self):
        """Create initial departments"""
        departments_data = [
            {'name': 'Computer Science Engineering', 'code': 'CSE'},
            {'name': 'Information Technology', 'code': 'IT'},
            {'name': 'Electronics and Communication Engineering', 'code': 'ECE'},
            {'name': 'Electrical Engineering', 'code': 'EE'},
            {'name': 'Mechanical Engineering', 'code': 'ME'},
            {'name': 'Civil Engineering', 'code': 'CE'},
            {'name': 'Chemical Engineering', 'code': 'CHE'},
            {'name': 'Aeronautical Engineering', 'code': 'AE'},
            {'name': 'Biotechnology', 'code': 'BT'},
            {'name': 'Mathematics', 'code': 'MATH'},
            {'name': 'Physics', 'code': 'PHY'},
            {'name': 'Chemistry', 'code': 'CHEM'},
            {'name': 'Biology', 'code': 'BIO'},
            {'name': 'Business Administration', 'code': 'MBA'},
            {'name': 'Commerce', 'code': 'COM'},
            {'name': 'Arts', 'code': 'ARTS'},
        ]
        
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults=dept_data
            )
            if created:
                self.stdout.write(f'Created department: {dept.name}')

    def create_courses(self):
        """Create initial courses"""
        # Get departments
        cse_dept = Department.objects.get(code='CSE')
        math_dept = Department.objects.get(code='MATH')
        phy_dept = Department.objects.get(code='PHY')
        
        courses_data = [
            # CSE Courses
            {'name': 'Programming Fundamentals', 'code': 'CS101', 'department': cse_dept, 'semester': 1, 'credits': 4},
            {'name': 'Data Structures', 'code': 'CS201', 'department': cse_dept, 'semester': 2, 'credits': 4},
            {'name': 'Algorithms', 'code': 'CS301', 'department': cse_dept, 'semester': 3, 'credits': 4},
            {'name': 'Database Management Systems', 'code': 'CS302', 'department': cse_dept, 'semester': 4, 'credits': 3},
            {'name': 'Operating Systems', 'code': 'CS401', 'department': cse_dept, 'semester': 5, 'credits': 4},
            {'name': 'Computer Networks', 'code': 'CS402', 'department': cse_dept, 'semester': 6, 'credits': 3},
            {'name': 'Software Engineering', 'code': 'CS501', 'department': cse_dept, 'semester': 7, 'credits': 3},
            {'name': 'Machine Learning', 'code': 'CS502', 'department': cse_dept, 'semester': 8, 'credits': 4},
            
            # Mathematics Courses
            {'name': 'Calculus I', 'code': 'MATH101', 'department': math_dept, 'semester': 1, 'credits': 4},
            {'name': 'Linear Algebra', 'code': 'MATH201', 'department': math_dept, 'semester': 2, 'credits': 3},
            {'name': 'Discrete Mathematics', 'code': 'MATH301', 'department': math_dept, 'semester': 3, 'credits': 3},
            {'name': 'Statistics', 'code': 'MATH401', 'department': math_dept, 'semester': 4, 'credits': 3},
            
            # Physics Courses
            {'name': 'Physics I', 'code': 'PHY101', 'department': phy_dept, 'semester': 1, 'credits': 4},
            {'name': 'Physics II', 'code': 'PHY201', 'department': phy_dept, 'semester': 2, 'credits': 4},
        ]
        
        for course_data in courses_data:
            course, created = Course.objects.get_or_create(
                code=course_data['code'],
                department=course_data['department'],
                defaults=course_data
            )
            if created:
                self.stdout.write(f'Created course: {course.name}')

    def create_content_categories(self):
        """Create initial content categories"""
        categories_data = [
            {'name': 'Study Materials', 'description': 'Comprehensive study materials and notes'},
            {'name': 'Past Papers', 'description': 'Previous year question papers'},
            {'name': 'Practice Questions', 'description': 'Practice questions for exam preparation'},
            {'name': 'Video Lectures', 'description': 'Educational video content'},
            {'name': 'Reference Books', 'description': 'Recommended reference books and materials'},
            {'name': 'Lab Manuals', 'description': 'Laboratory manuals and experiments'},
            {'name': 'Project Ideas', 'description': 'Project ideas and guidelines'},
            {'name': 'Syllabus', 'description': 'Course syllabus and curriculum'},
        ]
        
        for cat_data in categories_data:
            category, created = ContentCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

    def create_tags(self):
        """Create initial tags"""
        tags_data = [
            {'name': 'important', 'color': '#ff6b6b'},
            {'name': 'easy', 'color': '#51cf66'},
            {'name': 'medium', 'color': '#ffd43b'},
            {'name': 'hard', 'color': '#ff8787'},
            {'name': 'theory', 'color': '#74c0fc'},
            {'name': 'practical', 'color': '#ff922b'},
            {'name': 'numerical', 'color': '#845ef7'},
            {'name': 'conceptual', 'color': '#69db7c'},
            {'name': 'mcq', 'color': '#3bc9db'},
            {'name': 'subjective', 'color': '#f783ac'},
            {'name': 'formula', 'color': '#ffd43b'},
            {'name': 'example', 'color': '#51cf66'},
            {'name': 'revision', 'color': '#ff6b6b'},
            {'name': 'quick-read', 'color': '#74c0fc'},
        ]
        
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults=tag_data
            )
            if created:
                self.stdout.write(f'Created tag: {tag.name}')

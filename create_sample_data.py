from models import Subject, Chapter, db

def create_sample_data():
    print("Creating sample subjects and chapters...")

    # Create Subjects if they don't exist
    subjects = [
        {
            'name': 'Mathematics',
            'chapters': [
                {'name': 'Algebra', 'description': 'Basic algebraic concepts'},
                {'name': 'Geometry', 'description': 'Geometric principles and theorems'},
                {'name': 'Calculus', 'description': 'Differential and integral calculus'}
            ]
        },
        {
            'name': 'Physics',
            'chapters': [
                {'name': 'Mechanics', 'description': 'Classical mechanics and motion'},
                {'name': 'Electricity', 'description': 'Electric circuits and magnetism'},
                {'name': 'Optics', 'description': 'Light and optical phenomena'}
            ]
        },
        {
            'name': 'Chemistry',
            'chapters': [
                {'name': 'Organic', 'description': 'Organic compounds and reactions'},
                {'name': 'Inorganic', 'description': 'Inorganic chemistry principles'},
                {'name': 'Physical', 'description': 'Chemical physics and thermodynamics'}
            ]
        }
    ]

    for subject_data in subjects:
        subject_name = subject_data['name']
        existing_subject = Subject.query.filter_by(name=subject_name).first()
        
        if not existing_subject:
            subject = Subject(name=subject_name)
            db.session.add(subject)
            db.session.flush()  # To get the subject ID

            # Create chapters for this subject
            for chapter_data in subject_data['chapters']:
                chapter = Chapter(
                    name=chapter_data['name'],
                    description=chapter_data['description'],
                    subject_id=subject.id
                )
                db.session.add(chapter)

    try:
        db.session.commit()
        print("Sample data created successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample data: {e}")
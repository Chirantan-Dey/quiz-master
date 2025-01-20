from flask import render_template_string, render_template, Flask, request, jsonify
from flask_security import auth_required, current_user, roles_required
from flask_security import SQLAlchemySessionUserDatastore
from flask_security.utils import hash_password
from models import Subject, Chapter, Quiz, Questions
from sqlalchemy import or_
from datetime import datetime

def create_views(app: Flask, user_datastore: SQLAlchemySessionUserDatastore, db):
    # homepage
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            
            # Check if required fields are present
            required_fields = ['email', 'password', 'role', 'full_name', 'qualification', 'dob']
            if not data or not all(k in data for k in required_fields):
                return jsonify({'message': 'All fields (email, password, role, full name, qualification, and date of birth) are required'}), 400

            email = data.get('email')
            password = data.get('password')
            role = data.get('role')
            full_name = data.get('full_name')
            qualification = data.get('qualification')
            dob = data.get('dob')

            # Check if user already exists
            if user_datastore.find_user(email=email):
                return jsonify({'message': 'An account with this email already exists'}), 400

            # Validate role - only allow 'user' role for registration
            if role != 'user':
                return jsonify({'message': 'Invalid role. Only user registration is allowed'}), 400

            try:
                # Parse date of birth
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
                
                # Create user with 'user' role
                user = user_datastore.create_user(
                    email=email,
                    password=hash_password(password),
                    active=True,
                    roles=['user'],
                    full_name=full_name,
                    qualification=qualification,
                    dob=dob_date
                )
                db.session.commit()
                return jsonify({
                    'message': 'User account created successfully',
                    'user': {
                        'email': user.email,
                        'roles': [{'name': 'user'}]
                    }
                }), 201

            except ValueError as e:
                return jsonify({
                    'message': 'Invalid date format. Please use YYYY-MM-DD format.'
                }), 400
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Database error during user creation: {str(e)}")
                return jsonify({
                    'message': 'Failed to create account. Please try again later.'
                }), 500

        except Exception as e:
            app.logger.error(f"Registration error: {str(e)}")
            return jsonify({
                'message': 'An unexpected error occurred. Please try again later.'
            }), 500

    @app.route('/api/subjects')
    @auth_required('token', 'session')
    def get_subjects():
        search_query = request.args.get('search', '').lower()
        
        subjects = db.session.query(Subject).all()
        subject_list = []
        
        for subject in subjects:
            chapters = db.session.query(Chapter).filter(Chapter.subject_id == subject.id).all()
            chapter_list = []
            
            for chapter in chapters:
                total_questions = 0
                quizzes = db.session.query(Quiz).filter(Quiz.chapter_id == chapter.id).all()
                for quiz in quizzes:
                    question_count = db.session.query(Questions).filter(Questions.quiz_id == quiz.id).count()
                    total_questions += question_count

                if not search_query or \
                   search_query in chapter.name.lower() or \
                   (chapter.description and search_query in chapter.description.lower()):
                    chapter_list.append({
                        'id': chapter.id,
                        'name': chapter.name,
                        'description': chapter.description,
                        'question_count': total_questions
                    })
            
            if chapter_list or not search_query or search_query in subject.name.lower():
                subject_list.append({ 'name': subject.name, 'chapters': chapter_list })
                
        return jsonify(subject_list)

    @app.route('/api/quizzes')
    @auth_required('token', 'session')
    def get_quizzes():
        search_query = request.args.get('search', '').lower()
        
        quizzes = db.session.query(Quiz)
        
        if search_query:
            quizzes = quizzes.filter(
                or_(
                    Quiz.name.ilike(f'%{search_query}%'),
                    Quiz.remarks.ilike(f'%{search_query}%')
                )
            )
            
        quizzes = quizzes.all()
        quiz_list = []
        
        for quiz in quizzes:
            questions = db.session.query(Questions).filter(Questions.quiz_id == quiz.id).all()
            question_list = []
            for question in questions:
                question_list.append({
                    'id': question.id,
                    'question_statement': question.question_statement,
                    'option1': question.option1,
                    'option2': question.option2,
                    'correct_answer': question.correct_answer
                })
            quiz_list.append({
                'id': quiz.id,
                'name': quiz.name,
                'chapter_id': quiz.chapter_id,
                'date_of_quiz': quiz.date_of_quiz.strftime('%Y-%m-%d') if quiz.date_of_quiz else None,
                'time_duration': quiz.time_duration,
                'remarks': quiz.remarks,
                'questions': question_list
            })
        return jsonify(quiz_list)
    
    @app.route('/api/chapters', methods=['POST'])
    @auth_required('token', 'session')
    def create_chapter():
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        subject_name = data.get('subject_name')

        if not name or not description or not subject_name:
            return jsonify({'message': 'Invalid input'}), 400
        
        subject = db.session.query(Subject).filter(Subject.name == subject_name).first()
        if not subject:
            return jsonify({'message': 'Subject not found'}), 404

        chapter = Chapter(name=name, description=description, subject_id=subject.id)
        db.session.add(chapter)
        db.session.commit()
        return jsonify({
            'message': 'Chapter created successfully',
            'chapter': {
                'id': chapter.id,
                'name': chapter.name,
                'description': chapter.description
            }
        }), 201

    @app.route('/api/chapters/<int:chapter_id>', methods=['PUT'])
    @auth_required('token', 'session')
    def update_chapter(chapter_id):
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')

        if not name or not description:
            return jsonify({'message': 'Invalid input'}), 400

        chapter = db.session.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return jsonify({'message': 'Chapter not found'}), 404

        chapter.name = name
        chapter.description = description
        db.session.commit()
        return jsonify({
            'message': 'Chapter updated successfully',
            'chapter': {
                'id': chapter.id,
                'name': chapter.name,
                'description': chapter.description
            }
        })

    @app.route('/api/chapters/<int:chapter_id>', methods=['DELETE'])
    @auth_required('token', 'session')
    def delete_chapter(chapter_id):
        chapter = db.session.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return jsonify({'message': 'Chapter not found'}), 404
        
        db.session.delete(chapter)
        db.session.commit()
        return jsonify({'message': 'Chapter deleted successfully'})
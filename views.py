from flask import render_template_string, render_template, Flask, request, jsonify
from flask_security import auth_required, current_user, roles_required
from flask_security import SQLAlchemySessionUserDatastore
from flask_security.utils import hash_password
from models import Subject, Chapter, Quiz, Questions, Scores
from extensions import cache
import charts
import os
from sqlalchemy import or_
from datetime import datetime

def create_views(app: Flask, user_datastore: SQLAlchemySessionUserDatastore, db):
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            required_fields = ['email', 'password', 'role', 'full_name', 'qualification', 'dob']
            if not data or not all(k in data for k in required_fields):
                return jsonify({'message': 'All fields (email, password, role, full name, qualification, and date of birth) are required'}), 400

            email = data.get('email')
            password = data.get('password')
            role = data.get('role')
            full_name = data.get('full_name')
            qualification = data.get('qualification')
            dob = data.get('dob')

            if user_datastore.find_user(email=email):
                return jsonify({'message': 'An account with this email already exists'}), 400

            if role != 'user':
                return jsonify({'message': 'Invalid role. Only user registration is allowed'}), 400

            try:
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
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
            except ValueError:
                return jsonify({'message': 'Invalid date format. Please use YYYY-MM-DD format.'}), 400
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Database error during user creation: {str(e)}")
                return jsonify({'message': 'Failed to create account. Please try again later.'}), 500
        except Exception as e:
            app.logger.error(f"Registration error: {str(e)}")
            return jsonify({'message': 'An unexpected error occurred. Please try again later.'}), 500

    @app.route('/api/subjects')
    @auth_required('token', 'session')
    @cache.memoize(timeout=1)
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
    @cache.memoize(timeout=1)  
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
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['name', 'description', 'subject_name']
            if not all(field in data for field in required_fields):
                return jsonify({'message': 'Missing required fields'}), 400

            name = data.get('name').strip()
            description = data.get('description').strip()
            subject_name = data.get('subject_name')

            # Basic validation
            if not name.strip():
                return jsonify({'message': 'Chapter name is required'}), 400
            if not description.strip():
                return jsonify({'message': 'Description is required'}), 400

            # Validate subject exists
            subject = db.session.query(Subject).filter(Subject.name == subject_name).first()
            if not subject:
                return jsonify({'message': 'Subject not found'}), 404

            # Check for duplicate chapter names in the same subject
            existing_chapter = db.session.query(Chapter).filter(
                Chapter.subject_id == subject.id,
                Chapter.name == name
            ).first()
            if existing_chapter:
                return jsonify({'message': 'A chapter with this name already exists in the subject'}), 400

            # Create and save chapter
            chapter = Chapter(
                name=name,
                description=description,
                subject_id=subject.id
            )
            db.session.add(chapter)
            db.session.commit()
            
            # Invalidate subject cache after adding new chapter
            cache.delete_memoized(get_subjects)
            
            return jsonify({
                'message': 'Chapter created successfully',
                'chapter': {
                    'id': chapter.id,
                    'name': chapter.name,
                    'description': chapter.description
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating chapter: {str(e)}")
            return jsonify({'message': 'Failed to create chapter'}), 500

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
        
        # Invalidate subject cache after updating chapter
        cache.delete_memoized(get_subjects)
        
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
        
        # Invalidate subject cache after deleting chapter
        cache.delete_memoized(get_subjects)
        
        return jsonify({'message': 'Chapter deleted successfully'})

    @app.route('/api/charts/admin')
    @auth_required('token', 'session')
    @roles_required('admin')
    @cache.memoize(timeout=1)  
    def get_admin_charts():
        try:
            # Clean up old charts first
            charts.cleanup_charts()
            
            scores_chart = charts.generate_admin_subject_scores()
            if not scores_chart:
                return jsonify({'message': 'No score data available'}), 404
                
            attempts_chart = charts.generate_admin_subject_attempts()
            if not attempts_chart:
                return jsonify({'message': 'No attempt data available'}), 404
            
            return jsonify({
                'scores_chart': f'/static/charts/admin/{scores_chart}',
                'attempts_chart': f'/static/charts/admin/{attempts_chart}'
            })
        except Exception as e:
            app.logger.error(f"Error generating admin charts: {str(e)}")
            return jsonify({'message': 'Error generating charts'}), 500

    @app.route('/api/charts/user')
    @auth_required('token', 'session')
    @cache.memoize(timeout=1)  
    def get_user_charts():
        try:
            # Clean up old charts first
            charts.cleanup_charts()
            
            questions_chart = charts.generate_user_subject_questions()
            attempts_chart = charts.generate_user_subject_attempts(current_user.id)
            
            if not questions_chart:
                return jsonify({'message': 'No questions data available'}), 404
            if not attempts_chart:
                return jsonify({'message': 'No quiz attempts found'}), 404
            
            return jsonify({
                'questions_chart': f'/static/charts/user/{questions_chart}',
                'attempts_chart': f'/static/charts/user/{attempts_chart}'
            })
        except Exception as e:
            app.logger.error(f"Error generating user charts: {str(e)}")
            return jsonify({'message': 'Error generating charts'}), 500

    @app.route('/api/quizzes', methods=['POST'])
    @auth_required('token', 'session')
    def create_quiz():
        try:
            data = request.get_json()
            required_fields = ['name', 'chapter_id', 'date_of_quiz', 'time_duration']
            if not all(field in data for field in required_fields):
                return jsonify({'message': 'Missing required fields'}), 400
            
            # Basic validation
            if not data['name'].strip():
                return jsonify({'message': 'Quiz name is required'}), 400
                
            if not isinstance(data['chapter_id'], (int, float)):
                return jsonify({'message': 'Invalid chapter ID'}), 400
                
            if not isinstance(data['time_duration'], (int, float)) or float(data['time_duration']) <= 0:
                return jsonify({'message': 'Duration must be a positive number'}), 400
            
            try:
                date_of_quiz = datetime.strptime(data['date_of_quiz'][:10], '%Y-%m-%d').date()
                if date_of_quiz < datetime.now().date():
                    return jsonify({'message': 'Quiz date cannot be in the past'}), 400
            except (ValueError, TypeError):
                return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
            
            # Verify chapter exists
            chapter = db.session.query(Chapter).get(data['chapter_id'])
            if not chapter:
                return jsonify({'message': 'Chapter not found'}), 404
            
            quiz = Quiz(
                name=data['name'],
                chapter_id=data['chapter_id'],
                date_of_quiz=date_of_quiz,
                time_duration=data['time_duration'],
                remarks=data.get('remarks', '')
            )
            
            db.session.add(quiz)
            db.session.commit()
            
            # Invalidate quiz cache
            cache.delete_memoized(get_quizzes)
            
            return jsonify({
                'message': 'Quiz created successfully',
                'quiz': {
                    'id': quiz.id,
                    'name': quiz.name,
                    'chapter_id': quiz.chapter_id,
                    'date_of_quiz': quiz.date_of_quiz.strftime('%Y-%m-%d'),
                    'time_duration': quiz.time_duration,
                    'remarks': quiz.remarks
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating quiz: {str(e)}")
            return jsonify({'message': 'Failed to create quiz'}), 500
            
    @app.route('/api/questions', methods=['POST'])
    @auth_required('token', 'session')
    def create_question():
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['question_statement', 'option1', 'option2', 'correct_answer', 'quiz_id']
            if not all(field in data for field in required_fields):
                return jsonify({'message': 'Missing required fields'}), 400

            # Basic validation
            if not data['question_statement'].strip():
                return jsonify({'message': 'Question statement is required'}), 400
            if not data['option1'].strip():
                return jsonify({'message': 'Option 1 is required'}), 400
            if not data['option2'].strip():
                return jsonify({'message': 'Option 2 is required'}), 400
            
            # Validate quiz ID format
            if not isinstance(data['quiz_id'], (int, float)):
                return jsonify({'message': 'Invalid quiz ID'}), 400

            # Validate correct answer matches one of the options
            if data['correct_answer'] not in [data['option1'], data['option2']]:
                return jsonify({'message': 'Correct answer must match one of the options'}), 400

            # Validate quiz exists
            quiz = db.session.query(Quiz).get(data['quiz_id'])
            if not quiz:
                return jsonify({'message': 'Quiz not found'}), 404

            question = Questions(
                quiz_id=data['quiz_id'],
                question_statement=data['question_statement'].strip(),
                option1=data['option1'].strip(),
                option2=data['option2'].strip(),
                correct_answer=data['correct_answer']
            )
            
            db.session.add(question)
            db.session.commit()
            
            # Invalidate quiz cache
            cache.delete_memoized(get_quizzes)
            
            return jsonify({
                'message': 'Question created successfully',
                'question': {
                    'id': question.id,
                    'quiz_id': question.quiz_id,
                    'question_statement': question.question_statement,
                    'option1': question.option1,
                    'option2': question.option2,
                    'correct_answer': question.correct_answer
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating question: {str(e)}")
            return jsonify({'message': 'Failed to create question'}), 500

    @app.route('/api/questions/<int:question_id>', methods=['PUT'])
    @auth_required('token', 'session')
    def update_question(question_id):
        try:
            data = request.get_json()
            question = db.session.query(Questions).filter(Questions.id == question_id).first()
            
            if not question:
                return jsonify({'message': 'Question not found'}), 404
                # Validate required fields and content
                required_fields = ['question_statement', 'option1', 'option2', 'correct_answer']
                if not all(field in data for field in required_fields):
                    return jsonify({'message': 'Missing required fields'}), 400
    
                # Validate question statement length (10-500 characters)
                if len(data['question_statement'].strip()) < 10:
                    return jsonify({'message': 'Question statement must be at least 10 characters'}), 400
                if len(data['question_statement']) > 500:
                    return jsonify({'message': 'Question statement must be less than 500 characters'}), 400
    
                # Validate options (1-200 characters each)
                if not data['option1'].strip() or len(data['option1']) > 200:
                    return jsonify({'message': 'Option 1 must be between 1 and 200 characters'}), 400
                if not data['option2'].strip() or len(data['option2']) > 200:
                    return jsonify({'message': 'Option 2 must be between 1 and 200 characters'}), 400
    
                # Validate correct answer matches one of the options
                if data['correct_answer'] not in [data['option1'], data['option2']]:
                    return jsonify({'message': 'Correct answer must match one of the options'}), 400
    
                question.question_statement = data['question_statement'].strip()
                question.option1 = data['option1'].strip()
                question.option2 = data['option2'].strip()
                question.correct_answer = data['correct_answer']
            question.correct_answer = data['correct_answer']
            
            db.session.commit()
            
            # Invalidate quiz cache
            cache.delete_memoized(get_quizzes)
            
            return jsonify({
                'message': 'Question updated successfully',
                'question': {
                    'id': question.id,
                    'question_statement': question.question_statement,
                    'option1': question.option1,
                    'option2': question.option2,
                    'correct_answer': question.correct_answer
                }
            })
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating question: {str(e)}")
            return jsonify({'message': 'Failed to update question'}), 500

    @app.route('/api/questions/<int:question_id>', methods=['DELETE'])
    @auth_required('token', 'session')
    def delete_question(question_id):
        try:
            question = db.session.query(Questions).filter(Questions.id == question_id).first()
            
            if not question:
                return jsonify({'message': 'Question not found'}), 404
            
            db.session.delete(question)
            db.session.commit()
            
            # Invalidate quiz cache
            cache.delete_memoized(get_quizzes)
            
            return jsonify({'message': 'Question deleted successfully'})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error deleting question: {str(e)}")
            return jsonify({'message': 'Failed to delete question'}), 500
            
    @app.route('/api/scores', methods=['POST'])
    @auth_required('token', 'session')
    def submit_score():
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['quiz_id', 'time_stamp_of_attempt', 'total_scored']
            if not all(field in data for field in required_fields):
                return jsonify({'message': 'Missing required fields'}), 400
                
            # Validate data types
            if not isinstance(data['quiz_id'], (int, float)):
                return jsonify({'message': 'quiz_id must be a number'}), 400
            
            if not isinstance(data['total_scored'], (int, float)):
                return jsonify({'message': 'total_scored must be a number'}), 400
                
            # Parse and validate timestamp
            try:
                timestamp = datetime.fromisoformat(data['time_stamp_of_attempt'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'message': 'Invalid timestamp format'}), 400
            
            # Validate quiz exists
            quiz = db.session.query(Quiz).filter(Quiz.id == data['quiz_id']).first()
            if not quiz:
                return jsonify({'message': 'Quiz not found'}), 404
            
            score = Scores(
                quiz_id=data['quiz_id'],
                user_id=current_user.id,
                time_stamp_of_attempt=timestamp,
                total_scored=data['total_scored']
            )
            
            db.session.add(score)
            db.session.commit()
            
            return jsonify({
                'message': 'Score submitted successfully',
                'score': {
                    'id': score.id,
                    'quiz_id': score.quiz_id,
                    'user_id': score.user_id,
                    'time_stamp_of_attempt': score.time_stamp_of_attempt.isoformat(),
                    'total_scored': score.total_scored
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error submitting score: {str(e)}")
            return jsonify({'message': 'Failed to submit score'}), 500
from flask_restful import Resource, Api, reqparse, marshal_with, fields
from models import Subject, Quiz, Questions, Scores, Chapter, db
from flask_security import auth_required, current_user, roles_required
from datetime import datetime
from extensions import cache
from workers import generate_user_export
from flask import current_app

parser = reqparse.RequestParser()
api = Api(prefix='/api')

subject_fields = {
    'id': fields.Integer,
    'name': fields.String
}

quiz_fields = {
    'id': fields.Integer,
    'chapter_id': fields.Integer,
    'date_of_quiz': fields.String,
    'time_duration': fields.Integer,
    'remarks': fields.String,
    'name': fields.String,
}

question_fields = {
    'id': fields.Integer,
    'quiz_id': fields.Integer,
    'question_statement': fields.String,
    'option1': fields.String,
    'option2': fields.String,
    'correct_answer': fields.String
}

score_fields = {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'quiz_id': fields.Integer,
    'time_stamp_of_attempt': fields.DateTime,
    'total_scored': fields.Integer
}

chapter_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String
}

class SubjectResource(Resource):
    @auth_required('token', 'session')
    @marshal_with(subject_fields)
    @cache.cached(timeout=1, key_prefix='subject_list')
    def get(self):
        all_subjects = Subject.query.all()
        result = []
        for subject in all_subjects:
            chapters = Chapter.query.filter_by(subject_id=subject.id).all()
            subject_data = {
                'id': subject.id,
                'name': subject.name,
                'chapters': [{
                    'id': chapter.id,
                    'name': chapter.name,
                    'description': chapter.description
                } for chapter in chapters]
            }
            result.append(subject_data)
        return result

    @auth_required('token', 'session')
    @marshal_with(subject_fields)
    def post(self):
        parser.add_argument('name', type=str, help="Name should be string", required=True)
        args = parser.parse_args()
        subject = Subject(name=args['name'])
        db.session.add(subject)
        db.session.commit()
        cache.delete('subject_list')
        return subject

    @auth_required('token', 'session')
    @marshal_with(subject_fields)
    def put(self, id):
        parser.add_argument('name', type=str, help="Name should be string", required=True)
        args = parser.parse_args()
        subject = Subject.query.get(id)
        if not subject:
            return {"message": "subject not found"}, 404
        subject.name = args['name']
        db.session.commit()
        cache.delete('subject_list')
        return subject

    @auth_required('token', 'session')
    @marshal_with(subject_fields)
    def delete(self, id):
        subject = Subject.query.get(id)
        if not subject:
            return {"message": "subject not found"}, 404
        db.session.delete(subject)
        db.session.commit()
        cache.delete('subject_list')
        return {"message": "subject deleted"}

class QuizResource(Resource):
    @auth_required('token', 'session')
    @marshal_with(quiz_fields)
    @cache.cached(timeout=1, key_prefix='quiz_list')
    def get(self):
        return Quiz.query.all()

    @auth_required('token', 'session')
    @marshal_with(quiz_fields)
    def post(self):
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('chapter_id', type=int, required=True)
        parser.add_argument('date_of_quiz', type=str, required=True)
        parser.add_argument('time_duration', type=str, required=True)  # Changed to str to match frontend
        parser.add_argument('remarks', type=str, required=False)
        args = parser.parse_args()
        
        # Convert time_duration to int and validate
        try:
            time_duration = int(args.get('time_duration'))
            if time_duration <= 0:
                return {"message": "Duration must be a positive number"}, 400
        except (ValueError, TypeError):
            return {"message": "Duration must be a valid number"}, 400
            
        date_of_quiz_str = args.get('date_of_quiz')
        try:
            # Handle ISO format date string from frontend
            date_of_quiz = datetime.strptime(date_of_quiz_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return {"message": "Invalid date format"}, 400

        quiz = Quiz(
            name=args.get('name'),
            chapter_id=args.get('chapter_id'),
            date_of_quiz=date_of_quiz,
            time_duration=time_duration,  # Use converted integer
            remarks=args.get('remarks')
        )
        db.session.add(quiz)
        db.session.commit()
        cache.delete('quiz_list')
        return quiz

class QuestionResource(Resource):
    @auth_required('token', 'session')
    @marshal_with(question_fields)
    @cache.cached(timeout=1)
    def get(self):
        parser.add_argument('quiz_id', type=int, location='args', required=False)
        args = parser.parse_args()
        
        if args.get('quiz_id'):
            return Questions.query.filter_by(quiz_id=args['quiz_id']).all()
        return Questions.query.all()

    @auth_required('token', 'session')
    @marshal_with(question_fields)
    def post(self):
        parser.add_argument('quiz_id', type=int, required=True)
        parser.add_argument('question_statement', type=str, required=True)
        parser.add_argument('option1', type=str, required=True)
        parser.add_argument('option2', type=str, required=True)
        parser.add_argument('correct_answer', type=str, required=True)
        args = parser.parse_args()

        question = Questions(**args)
        db.session.add(question)
        db.session.commit()
        cache.delete_memoized(self.get)
        return question

class ScoreResource(Resource):
    @auth_required('token', 'session')
    @marshal_with(score_fields)
    @cache.memoize(timeout=1)
    def get(self):
        user_id = current_user.id
        return Scores.query.filter_by(user_id=user_id).all()

    @auth_required('token', 'session')
    @marshal_with(score_fields)
    def post(self):
        parser.add_argument('quiz_id', type=int, required=True)
        parser.add_argument('total_scored', type=int, required=True)
        parser.add_argument('time_stamp_of_attempt', type=str, required=True)
        args = parser.parse_args()
        
        try:
            time_stamp = datetime.fromisoformat(args['time_stamp_of_attempt'].replace('Z', '+00:00'))
        except ValueError:
            return {"message": "Invalid timestamp format"}, 400
        
        score = Scores(
            quiz_id=args['quiz_id'],
            user_id=current_user.id,
            time_stamp_of_attempt=time_stamp,
            total_scored=args['total_scored']
        )
        db.session.add(score)
        db.session.commit()
        cache.delete_memoized(self.get)
        return score

class ChapterResource(Resource):
    @auth_required('token', 'session')
    @marshal_with(chapter_fields)
    @cache.cached(timeout=1, key_prefix='chapter_list')
    def get(self):
        return Chapter.query.all()

    @auth_required('token', 'session')
    @marshal_with(chapter_fields)
    def post(self):
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('subject_name', type=str, required=True)
        parser.add_argument('description', type=str, required=False)
        args = parser.parse_args()

        subject = Subject.query.filter_by(name=args['subject_name']).first()
        if not subject:
            return {"message": "Subject not found"}, 404

        chapter = Chapter(
            name=args['name'],
            subject_id=subject.id,
            description=args.get('description')
        )
        db.session.add(chapter)
        db.session.commit()
        cache.delete('chapter_list')
        return chapter

    @auth_required('token', 'session')
    def delete(self, id):
        chapter = Chapter.query.get(id)
        if not chapter:
            return {"message": "Chapter not found"}, 404
        try:
            db.session.delete(chapter)
            db.session.commit()
            cache.delete('chapter_list')
            return {"message": "Chapter deleted"}, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Delete chapter error: {str(e)}")
            return {"message": "Failed to delete chapter"}, 500

class ExportResource(Resource):
    @auth_required('token', 'session')
    @roles_required('admin')
    def post(self):
        """Start a background task to export user data"""
        task = None
        try:
            task = generate_user_export.delay(current_user.email)            
            cache.delete('export_task')            
            return {
                'message': 'Export started. You will receive an email when ready.',
                'task_id': str(task.id) if task else None
            }, 202
        except Exception as e:
            current_app.logger.error(f"Export error: {str(e)}")
            return {
                'message': f'Export failed: {str(e)}'
            }, 500

api.add_resource(SubjectResource, '/subjects', '/subjects/<int:id>')
api.add_resource(QuizResource, '/quizzes', '/quizzes/<int:id>')
api.add_resource(QuestionResource, '/questions', '/questions/<int:id>')
api.add_resource(ScoreResource, '/scores', '/scores/<int:id>')
api.add_resource(ChapterResource, '/chapters', '/chapters/<int:id>')
api.add_resource(ExportResource, '/export/users')

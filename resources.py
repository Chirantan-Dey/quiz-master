from flask_restful import Resource, Api, reqparse, marshal_with, fields
from models import Subject, Quiz, Questions, Scores, Chapter, db
<<<<<<< Updated upstream
from flask_security import auth_required
from datetime import datetime

parser = reqparse.RequestParser()


api = Api(prefix='/api')

=======
from flask_security import auth_required, current_user
from datetime import datetime
from extensions import cache
from flask import current_app, request
from flask_wtf.csrf import generate_csrf

api = Api(prefix='/api')

# Request parsers with CSRF token handling
def create_parser():
    parser = reqparse.RequestParser()
    return parser

parser = create_parser()

# Resource fields definitions
>>>>>>> Stashed changes
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
    'option1': fields.String,
    'option2': fields.String
}

question_fields = {
    'id': fields.Integer,
    'quiz_id': fields.Integer,
    'text': fields.String,
    'correct_answer': fields.String,
    'option1': fields.String,
    'option2': fields.String
}

score_fields = {
    'id': fields.Integer,
    'student_id': fields.Integer,
    'quiz_id': fields.Integer,
    'score': fields.Integer
}

chapter_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String
}

class SubjectResource(Resource):
    @auth_required('token', 'session')
    @marshal_with(subject_fields)
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
        subject = Subject(name=args['name'], description=None)
        db.session.add(subject)
        db.session.commit()
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
        subject.description = None
        db.session.commit()
        return subject

    @auth_required('token', 'session')
    @marshal_with(subject_fields)
    def delete(self, id):
        subject = Subject.query.get(id)
        if not subject:
            return {"message": "subject not found"}, 404
        db.session.delete(subject)
        db.session.commit()
        return {"message": "subject deleted"}

class QuizResource(Resource):
    @auth_required('token', 'session')
    @marshal_with(quiz_fields)
    def get(self):
        all_quizzes = Quiz.query.all()
        return all_quizzes

    @auth_required('token', 'session')
    @marshal_with(quiz_fields)
    def post(self):
        parser.add_argument('name', type=str, help="Name should be string", required=True)
        parser.add_argument('chapter_id', type=int, help="Chapter ID should be integer", required=True)
        parser.add_argument('date_of_quiz', type=str, help="Date of quiz should be string", required=False)
        parser.add_argument('time_duration', type=int, help="Time duration should be integer", required=False)
        parser.add_argument('remarks', type=str, help="Remarks should be string", required=False)
        parser.add_argument('option1', type=str, help="Option 1 should be string", required=False)
        parser.add_argument('option2', type=str, help="Option 2 should be string", required=False)
        args = parser.parse_args()
        date_of_quiz_str = args.get('date_of_quiz')
        if date_of_quiz_str:
            try:
                date_of_quiz = datetime.strptime(date_of_quiz_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                return {"message": "Invalid date format. Please use YYYY-MM-DDTHH:MM:SS.ffffffZ"}, 400
        else:
            date_of_quiz = None

        quiz = Quiz(
            name=args.get('name'),
            chapter_id=args.get('chapter_id'),
            date_of_quiz=date_of_quiz,
            time_duration=args.get('time_duration'),
            remarks=args.get('remarks'),
            option1=args.get('option1'),
            option2=args.get('option2')
        )
        db.session.add(quiz)
        db.session.commit()
        return quiz
    
    @auth_required('token', 'session')
    @marshal_with(quiz_fields)
    def put(self, id):
        parser.add_argument('name', type=str, help="Name should be string", required=True)
        parser.add_argument('chapter_id', type=int, help="Chapter ID should be integer", required=True)
        parser.add_argument('date_of_quiz', type=str, help="Date of quiz should be string", required=False)
        parser.add_argument('time_duration', type=int, help="Time duration should be integer", required=False)
        parser.add_argument('remarks', type=str, help="Remarks should be string", required=False)
        parser.add_argument('option1', type=str, help="Option 1 should be string", required=False)
        parser.add_argument('option2', type=str, help="Option 2 should be string", required=False)
        args = parser.parse_args()
        quiz = Quiz.query.get(id)
        if not quiz:
            return {"message": "quiz not found"}, 404
        quiz.name = args.get('name')
        quiz.chapter_id = args.get('chapter_id')

        date_of_quiz_str = args.get('date_of_quiz')
        if date_of_quiz_str:
            try:
                date_of_quiz = datetime.strptime(date_of_quiz_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                return {"message": "Invalid date format. Please use YYYY-MM-DDTHH:MM:SS.ffffffZ"}, 400
        else:
            date_of_quiz = None
        quiz.date_of_quiz = date_of_quiz

        quiz.time_duration = args.get('time_duration')
        quiz.remarks = args.get('remarks')
        quiz.option1 = args.get('option1')
        quiz.option2 = args.get('option2')
        db.session.commit()
        return {"message": "quiz updated"}

    @auth_required('token', 'session')
    @marshal_with(quiz_fields)
    def delete(self, id):
        quiz = Quiz.query.get(id)
        if not quiz:
            return {"message": "quiz not found"}, 404
        db.session.delete(quiz)
        db.session.commit()
        return {"message": "quiz deleted"}

class QuestionResource(Resource):
    @auth_required('token', 'session')
    @marshal_with(question_fields)
    def get(self):
        all_questions = Questions.query.all()
        return all_questions

    @auth_required('token', 'session')
    @marshal_with(question_fields)
    def post(self):
        parser.add_argument('quiz_id', type=int, help="Quiz ID should be integer", required=True)
        parser.add_argument('text', type=str, help="Text should be string", required=True)
        parser.add_argument('correct_answer', type=str, help="Correct answer should be string", required=True)
        parser.add_argument('option1', type=str, help="Option 1 should be string", required=True)
        parser.add_argument('option2', type=str, help="Option 2 should be string", required=True)
        args = parser.parse_args()
        question = Questions(**args)
        db.session.add(question)
        db.session.commit()
        return {"message": "question created"}
    
    @auth_required('token', 'session')
    @marshal_with(question_fields)
    def put(self, id):
        parser.add_argument('quiz_id', type=int, help="Quiz ID should be integer", required=True)
        parser.add_argument('text', type=str, help="Text should be string", required=True)
        parser.add_argument('correct_answer', type=str, help="Correct answer should be string", required=True)
        parser.add_argument('option1', type=str, help="Option 1 should be string", required=True)
        parser.add_argument('option2', type=str, help="Option 2 should be string", required=True)
        args = parser.parse_args()
        question = Questions.query.get(id)
        if not question:
            return {"message": "question not found"}, 404
        for key, value in args.items():
            setattr(question, key, value)
        db.session.commit()
        return {"message": "question updated"}

    @auth_required('token', 'session')
    @marshal_with(question_fields)
    def delete(self, id):
        question = Questions.query.get(id)
        if not question:
            return {"message": "question not found"}, 404
        db.session.delete(question)
        db.session.commit()
        return {"message": "question deleted"}

<<<<<<< Updated upstream
class ScoreResource(Resource):
    @auth_required('token', 'session')
    @marshal_with(score_fields)
    def get(self):
        all_scores = Scores.query.all()
        return all_scores

    @auth_required('token', 'session')
    @marshal_with(score_fields)
    def post(self):
        parser.add_argument('student_id', type=int, help="Student ID should be integer", required=True)
        parser.add_argument('score', type=int, help="Score should be integer", required=True)
        parser.add_argument('chapter_id', type=int, help="Chapter ID should be integer", required=True)
        args = parser.parse_args()
        score = Scores(**args)
        db.session.add(score)
        db.session.commit()
        return {"message": "score created"}
    
    @auth_required('token', 'session')
    @marshal_with(score_fields)
    def put(self, id):
        parser.add_argument('student_id', type=int, help="Student ID should be integer", required=True)
        parser.add_argument('score', type=int, help="Score should be integer", required=True)
        parser.add_argument('chapter_id', type=int, help="Chapter ID should be integer", required=True)
        args = parser.parse_args()
        score = Scores.query.get(id)
        if not score:
            return {"message": "score not found"}, 404
        for key, value in args.items():
            setattr(score, key, value)
        db.session.commit()
        return {"message": "score updated"}

    @auth_required('token', 'session')
    @marshal_with(score_fields)
    def delete(self, id):
        score = Scores.query.get(id)
        if not score:
            return {"message": "score not found"}, 404
        db.session.delete(score)
        db.session.commit()
        return {"message": "score deleted"}

class ChapterResource(Resource):
    @auth_required('token', 'session')
    @marshal_with(chapter_fields)
    def get(self):
        all_chapters = Chapter.query.all()
        return all_chapters

    @auth_required('token', 'session')
    @marshal_with(chapter_fields)
    def post(self):
        parser.add_argument('name', type=str, help="Name should be string", required=True)
        parser.add_argument('subject_name', type=str, help="Subject Name should be string", required=True)
        parser.add_argument('description', type=str, help="Description should be string", required=False)
        args = parser.parse_args()

        subject = Subject.query.filter_by(name=args['subject_name']).first()
        if not subject:
            return {"message": "Subject not found"}, 404

        chapter = Chapter(name=args['name'], subject_id=subject.id, description=args.get('description'))
        db.session.add(chapter)
        db.session.commit()
        return chapter
    
    @auth_required('token', 'session')
    @marshal_with(chapter_fields)
    def put(self, id):
        parser.add_argument('name', type=str, help="Name should be string", required=True)
        parser.add_argument('subject_name', type=str, help="Subject Name should be string", required=True)
        parser.add_argument('description', type=str, help="Description should be string", required=False)
        args = parser.parse_args()

        chapter = Chapter.query.get(id)
        if not chapter:
            return {"message": "chapter not found"}, 404
        
        subject = Subject.query.filter_by(name=args['subject_name']).first()
        if not subject:
            return {"message": "Subject not found"}, 404
        
        chapter.name = args['name']
        chapter.subject_id = subject.id
        if 'description' in args:
            chapter.description = args.get('description')
        db.session.commit()
        return chapter

    @auth_required('token', 'session')
    @marshal_with(chapter_fields)
    def delete(self, id):
        chapter = Chapter.query.get(id)
        if not chapter:
            return {"message": "chapter not found"}, 404
        db.session.delete(chapter)
        db.session.commit()
        return {"message": "chapter deleted"}

=======
>>>>>>> Stashed changes
api.add_resource(SubjectResource, '/subjects', '/subjects/<int:id>')
api.add_resource(QuizResource, '/quizzes', '/quizzes/<int:id>')
api.add_resource(QuestionResource, '/questions', '/questions/<int:id>')
<<<<<<< Updated upstream
api.add_resource(ScoreResource, '/scores', '/scores/<int:id>')
api.add_resource(ChapterResource, '/chapters', '/chapters/<int:id>')
=======
>>>>>>> Stashed changes

from flask_restful import Resource, Api, reqparse, marshal_with, fields
from models import Subject, Quiz, Questions, Scores, Chapter, db
from flask_security import auth_required

parser = reqparse.RequestParser()
parser.add_argument('name', type=str, help="Name should be string", required=True)
parser.add_argument('description', type=str, help="Description should be string")

parser.add_argument('subject_id', type=int, help="Subject ID should be integer", required=True)
parser.add_argument('title', type=str, help="Title should be string", required=True)

parser.add_argument('quiz_id', type=int, help="Quiz ID should be integer", required=True)
parser.add_argument('text', type=str, help="Text should be string", required=True)
parser.add_argument('correct_answer', type=str, help="Correct answer should be string", required=True)

parser.add_argument('student_id', type=int, help="Student ID should be integer", required=True)
parser.add_argument('score', type=int, help="Score should be integer", required=True)
parser.add_argument('chapter_id', type=int, help="Chapter ID should be integer", required=True)

api = Api(prefix='/api')

subject_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String
}

quiz_fields = {
    'id': fields.Integer,
    'subject_id': fields.Integer,
    'title': fields.String
}

question_fields = {
    'id': fields.Integer,
    'quiz_id': fields.Integer,
    'text': fields.String,
    'correct_answer': fields.String
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
        return all_subjects

    @auth_required('token', 'session')
    def post(self):
        args = parser.parse_args()
        subject = Subject(**args)
        db.session.add(subject)
        db.session.commit()
        return {"message": "subject created"}
    
    @auth_required('token', 'session')
    def put(self, id):
        args = parser.parse_args()
        subject = Subject.query.get(id)
        if not subject:
            return {"message": "subject not found"}, 404
        for key, value in args.items():
            setattr(subject, key, value)
        db.session.commit()
        return {"message": "subject updated"}

    @auth_required('token', 'session')
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
    def post(self):
        args = parser.parse_args()
        quiz = Quiz(**args)
        db.session.add(quiz)
        db.session.commit()
        return {"message": "quiz created"}
    
    @auth_required('token', 'session')
    def put(self, id):
        args = parser.parse_args()
        quiz = Quiz.query.get(id)
        if not quiz:
            return {"message": "quiz not found"}, 404
        for key, value in args.items():
            setattr(quiz, key, value)
        db.session.commit()
        return {"message": "quiz updated"}

    @auth_required('token', 'session')
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
    def post(self):
        args = parser.parse_args()
        question = Questions(**args)
        db.session.add(question)
        db.session.commit()
        return {"message": "question created"}
    
    @auth_required('token', 'session')
    def put(self, id):
        args = parser.parse_args()
        question = Questions.query.get(id)
        if not question:
            return {"message": "question not found"}, 404
        for key, value in args.items():
            setattr(question, key, value)
        db.session.commit()
        return {"message": "question updated"}

    @auth_required('token', 'session')
    def delete(self, id):
        question = Questions.query.get(id)
        if not question:
            return {"message": "question not found"}, 404
        db.session.delete(question)
        db.session.commit()
        return {"message": "question deleted"}

class ScoreResource(Resource):
    @auth_required('token', 'session')
    @marshal_with(score_fields)
    def get(self):
        all_scores = Scores.query.all()
        return all_scores

    @auth_required('token', 'session')
    def post(self):
        args = parser.parse_args()
        score = Scores(**args)
        db.session.add(score)
        db.session.commit()
        return {"message": "score created"}
    
    @auth_required('token', 'session')
    def put(self, id):
        args = parser.parse_args()
        score = Scores.query.get(id)
        if not score:
            return {"message": "score not found"}, 404
        for key, value in args.items():
            setattr(score, key, value)
        db.session.commit()
        return {"message": "score updated"}

    @auth_required('token', 'session')
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
    def post(self):
        args = parser.parse_args()
        chapter = Chapter(**args)
        db.session.add(chapter)
        db.session.commit()
        return {"message": "chapter created"}
    
    @auth_required('token', 'session')
    def put(self, id):
        args = parser.parse_args()
        chapter = Chapter.query.get(id)
        if not chapter:
            return {"message": "chapter not found"}, 404
        for key, value in args.items():
            setattr(chapter, key, value)
        db.session.commit()
        return {"message": "chapter updated"}

    @auth_required('token', 'session')
    def delete(self, id):
        chapter = Chapter.query.get(id)
        if not chapter:
            return {"message": "chapter not found"}, 404
        db.session.delete(chapter)
        db.session.commit()
        return {"message": "chapter deleted"}

api.add_resource(SubjectResource, '/subjects', '/subjects/<int:id>')
api.add_resource(QuizResource, '/quizzes', '/quizzes/<int:id>')
api.add_resource(QuestionResource, '/questions', '/questions/<int:id>')
api.add_resource(ScoreResource, '/scores', '/scores/<int:id>')
api.add_resource(ChapterResource, '/chapters', '/chapters/<int:id>')

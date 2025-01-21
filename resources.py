from flask_restful import Resource, Api, reqparse, marshal_with, fields
from models import Subject, Quiz, Questions, Scores, Chapter, db
from flask_security import auth_required, current_user
from datetime import datetime

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
            remarks=args.get('remarks')
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
        parser.add_argument('quiz_id', type=int, location='args', required=False)
        args = parser.parse_args()
        
        if args.get('quiz_id'):
            questions = Questions.query.filter_by(quiz_id=args['quiz_id']).all()
        else:
            questions = Questions.query.all()
        return questions

    @auth_required('token', 'session')
    @marshal_with(question_fields)
    def post(self):
        question_parser = reqparse.RequestParser()
        question_parser.add_argument('quiz_id', type=int, help="Quiz ID should be integer", required=True)
        question_parser.add_argument('question_statement', type=str, help="Question statement should be string", required=True)
        question_parser.add_argument('option1', type=str, help="Option 1 should be string", required=True)
        question_parser.add_argument('option2', type=str, help="Option 2 should be string", required=True)
        question_parser.add_argument('correct_answer', type=str, help="Correct answer should be string", required=True)
        args = question_parser.parse_args()
        question = Questions(**args)
        db.session.add(question)
        db.session.commit()
        return {"message": "question created"}
    
    @auth_required('token', 'session')
    @marshal_with(question_fields)
    def put(self, id):
        question_parser = reqparse.RequestParser()
        question_parser.add_argument('quiz_id', type=int, help="Quiz ID should be integer", required=True)
        question_parser.add_argument('question_statement', type=str, help="Question statement should be string", required=True)
        question_parser.add_argument('option1', type=str, help="Option 1 should be string", required=True)
        question_parser.add_argument('option2', type=str, help="Option 2 should be string", required=True)
        question_parser.add_argument('correct_answer', type=str, help="Correct answer should be string", required=True)
        args = question_parser.parse_args()
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

class ScoreResource(Resource):
    @auth_required('token', 'session')
    @marshal_with(score_fields)
    def get(self):
        all_scores = Scores.query.all()
        return all_scores

    @auth_required('token', 'session')
    @marshal_with(score_fields)
    def post(self):
        parser.add_argument('quiz_id', type=int, help="Quiz ID should be integer", required=True)
        parser.add_argument('total_scored', type=int, help="Total scored should be integer", required=True)
        parser.add_argument('time_stamp_of_attempt', type=str, help="Timestamp should be string", required=True)
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
        return score
    
    @auth_required('token', 'session')
    @marshal_with(score_fields)
    def put(self, id):
        parser.add_argument('quiz_id', type=int, help="Quiz ID should be integer", required=True)
        parser.add_argument('total_scored', type=int, help="Total scored should be integer", required=True)
        args = parser.parse_args()
        score = Scores.query.get(id)
        if not score:
            return {"message": "score not found"}, 404
        score.quiz_id = args['quiz_id']
        score.total_scored = args['total_scored']
        db.session.commit()
        return score

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

api.add_resource(SubjectResource, '/subjects', '/subjects/<int:id>')
api.add_resource(QuizResource, '/quizzes', '/quizzes/<int:id>')
api.add_resource(QuestionResource, '/questions', '/questions/<int:id>')
api.add_resource(ScoreResource, '/scores', '/scores/<int:id>')
api.add_resource(ChapterResource, '/chapters', '/chapters/<int:id>')

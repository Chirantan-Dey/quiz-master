import store from '../utils/store.js';
import Question from '../components/Question.js';

const QuizAdmin = {
    components: {
        Question
    },
    template: `
    <div class="container">
        <h1>Quiz Admin</h1>
        <div v-for="quiz in quizzes" :key="quiz.name" class="mb-4">
            <h2>{{ quiz.name }}</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Question Text</th>
                        <th>Option 1</th>
                        <th>Option 2</th>
                        <th>Correct Answer</th>
                        <th>Quiz</th>
                        <th>Creator</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    <question
                        v-for="question in quiz.questions"
                        :key="question.id"
                        :text="question.text"
                        :option1="question.option1"
                        :option2="question.option2"
                        :correct-answer="question.correct_answer"
                        :quiz="quiz.name"
                        :creator="question.creator"
                    >
                    </question>
                    <tr>
                        <td colspan="7">
                            <button class="btn btn-sm btn-success" @click="openAddQuestionModal(quiz)">Add Question</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        <button class="btn btn-primary" @click="openAddQuizModal">Add Quiz</button>

        <div class="modal fade" id="questionModal" tabindex="-1" role="dialog" aria-labelledby="questionModalLabel" aria-hidden="true">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="questionModalLabel" v-if="editingQuestion">Edit Question</h5>
                        <h5 class="modal-title" id="questionModalLabel" v-else>Add Question</h5>
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <input type="text" class="form-control" v-model="questionText" placeholder="Question Text"><br>
                        <input type="text" class="form-control" v-model="option1" placeholder="Option 1"><br>
                        <input type="text" class="form-control" v-model="option2" placeholder="Option 2"><br>
                        <input type="text" class="form-control" v-model="correctAnswer" placeholder="Correct Answer">
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" @click="saveQuestion">Save</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="modal fade" id="addQuizModal" tabindex="-1" role="dialog" aria-labelledby="addQuizModalLabel" aria-hidden="true">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="addQuizModalLabel">Add Quiz</h5>
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <input type="text" class="form-control" v-model="quizName" placeholder="Quiz Name"><br>
                        <select class="form-control" v-model="chapterId">
                            <option v-for="chapter in chapters" :key="chapter.id" :value="chapter.id">{{ chapter.name }}</option>
                        </select><br>
                        <input type="date" class="form-control" v-model="dateOfQuiz" placeholder="Date of Quiz"><br>
                        <input type="number" class="form-control" v-model="timeDuration" placeholder="Time Duration"><br>
                        <input type="text" class="form-control" v-model="remarks" placeholder="Remarks">
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" @click="saveQuiz">Save</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            quizzes: [],
            isQuestionModalActive: false,
            isQuizModalActive: false,
            editingQuestion: null,
            questionText: '',
            option1: '',
            option2: '',
            correctAnswer: '',
            quizName: '',
            selectedQuizId: null,
            chapterId: '',
            dateOfQuiz: '',
            timeDuration: '',
            remarks: '',
            chapters: [],
        };
    },
    mounted() {
        this.fetchQuizzes();
        this.fetchChapters();
    },
    methods: {
        async fetchQuizzes() {
            try {
                const response = await fetch('/api/quizzes', {
                    headers: {
                        'Authentication-Token': store.state.authToken
                    }
                });
                const data = await response.json();
                this.quizzes = data;
            } catch (error) {
                console.error('Error fetching quizzes:', error);
            }
        },
        async fetchChapters() {
            try {
                const response = await fetch('/api/chapters', {
                    headers: {
                        'Authentication-Token': store.state.authToken
                    }
                });
                const data = await response.json();
                this.chapters = data;
            } catch (error) {
                console.error('Error fetching chapters:', error);
            }
        },
        openEditQuestionModal(question) {
            this.editingQuestion = question;
            this.questionText = question.text;
            this.option1 = question.option1;
            this.option2 = question.option2;
            this.correctAnswer = question.correct_answer;
            this.isQuestionModalActive = true;
            $('#questionModal').modal('show');
        },
        openAddQuestionModal(quiz) {
            this.editingQuestion = null;
            this.questionText = '';
            this.option1 = '';
            this.option2 = '';
            this.correctAnswer = '';
            this.selectedQuizId = quiz.id;
            this.isQuestionModalActive = true;
            $('#questionModal').modal('show');
        },

        closeQuestionModal() {
            this.isQuestionModalActive = false;
            this.editingQuestion = null;
            this.questionText = '';
            this.option1 = '';
            this.option2 = '';
            this.correctAnswer = '';
            $('#questionModal').modal('hide');
        },
        async saveQuestion() {
            try {
                const headers = {
                    'Content-Type': 'application/json',
                    'Authentication-Token': store.state.authToken
                };

                if (this.editingQuestion) {
                    const body = JSON.stringify({
                        quiz_id: this.editingQuestion.quiz_id,
                        text: this.questionText,
                        option1: this.option1,
                        option2: this.option2,
                        correct_answer: this.correctAnswer
                    });
                    await fetch(`/api/questions/${this.editingQuestion.id}`, {
                        method: 'PUT',
                        headers,
                        body,
                    });
                } else {
                    await fetch('/api/questions', {
                        method: 'POST',
                        headers,
                        body: JSON.stringify({
                            quiz_id: this.selectedQuizId,
                            text: this.questionText,
                            option1: this.option1,
                            option2: this.option2,
                            correct_answer: this.correctAnswer
                        }),
                    });
                }
                this.fetchQuizzes();
                this.closeQuestionModal();
            } catch (error) {
                console.error('Error saving question:', error);
            }
        },
        async handleDeleteQuestion(questionId) {
            try {
                await fetch(`/api/questions/${questionId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authentication-Token': store.state.authToken
                    }
                });
                this.fetchQuizzes();
            } catch (error) {
                console.error('Error deleting question:', error);
            }
        },
        openAddQuizModal() {
            console.log('openAddQuizModal called');
            this.isQuizModalActive = true;
            this.quizName = '';
            $('#addQuizModal').modal('show');
        },
        closeQuizModal() {
            this.isQuizModalActive = false;
            this.quizName = '';
            $('#addQuizModal').modal('hide');

        },
        async saveQuiz() {
            try {
                const dateObject = new Date(this.dateOfQuiz);
                await fetch('/api/quizzes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authentication-Token': store.state.authToken
                    },
                    body: JSON.stringify({
                        name: this.quizName,
                        chapter_id: this.chapterId,
                        date_of_quiz: dateObject,
                        time_duration: this.timeDuration,
                        remarks: this.remarks
                    }),
                });
                this.fetchQuizzes();
                this.closeQuizModal();
            } catch (error) {
                console.error('Error saving quiz:', error);
            }
        }
    },
};

export default QuizAdmin;
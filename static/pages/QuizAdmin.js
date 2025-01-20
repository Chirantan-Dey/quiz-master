import store from '../utils/store.js';
import Question from '../components/Question.js';

const QuizAdmin = {
    components: {
        Question
    },
    template: `
    <div class="container">
        <h1>Quiz Admin</h1>
        <div v-if="filteredQuizzes.length === 0" class="alert alert-info">
            No matches found
        </div>
        <div v-for="quiz in filteredQuizzes" :key="quiz.name" class="mb-4">
            <h2>{{ quiz.name }}</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Question Statement</th>
                        <th>Option 1</th>
                        <th>Option 2</th>
                        <th>Correct Answer</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <Question
                        v-for="question in quiz.questions"
                        :key="question.id"
                        :question="question"
                        :isAdmin="true"
                        @edit="openEditQuestionModal"
                        @delete="handleDeleteQuestion"
                    />
                    <tr>
                        <td colspan="2">
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
                        <div v-if="formError" class="alert alert-danger">{{ formError }}</div>
                        <div class="form-group mb-3">
                            <label>Question Statement</label>
                            <input
                                type="text"
                                class="form-control"
                                v-model="questionData.question_statement"
                                placeholder="Enter question statement"
                                maxlength="500"
                            >
                            <small class="text-muted">Maximum 500 characters</small>
                        </div>
                        <div class="form-group mb-3">
                            <label>Option 1</label>
                            <input
                                type="text"
                                class="form-control"
                                v-model="questionData.option1"
                                placeholder="Enter option 1"
                                maxlength="200"
                            >
                            <small class="text-muted">Maximum 200 characters</small>
                        </div>
                        <div class="form-group mb-3">
                            <label>Option 2</label>
                            <input
                                type="text"
                                class="form-control"
                                v-model="questionData.option2"
                                placeholder="Enter option 2"
                                maxlength="200"
                            >
                            <small class="text-muted">Maximum 200 characters</small>
                        </div>
                        <div class="form-group mb-3">
                            <label>Correct Answer</label>
                            <select class="form-control" v-model="questionData.correct_answer">
                                <option value="">Select correct answer</option>
                                <option v-if="questionData.option1" :value="questionData.option1">{{ questionData.option1 }}</option>
                                <option v-if="questionData.option2" :value="questionData.option2">{{ questionData.option2 }}</option>
                            </select>
                        </div>
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
                        <input type="number" class="form-control" v-model="timeDuration" placeholder="Time Duration(in minutes)"><br>
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
            questionData: {
                question_statement: '',
                option1: '',
                option2: '',
                correct_answer: ''
            },
            formError: '',
            quizName: '',
            selectedQuizId: null,
            chapterId: '',
            dateOfQuiz: '',
            timeDuration: '',
            remarks: '',
            chapters: [],
        };
    },
    computed: {
        filteredQuizzes() {
            const query = this.$store.state.search.query.toLowerCase();
            if (!query) return this.quizzes;
            
            return this.quizzes.filter(quiz => 
                quiz.name.toLowerCase().includes(query) ||
                (quiz.remarks && quiz.remarks.toLowerCase().includes(query))
            );
        }
    },
    mounted() {
        this.fetchQuizzes();
        this.fetchChapters();
    },
    methods: {
        resetQuizForm() {
            this.quizName = '';
            this.chapterId = '';
            this.dateOfQuiz = '';
            this.timeDuration = '';
            this.remarks = '';
        },
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
            this.questionData = {
                question_statement: question.question_statement,
                option1: question.option1,
                option2: question.option2,
                correct_answer: question.correct_answer
            };
            this.isQuestionModalActive = true;
            $('#questionModal').modal('show');
        },
        openAddQuestionModal(quiz) {
            this.editingQuestion = null;
            this.questionData = {
                question_statement: '',
                option1: '',
                option2: '',
                correct_answer: ''
            };
            this.selectedQuizId = quiz.id;
            this.isQuestionModalActive = true;
            $('#questionModal').modal('show');
        },
        closeQuestionModal() {
            this.isQuestionModalActive = false;
            this.editingQuestion = null;
            this.questionData = {
                question_statement: '',
                option1: '',
                option2: '',
                correct_answer: ''
            };
            this.formError = '';
            $('#questionModal').modal('hide');
        },
        validateQuestionData() {
            if (!this.questionData.question_statement.trim()) {
                this.formError = 'Question statement is required';
                return false;
            }
            if (!this.questionData.option1.trim()) {
                this.formError = 'Option 1 is required';
                return false;
            }
            if (!this.questionData.option2.trim()) {
                this.formError = 'Option 2 is required';
                return false;
            }
            if (!this.questionData.correct_answer) {
                this.formError = 'Please select the correct answer';
                return false;
            }
            if (this.questionData.question_statement.length > 500) {
                this.formError = 'Question statement must be less than 500 characters';
                return false;
            }
            if (this.questionData.option1.length > 200 || this.questionData.option2.length > 200) {
                this.formError = 'Options must be less than 200 characters';
                return false;
            }
            this.formError = '';
            return true;
        },
        async saveQuestion() {
            try {
                if (!this.validateQuestionData()) {
                    return;
                }

                const headers = {
                    'Content-Type': 'application/json',
                    'Authentication-Token': store.state.authToken
                };
                
                const payload = {
                    ...this.questionData,
                    quiz_id: parseInt(this.selectedQuizId)
                };

                let response;
                if (this.editingQuestion) {
                    response = await fetch(`/api/questions/${this.editingQuestion.id}`, {
                        method: 'PUT',
                        headers,
                        body: JSON.stringify(payload)
                    });
                } else {
                    response = await fetch('/api/questions', {
                        method: 'POST',
                        headers,
                        body: JSON.stringify(payload)
                    });
                }

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.message || 'Failed to save question');
                }
                
                await this.fetchQuizzes();
                this.closeQuestionModal();
            } catch (error) {
                console.error('Error saving question:', error);
                this.formError = error.message || 'Failed to save question. Please try again.';
            }
        },
        async handleDeleteQuestion(questionId) {
            try {
                if (!confirm('Are you sure you want to delete this question? This action cannot be undone.')) {
                    return;
                }

                const response = await fetch(`/api/questions/${questionId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authentication-Token': store.state.authToken
                    }
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.message || 'Failed to delete question');
                }

                await this.fetchQuizzes();
            } catch (error) {
                console.error('Error deleting question:', error);
                alert('Failed to delete question: ' + (error.message || 'Please try again'));
            }
        },
        openAddQuizModal() {
            this.isQuizModalActive = true;
            this.resetQuizForm();
            $('#addQuizModal').modal('show');
        },
        closeQuizModal() {
            this.isQuizModalActive = false;
            this.resetQuizForm();
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
                await this.fetchQuizzes();
                this.closeQuizModal();
            } catch (error) {
                console.error('Error saving quiz:', error);
            }
        }
    },
};

export default QuizAdmin;
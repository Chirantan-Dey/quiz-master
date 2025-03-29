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
            <div class="table-responsive">
                <table class="table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Question</th>
                            <th class="d-none d-md-table-cell">Option 1</th>
                            <th class="d-none d-md-table-cell">Option 2</th>
                            <th class="d-none d-md-table-cell">Correct Answer</th>
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
                            <td colspan="6">
                                <button class="btn btn-sm btn-success" @click="openAddQuestionModal(quiz)">Add Question</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        <button class="btn btn-primary" @click="openAddQuizModal">Add Quiz</button>

        <div class="modal fade" id="questionModal" tabindex="-1" aria-labelledby="questionModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="questionModalLabel" v-if="editingQuestion">Edit Question</h5>
                        <h5 class="modal-title" id="questionModalLabel" v-else>Add Question</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <form @submit.prevent="saveQuestion">
                        <div class="modal-body">
                            <div v-if="formError" class="alert alert-danger">{{ formError }}</div>
                            <div class="form-group mb-3">
                                <label>Question Statement</label>
                                <input
                                    type="text"
                                    class="form-control"
                                    v-model="questionData.question_statement"
                                    placeholder="Enter question statement"
                                    required
                                    @input="validateQuestionField('question_statement')"
                                >
                                <small class="text-muted">10-500 characters</small>
                                <div v-if="fieldErrors.question_statement" class="text-danger small mt-1">{{ fieldErrors.question_statement }}</div>
                            </div>
                            <div class="form-group mb-3">
                                <label>Option 1</label>
                                <input
                                    type="text"
                                    class="form-control"
                                    v-model="questionData.option1"
                                    placeholder="Enter option 1"
                                    required
                                    @input="validateQuestionField('option1')"
                                >
                                <small class="text-muted">1-200 characters</small>
                                <div v-if="fieldErrors.option1" class="text-danger small mt-1">{{ fieldErrors.option1 }}</div>
                            </div>
                            <div class="form-group mb-3">
                                <label>Option 2</label>
                                <input
                                    type="text"
                                    class="form-control"
                                    v-model="questionData.option2"
                                    placeholder="Enter option 2"
                                    required
                                    @input="validateQuestionField('option2')"
                                >
                                <small class="text-muted">1-200 characters</small>
                                <div v-if="fieldErrors.option2" class="text-danger small mt-1">{{ fieldErrors.option2 }}</div>
                            </div>
                            <div class="form-group mb-3">
                                <label>Correct Answer</label>
                                <select class="form-control" v-model="questionData.correct_answer" required>
                                    <option value="">Select correct answer</option>
                                    <option v-if="questionData.option1" :value="questionData.option1">{{ questionData.option1 }}</option>
                                    <option v-if="questionData.option2" :value="questionData.option2">{{ questionData.option2 }}</option>
                                </select>
                                <div v-if="fieldErrors.correct_answer" class="text-danger small mt-1">{{ fieldErrors.correct_answer }}</div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-primary">Save</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <div class="modal fade" id="addQuizModal" tabindex="-1" aria-labelledby="addQuizModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="addQuizModalLabel">Add Quiz</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <form @submit.prevent="saveQuiz">
                        <div class="modal-body">
                            <div v-if="quizError" class="alert alert-danger">{{ quizError }}</div>
                            <div class="form-group mb-3">
                                <label>Quiz Name</label>
                                <input
                                    type="text"
                                    class="form-control"
                                    v-model="quizName"
                                    placeholder="Quiz Name"
                                    required
                                    @input="validateQuizField('name')"
                                >
                                <div v-if="quizFieldErrors.name" class="text-danger small mt-1">{{ quizFieldErrors.name }}</div>
                            </div>
                            <div class="form-group mb-3">
                                <label>Chapter</label>
                                <select class="form-control" v-model="chapterId" required>
                                    <option value="">Select a chapter</option>
                                    <option v-for="chapter in chapters" :key="chapter.id" :value="chapter.id">{{ chapter.name }}</option>
                                </select>
                                <div v-if="quizFieldErrors.chapter" class="text-danger small mt-1">{{ quizFieldErrors.chapter }}</div>
                            </div>
                            <div class="form-group mb-3">
                                <label>Date of Quiz</label>
                                <input
                                    type="date"
                                    class="form-control"
                                    v-model="dateOfQuiz"
                                    required
                                    :min="getCurrentDate()"
                                >
                                <div v-if="quizFieldErrors.date" class="text-danger small mt-1">{{ quizFieldErrors.date }}</div>
                            </div>
                            <div class="form-group mb-3">
                                <label>Duration (minutes)</label>
                                <input
                                    type="number"
                                    class="form-control"
                                    v-model.number="timeDuration"
                                    placeholder="Enter duration in minutes"
                                    required
                                    min="1"
                                    max="180"
                                    @input="validateQuizField('duration')"
                                >
                                <div v-if="quizFieldErrors.duration" class="text-danger small mt-1">{{ quizFieldErrors.duration }}</div>
                            </div>
                            <div class="form-group mb-3">
                                <label>Remarks</label>
                                <input
                                    type="text"
                                    class="form-control"
                                    v-model="remarks"
                                    placeholder="Enter remarks (optional)"
                                >
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-primary">Save</button>
                        </div>
                    </form>
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
            fieldErrors: {
                question_statement: '',
                option1: '',
                option2: '',
                correct_answer: ''
            },
            quizError: '',
            quizFieldErrors: {
                name: '',
                chapter: '',
                date: '',
                duration: ''
            },
            quizName: '',
            selectedQuizId: null,
            chapterId: '',
            dateOfQuiz: '',
            timeDuration: '',
            remarks: '',
            chapters: [],
            questionModal: null,
            quizModal: null
        };
    },
    computed: {
        filteredQuizzes() {
            const query = this.$store.state.search.query.toLowerCase();
            if (!query) return this.quizzes;
            
            return this.quizzes.filter(quiz => {
                // Check if quiz name or remarks match
                if (quiz.name.toLowerCase().includes(query) ||
                    (quiz.remarks && quiz.remarks.toLowerCase().includes(query))) {
                    return true;
                }
                
                // Check if any question in the quiz matches
                if (quiz.questions && quiz.questions.length > 0) {
                    return quiz.questions.some(question => 
                        question.question_statement.toLowerCase().includes(query) ||
                        question.option1.toLowerCase().includes(query) ||
                        question.option2.toLowerCase().includes(query) ||
                        question.correct_answer.toLowerCase().includes(query)
                    );
                }
                
                return false;
            });
        }
    },
    mounted() {
        this.fetchQuizzes();
        this.fetchChapters();
        this.questionModal = new bootstrap.Modal(document.getElementById('questionModal'));
        this.quizModal = new bootstrap.Modal(document.getElementById('addQuizModal'));
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
            this.selectedQuizId = question.quiz_id;
            this.questionData = {
                question_statement: question.question_statement,
                option1: question.option1,
                option2: question.option2,
                correct_answer: question.correct_answer
            };
            this.isQuestionModalActive = true;
            this.questionModal.show();
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
            this.questionModal.show();
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
            this.questionModal.hide();
        },
        validateQuestionData() {
            const fields = {
                'question_statement': 'Question',
                'option1': 'Option 1',
                'option2': 'Option 2'
            };
            
            for (const [field, label] of Object.entries(fields)) {
                if (!this.questionData[field].trim()) {
                    this.formError = `${label} is required`;
                    return false;
                }
            }
            
            if (!this.questionData.correct_answer) {
                this.formError = 'Please select the correct answer';
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
            this.quizModal.show();
        },
        closeQuizModal() {
            this.isQuizModalActive = false;
            this.resetQuizForm();
            this.quizModal.hide();
        },
        validateQuestionField(field) {
            const labels = {
                'question_statement': 'Question statement',
                'option1': 'Option 1',
                'option2': 'Option 2',
                'correct_answer': 'Correct answer'
            };

            if (field === 'correct_answer') {
                if (!this.questionData.correct_answer) {
                    this.fieldErrors.correct_answer = 'Please select the correct answer';
                } else {
                    this.fieldErrors.correct_answer = '';
                }
                return;
            }

            if (!this.questionData[field]?.trim()) {
                this.fieldErrors[field] = `${labels[field]} is required`;
            } else {
                this.fieldErrors[field] = '';
            }
        },
        validateQuizField(field) {
            switch(field) {
                case 'name':
                    if (!this.quizName.trim()) {
                        this.quizFieldErrors.name = 'Quiz name is required';
                    } else {
                        this.quizFieldErrors.name = '';
                    }
                    break;
                case 'chapter':
                    if (!this.chapterId) {
                        this.quizFieldErrors.chapter = 'Please select a chapter';
                    } else {
                        this.quizFieldErrors.chapter = '';
                    }
                    break;
                case 'duration':
                    const duration = parseInt(this.timeDuration);
                    if (!duration || duration <= 0) {
                        this.quizFieldErrors.duration = 'Duration must be a positive number';
                    } else {
                        this.quizFieldErrors.duration = '';
                    }
                    break;
            }
        },
        getCurrentDate() {
            return new Date().toISOString().split('T')[0];
        },
        async saveQuiz() {
            try {
                this.validateQuizField('name');
                this.validateQuizField('chapter');
                this.validateQuizField('duration');
                
                if (this.quizFieldErrors.name || this.quizFieldErrors.chapter || this.quizFieldErrors.duration) {
                    return;
                }
                
                if (!this.dateOfQuiz) {
                    this.quizFieldErrors.date = 'Please select a date';
                    return;
                }
                
                const dateObject = new Date(this.dateOfQuiz);
                if (dateObject < new Date().setHours(0, 0, 0, 0)) {
                    this.quizFieldErrors.date = 'Date cannot be in the past';
                    return;
                }

                const response = await fetch('/api/quizzes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authentication-Token': store.state.authToken
                    },
                    body: JSON.stringify({
                        name: this.quizName,
                        chapter_id: parseInt(this.chapterId),
                        date_of_quiz: dateObject.toISOString(),
                        time_duration: parseInt(this.timeDuration),
                        remarks: this.remarks || ''
                    }),
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.message || 'Failed to save quiz');
                }

                await this.fetchQuizzes();
                this.closeQuizModal();
            } catch (error) {
                console.error('Error saving quiz:', error);
                this.quizError = error.message || 'Failed to save quiz. Please try again.';
            }
        }
    }
};

export default QuizAdmin;
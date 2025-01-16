import store from '../utils/store.js';

const QuizAdmin = {
  template: `
    <div class="container">
      <h1>Quiz Admin</h1>
      <div v-for="quiz in quizzes" :key="quiz.name" class="mb-4">
        <h2>{{ quiz.name }}</h2>
        <table class="table">
          <thead>
            <tr>
              <th>Question Text</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="question in quiz.questions" :key="question.id">
              <td>{{ question.text }}</td>
              <td>
                <button class="btn btn-sm btn-primary mr-2" @click="openEditQuestionModal(question)">Edit</button>
                <button class="btn btn-sm btn-danger" @click="handleDeleteQuestion(question.id)">Delete</button>
              </td>
            </tr>
            <tr>
              <td colspan="2">
                <button class="btn btn-sm btn-success" @click="openAddQuestionModal(quiz.name)">Add Question</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <button class="btn btn-primary" @click="openAddQuizModal">Add Quiz</button>

        <div class="modal" :class="{ 'show': isQuestionModalActive }" >
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" v-if="editingQuestion">Edit Question</h5>
                        <h5 class="modal-title" v-else>Add Question</h5>
                        <button type="button" class="close" @click="closeQuestionModal">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <input type="text" class="form-control" v-model="questionText" placeholder="Question Text">
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-primary" @click="saveQuestion">Save</button>
                        <button class="btn btn-secondary" @click="closeQuestionModal">Cancel</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="modal" :class="{ 'show': isQuizModalActive }" >
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Add Quiz</h5>
                        <button type="button" class="close" @click="closeQuizModal">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <input type="text" class="form-control" v-model="quizName" placeholder="Quiz Name">
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-primary" @click="saveQuiz">Save</button>
                        <button class="btn btn-secondary" @click="closeQuizModal">Cancel</button>
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
        quizName: '',
        selectedQuizName: '',
    };
  },
  mounted() {
    this.fetchQuizzes();
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
      openEditQuestionModal(question) {
          this.editingQuestion = question;
          this.questionText = question.text;
          this.isQuestionModalActive = true;
          document.body.classList.add('modal-open');
      },
      openAddQuestionModal(quizName) {
          this.editingQuestion = null;
          this.questionText = '';
          this.selectedQuizName = quizName;
          this.isQuestionModalActive = true;
          document.body.classList.add('modal-open');
      },
      closeQuestionModal() {
          this.isQuestionModalActive = false;
          this.editingQuestion = null;
          this.questionText = '';
          document.body.classList.remove('modal-open');
      },
      async saveQuestion() {
          try {
              const headers = {
                  'Content-Type': 'application/json',
                  'Authentication-Token': store.state.authToken
              };
              const body = JSON.stringify({ text: this.questionText });
              if (this.editingQuestion) {
                  await fetch(`/api/questions/${this.editingQuestion.id}`, {
                      method: 'PUT',
                      headers,
                      body,
                  });
              } else {
                  await fetch('/api/questions', {
                      method: 'POST',
                      headers,
                      body: JSON.stringify({ text: this.questionText, quiz_name: this.selectedQuizName }),
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
          this.isQuizModalActive = true;
          this.quizName = '';
          document.body.classList.add('modal-open');
      },
      closeQuizModal() {
          this.isQuizModalActive = false;
          this.quizName = '';
          document.body.classList.remove('modal-open');
      },
      async saveQuiz() {
          try {
              await fetch('/api/quizzes', {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/json',
                      'Authentication-Token': store.state.authToken
                  },
                  body: JSON.stringify({ name: this.quizName }),
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
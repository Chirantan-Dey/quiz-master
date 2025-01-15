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
                <button class="btn btn-sm btn-primary mr-2" @click="handleEditQuestion(question.id)">Edit</button>
                <button class="btn btn-sm btn-danger" @click="handleDeleteQuestion(question.id)">Delete</button>
              </td>
            </tr>
            <tr>
              <td colspan="2">
                <button class="btn btn-sm btn-success" @click="handleAddQuestion(quiz.name)">Add Question</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <button class="btn btn-primary" @click="handleAddQuiz">Add Quiz</button>
    </div>
  `,
  data() {
    return {
      quizzes: [],
    };
  },
  mounted() {
    this.fetchQuizzes();
  },
  methods: {
    async fetchQuizzes() {
      try {
        const response = await fetch('/api/quizzes');
        const data = await response.json();
        this.quizzes = data;
      } catch (error) {
        console.error('Error fetching quizzes:', error);
      }
    },
    handleEditQuestion(questionId) {
      // Implement edit question logic
      console.log('Edit question:', questionId);
    },
    handleDeleteQuestion(questionId) {
      // Implement delete question logic
      console.log('Delete question:', questionId);
    },
    handleAddQuestion(quizName) {
      // Implement add question logic
      console.log('Add question to:', quizName);
    },
      handleAddQuiz() {
          // Implement add quiz logic
          console.log('Add quiz');
      }
  },
};

export default QuizAdmin;
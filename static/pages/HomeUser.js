const HomeUser = {
  template: `
    <div class="container mt-4">
      <!-- Quiz Table -->
      <h2>Quizzes</h2>
      <table class="table">
        <thead>
          <tr>
            <th>Quiz ID</th>
            <th>Number of Questions</th>
            <th>Date</th>
            <th>Duration (in minutes)</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="quiz in quizzes" :key="quiz.id">
            <td>{{quiz.id}}</td>
            <td>{{quiz.questions.length}}</td>
            <td>{{formatDate(quiz.date_of_quiz)}}</td>
            <td>{{quiz.time_duration}}</td>
            <td>
              <button class="btn btn-secondary me-2" @click="viewQuiz(quiz)">View</button>
              <button class="btn btn-primary" @click="startQuiz(quiz)">Start</button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- View Quiz Modal -->
      <div class="modal fade" id="viewQuizModal" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Quiz Details</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" v-if="selectedQuiz">
              <p><strong>Quiz ID:</strong> {{selectedQuiz.id}}</p>
              <p><strong>Quiz Name:</strong> {{selectedQuiz.name}}</p>
              <p><strong>Chapter:</strong> {{chapters[selectedQuiz.chapter_id]?.name}}</p>
              <p><strong>Number of Questions:</strong> {{selectedQuiz.questions.length}}</p>
              <p><strong>Date:</strong> {{formatDate(selectedQuiz.date_of_quiz)}}</p>
              <p><strong>Duration (in minutes):</strong> {{selectedQuiz.time_duration}}</p>
              <p><strong>Remarks:</strong> {{selectedQuiz.remarks}}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Start Quiz Modal -->
      <div class="modal fade" id="startQuizModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Quiz</h5>
              <div class="ms-auto">{{formatCountdown}}</div>
            </div>
            <div class="modal-body">
              <div class="row">
                <!-- Left sidebar with question numbers -->
                <div class="col-3">
                  <div class="list-group">
                    <a 
                      v-for="(question, index) in currentQuiz?.questions" 
                      :key="index"
                      href="#"
                      class="list-group-item list-group-item-action"
                      :class="{'bg-success text-white': isAnswered(index)}"
                      @click.prevent="showQuestion(index)"
                    >
                      {{index + 1}}
                    </a>
                  </div>
                </div>
                
                <!-- Main question area -->
                <div class="col-9">
                  <div v-if="currentQuestion">
                    <p class="h5 mb-4">Question {{currentQuestionIndex + 1}}: {{currentQuestion.question_statement}}</p>
                    <div class="form-check mb-2">
                      <input 
                        type="radio" 
                        class="form-check-input"
                        :name="'q'+currentQuestionIndex"
                        :value="currentQuestion.option1"
                        v-model="currentAnswer"
                      >
                      <label class="form-check-label">{{currentQuestion.option1}}</label>
                    </div>
                    <div class="form-check mb-4">
                      <input 
                        type="radio" 
                        class="form-check-input"
                        :name="'q'+currentQuestionIndex"
                        :value="currentQuestion.option2"
                        v-model="currentAnswer"
                      >
                      <label class="form-check-label">{{currentQuestion.option2}}</label>
                    </div>
                    <div class="d-flex justify-content-between">
                      <button class="btn btn-primary" @click="saveAndNext">Save and Next</button>
                      <button class="btn btn-success" @click="submitQuiz">Submit</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,

  data() {
    return {
      quizzes: [],
      chapters: {},
      selectedQuiz: null,
      currentQuiz: null,
      currentQuestionIndex: 0,
      currentAnswer: null,
      answers: new Map(),
      timeRemainingSeconds: 0,
      timerInterval: null,
      viewModal: null,
      startModal: null
    };
  },

  computed: {
    currentQuestion() {
      if (!this.currentQuiz) return null;
      return this.currentQuiz.questions[this.currentQuestionIndex];
    },

    formatCountdown() {
      const minutes = Math.floor(this.timeRemainingSeconds / 60);
      const seconds = this.timeRemainingSeconds % 60;
      return `Time Remaining: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
  },

  methods: {
    async fetchQuizzes() {
      try {
        const response = await fetch('/api/quizzes', {
          headers: {
            'Authentication-Token': this.$store.state.authToken
          }
        });
        this.quizzes = await response.json();
      } catch (error) {
        console.error('Error fetching quizzes:', error);
      }
    },

    async fetchChapters() {
      try {
        const response = await fetch('/api/chapters', {
          headers: {
            'Authentication-Token': this.$store.state.authToken
          }
        });
        const chapters = await response.json();
        this.chapters = chapters.reduce((acc, chapter) => {
          acc[chapter.id] = chapter;
          return acc;
        }, {});
      } catch (error) {
        console.error('Error fetching chapters:', error);
      }
    },

    formatDate(dateString) {
      if (!dateString) return '';
      return new Date(dateString).toLocaleDateString();
    },

    viewQuiz(quiz) {
      this.selectedQuiz = quiz;
      this.viewModal.show();
    },

    startQuiz(quiz) {
      this.currentQuiz = quiz;
      this.currentQuestionIndex = 0;
      this.answers = new Map();
      this.currentAnswer = null;
      this.startTimer(quiz.time_duration);
      this.startModal.show();
    },

    startTimer(duration) {
      // Convert duration from minutes to seconds
      this.timeRemainingSeconds = duration * 60;
      if (this.timerInterval) {
        clearInterval(this.timerInterval);
      }
      this.timerInterval = setInterval(() => {
        if (this.timeRemainingSeconds > 0) {
          this.timeRemainingSeconds--;
        } else {
          this.submitQuiz();
        }
      }, 1000); // Update every second
    },

    showQuestion(index) {
      this.currentQuestionIndex = index;
      this.currentAnswer = this.answers.get(index) || null;
    },

    isAnswered(index) {
      return this.answers.has(index);
    },

    saveAndNext() {
      if (this.currentAnswer) {
        this.answers.set(this.currentQuestionIndex, this.currentAnswer);
        this.currentQuestionIndex = 
          (this.currentQuestionIndex + 1) % this.currentQuiz.questions.length;
        this.currentAnswer = this.answers.get(this.currentQuestionIndex) || null;
      }
    },

    async submitQuiz() {
      if (this.timerInterval) {
        clearInterval(this.timerInterval);
      }

      // Calculate score
      let totalScore = 0;
      this.currentQuiz.questions.forEach((question, index) => {
        if (this.answers.get(index) === question.correct_answer) {
          totalScore++;
        }
      });

      try {
        await fetch('/api/scores', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authentication-Token': this.$store.state.authToken
          },
          body: JSON.stringify({
            quiz_id: this.currentQuiz.id,
            time_stamp_of_attempt: new Date().toISOString(),
            total_scored: totalScore
          })
        });

        this.startModal.hide();
      } catch (error) {
        console.error('Error submitting quiz:', error);
      }
    }
  },

  async mounted() {
    await Promise.all([
      this.fetchQuizzes(),
      this.fetchChapters()
    ]);
    this.viewModal = new bootstrap.Modal(document.getElementById('viewQuizModal'));
    this.startModal = new bootstrap.Modal(document.getElementById('startQuizModal'));
  },

  beforeUnmount() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  }
};

export default HomeUser;
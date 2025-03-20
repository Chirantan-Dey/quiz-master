import { api } from '../utils/api.js';

const STORAGE_KEY = 'quiz_in_progress';

const HomeUser = {
  template: `
<<<<<<< Updated upstream
    <div>
      <h1>User Home</h1>
      {/* Add user-specific home page content */}
    </div>
  `,
=======
    <div class="container mt-4" @keydown="handleKeyPress">
      <!-- Loading State -->
      <div v-if="isLoading" class="text-center" role="status" aria-live="polite">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <!-- Error State -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = null" aria-label="Close"></button>
      </div>

      <!-- Resume Quiz Alert -->
      <div v-if="hasInProgressQuiz" class="alert alert-warning alert-dismissible fade show" role="alert">
        You have an unfinished quiz. Would you like to resume?
        <div class="mt-2">
          <button class="btn btn-sm btn-primary me-2" @click="resumeQuiz">Resume</button>
          <button class="btn btn-sm btn-secondary" @click="clearInProgressQuiz">Start Fresh</button>
        </div>
      </div>

      <!-- Quiz Table -->
      <div v-if="!isLoading">
        <h2>Available Quizzes</h2>
        <div v-if="quizzes.length === 0" class="alert alert-info" role="status">
          No quizzes available at the moment.
        </div>
        <table v-else class="table" role="grid">
          <thead>
            <tr>
              <th scope="col">Quiz ID</th>
              <th scope="col">Name</th>
              <th scope="col">Questions</th>
              <th scope="col">Date</th>
              <th scope="col">Duration</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="quiz in quizzes" :key="quiz.id">
              <td>{{quiz.id}}</td>
              <td>{{quiz.name}}</td>
              <td>{{quiz.questions.length}}</td>
              <td>{{formatDate(quiz.date_of_quiz)}}</td>
              <td>{{quiz.time_duration}} mins</td>
              <td>
                <button 
                  class="btn btn-secondary me-2" 
                  @click="viewQuiz(quiz)"
                  :disabled="isActionLoading"
                  aria-label="View quiz details"
                >
                  View
                </button>
                <button 
                  class="btn btn-primary" 
                  @click="startQuiz(quiz)"
                  :disabled="isActionLoading"
                  aria-label="Start quiz"
                >
                  Start
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ... [View Quiz Modal remains unchanged] ... -->

      <!-- Start Quiz Modal -->
      <div class="modal fade" id="startQuizModal" tabindex="-1" data-bs-backdrop="static">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title d-flex justify-content-between w-100">
                <span>Quiz: {{ currentQuiz?.name }}</span>
                <span 
                  class="badge" 
                  :class="timeRemainingSeconds <= 60 ? 'bg-danger' : 'bg-warning'"
                  role="timer"
                  aria-label="Time remaining"
                >
                  {{ formatCountdown }}
                </span>
              </h5>
            </div>
            <div class="modal-body">
              <!-- Progress bar -->
              <div class="progress mb-3">
                <div 
                  class="progress-bar" 
                  role="progressbar"
                  :style="{ width: (answeredQuestions / totalQuestions * 100) + '%' }"
                  :aria-valuenow="answeredQuestions"
                  aria-valuemin="0"
                  :aria-valuemax="totalQuestions"
                >
                  {{ answeredQuestions }}/{{ totalQuestions }}
                </div>
              </div>

              <div class="row">
                <!-- ... [Question navigation remains similar with added aria-labels] ... -->
                <!-- Main question area with improved accessibility -->
                <div class="col-9">
                  <div v-if="currentQuestion" class="p-3 border rounded">
                    <p class="h5 mb-4" role="heading">
                      Question {{currentQuestionIndex + 1}}: {{currentQuestion.question_statement}}
                    </p>
                    <fieldset role="radiogroup" :aria-label="'Question ' + (currentQuestionIndex + 1)">
                      <div class="form-check mb-3">
                        <input 
                          type="radio" 
                          class="form-check-input"
                          :id="'option1-'+currentQuestionIndex"
                          :name="'q'+currentQuestionIndex"
                          :value="currentQuestion.option1"
                          v-model="currentAnswer"
                          @change="autoSaveAnswer"
                        >
                        <label class="form-check-label" :for="'option1-'+currentQuestionIndex">
                          {{currentQuestion.option1}}
                        </label>
                      </div>
                      <div class="form-check mb-4">
                        <input 
                          type="radio" 
                          class="form-check-input"
                          :id="'option2-'+currentQuestionIndex"
                          :name="'q'+currentQuestionIndex"
                          :value="currentQuestion.option2"
                          v-model="currentAnswer"
                          @change="autoSaveAnswer"
                        >
                        <label class="form-check-label" :for="'option2-'+currentQuestionIndex">
                          {{currentQuestion.option2}}
                        </label>
                      </div>
                    </fieldset>
                    <div class="d-flex justify-content-between mt-4">
                      <button 
                        class="btn btn-secondary" 
                        @click="previousQuestion" 
                        :disabled="currentQuestionIndex === 0"
                        aria-label="Previous question"
                      >
                        <span aria-hidden="true">←</span> Previous
                      </button>
                      <button 
                        class="btn btn-primary" 
                        @click="nextQuestion"
                        :disabled="currentQuestionIndex === currentQuiz.questions.length - 1"
                        aria-label="Next question"
                      >
                        Next <span aria-hidden="true">→</span>
                      </button>
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
      isLoading: false,
      isActionLoading: false,
      isSubmitting: false,
      error: null,
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
      startModal: null,
      autoSaveTimeout: null,
      hasInProgressQuiz: false
    };
  },

  computed: {
    // ... [Previous computed properties remain unchanged] ...
  },

  methods: {
    // ... [Previous methods remain similar with added functionality] ...

    handleKeyPress(event) {
      if (this.currentQuiz) {
        switch(event.key) {
          case 'ArrowLeft':
            this.previousQuestion();
            break;
          case 'ArrowRight':
            this.nextQuestion();
            break;
          case '1':
            if (this.currentQuestion) {
              this.currentAnswer = this.currentQuestion.option1;
              this.autoSaveAnswer();
            }
            break;
          case '2':
            if (this.currentQuestion) {
              this.currentAnswer = this.currentQuestion.option2;
              this.autoSaveAnswer();
            }
            break;
        }
      }
    },

    saveProgress() {
      if (this.currentQuiz) {
        const progress = {
          quizId: this.currentQuiz.id,
          answers: Array.from(this.answers.entries()),
          timeRemaining: this.timeRemainingSeconds,
          timestamp: new Date().getTime()
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
      }
    },

    loadProgress() {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const progress = JSON.parse(saved);
        // Check if saved progress is less than 24 hours old
        if (new Date().getTime() - progress.timestamp < 24 * 60 * 60 * 1000) {
          this.hasInProgressQuiz = true;
          return progress;
        }
        this.clearInProgressQuiz();
      }
      return null;
    },

    clearInProgressQuiz() {
      localStorage.removeItem(STORAGE_KEY);
      this.hasInProgressQuiz = false;
    },

    async resumeQuiz() {
      const progress = this.loadProgress();
      if (progress) {
        const quiz = this.quizzes.find(q => q.id === progress.quizId);
        if (quiz) {
          this.currentQuiz = quiz;
          this.answers = new Map(progress.answers);
          this.timeRemainingSeconds = progress.timeRemaining;
          this.startTimer(quiz.time_duration);
          this.startModal.show();
        }
      }
      this.clearInProgressQuiz();
    },

    // Modified methods

    autoSaveAnswer() {
      if (this.currentAnswer) {
        this.answers.set(this.currentQuestionIndex, this.currentAnswer);
        this.saveProgress();
      }
    },

    async submitQuiz(isTimeout = false) {
      if (this.isSubmitting) return;

      // Additional validation
      const unanswered = this.totalQuestions - this.answeredQuestions;
      if (!isTimeout && unanswered > 0 && !confirm(`You have ${unanswered} unanswered questions. Submit anyway?`)) {
        return;
      }

      this.isSubmitting = true;
      if (this.timerInterval) {
        clearInterval(this.timerInterval);
      }

      try {
        let totalScore = 0;
        this.currentQuiz.questions.forEach((question, index) => {
          if (this.answers.get(index) === question.correct_answer) {
            totalScore++;
          }
        });

        await api.post('/api/scores', {
          quiz_id: this.currentQuiz.id,
          time_stamp_of_attempt: new Date().toISOString(),
          total_scored: totalScore
        });

        this.clearInProgressQuiz();
        this.startModal.hide();
        await this.fetchQuizzes();

        // Show detailed results
        const percentage = (totalScore / this.totalQuestions) * 100;
        let message = `Quiz Results:\n\n`;
        message += `Score: ${totalScore} out of ${this.totalQuestions}\n`;
        message += `Percentage: ${percentage.toFixed(1)}%\n\n`;
        message += percentage >= 70 ? 'Great job! 🎉' : 'Keep practicing! 💪';
        
        alert(message);

      } catch (error) {
        this.error = 'Failed to submit quiz. Your answers have been saved - please try submitting again.';
        console.error('Error submitting quiz:', error);
      } finally {
        this.isSubmitting = false;
        document.title = 'Quiz Application';
      }
    }
  },

  // ... [Lifecycle hooks remain similar with added progress loading] ...

  beforeUnmount() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
    if (this.currentQuiz) {
      this.saveProgress();
    }
    document.title = 'Quiz Application';
  }
>>>>>>> Stashed changes
};

export default HomeUser;
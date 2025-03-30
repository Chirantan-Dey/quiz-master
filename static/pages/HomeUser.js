const HomeUser = {
  template: `
    <div class="container mt-4">
      <h2>Quizzes</h2>
      <table class="table">
        <thead>
          <tr>
            <th>Quiz ID</th>
            <th>Quiz Name</th>
            <th>Number of Questions</th>
            <th>Date</th>
            <th>Duration (in minutes)</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="quiz in filteredQuizzes" :key="quiz.id" :class="{'table-secondary': isQuizExpired(quiz)}">
            <td>{{quiz.id}}</td>
            <td>{{quiz.name}}</td>
            <td>{{quiz.questions.length}}</td>
            <td>{{formatDate(quiz.date_of_quiz)}}</td>
            <td>{{quiz.time_duration}}</td>
            <td>
              <span v-if="isQuizExpired(quiz)" class="badge bg-secondary">Expired</span>
              <span v-else class="badge bg-success">Available</span>
            </td>
            <td>
              <button class="btn btn-secondary me-2" @click="viewQuiz(quiz)">View</button>
              <button 
                class="btn btn-primary" 
                @click="startQuiz(quiz)"
                :disabled="isQuizExpired(quiz)"
                :title="isQuizExpired(quiz) ? 'This quiz has expired' : ''"
              >Start</button>
            </td>
          </tr>
        </tbody>
      </table>

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
              <p><strong>Status:</strong> 
                <span :class="isQuizExpired(selectedQuiz) ? 'badge bg-secondary' : 'badge bg-success'">
                  {{isQuizExpired(selectedQuiz) ? 'Expired' : 'Available'}}
                </span>
              </p>
              <p><strong>Remarks:</strong> {{selectedQuiz.remarks}}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="modal fade" id="startQuizModal" tabindex="-1" data-bs-backdrop="static">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Quiz</h5>
              <div class="ms-auto">{{formatCountdown}}</div>
            </div>
            <div class="modal-body">
              <div class="row">
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
                
                <div class="col-9">
                  <div v-if="currentQuestion">
                    <p class="h5 mb-4">Question {{currentQuestionIndex + 1}}: {{currentQuestion.question_statement}}</p>
                    <div class="form-check mb-2">
                      <input 
                        type="radio" 
                        class="form-check-input"
                        :id="'q'+currentQuestionIndex+'opt1'"
                        :name="'q'+currentQuestionIndex"
                        :value="currentQuestion.option1"
                        v-model="currentAnswer"
                      >
                      <label class="form-check-label" :for="'q'+currentQuestionIndex+'opt1'">{{currentQuestion.option1}}</label>
                    </div>
                    <div class="form-check mb-4">
                      <input 
                        type="radio" 
                        class="form-check-input"
                        :id="'q'+currentQuestionIndex+'opt2'"
                        :name="'q'+currentQuestionIndex"
                        :value="currentQuestion.option2"
                        v-model="currentAnswer"
                      >
                      <label class="form-check-label" :for="'q'+currentQuestionIndex+'opt2'">{{currentQuestion.option2}}</label>
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
      currentAnswer: '',
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
    },

    filteredQuizzes() {
      const query = this.$store.state.search.query.toLowerCase();
      if (!query) return this.quizzes;
      
      return this.quizzes.filter(quiz => 
        quiz.name.toLowerCase().includes(query) ||
        (quiz.remarks && quiz.remarks.toLowerCase().includes(query)) ||
        (this.chapters[quiz.chapter_id]?.name.toLowerCase().includes(query))
      );
    }
  },

  watch: {
    currentQuestionIndex: {
      immediate: true,
      handler(index) {
        // When question changes, load saved answer if it exists
        this.$nextTick(() => {
          const savedAnswer = this.answers.get(index);
          this.currentAnswer = savedAnswer || '';
        });
      }
    }
  },

  methods: {
    initializeModals() {
      if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap is not loaded');
        return;
      }

      try {
        const viewModalEl = document.getElementById('viewQuizModal');
        const startModalEl = document.getElementById('startQuizModal');
        
        if (viewModalEl) {
          this.viewModal = new bootstrap.Modal(viewModalEl);
        }
        if (startModalEl) {
          this.startModal = new bootstrap.Modal(startModalEl);
        }
      } catch (error) {
        console.error('Error initializing modals:', error);
      }
    },

    isQuizExpired(quiz) {
      if (!quiz || !quiz.date_of_quiz) return true;
      const quizDate = new Date(quiz.date_of_quiz);
      return quizDate < new Date();
    },

    async fetchQuizzes() {
      try {
        const response = await fetch('/api/quizzes', {
          headers: {
            'Authentication-Token': this.$store.state.authToken
          }
        });
        if (!response.ok) {
          throw new Error('Failed to fetch quizzes');
        }
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
        if (!response.ok) {
          throw new Error('Failed to fetch chapters');
        }
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
      if (this.viewModal) {
        this.viewModal.show();
      }
    },

    startQuiz(quiz) {
      if (this.isQuizExpired(quiz)) {
        alert('This quiz has expired and cannot be attempted.');
        return;
      }
      this.currentQuiz = quiz;
      this.currentQuestionIndex = 0;
      this.answers = new Map();
      this.currentAnswer = '';
      this.startTimer(quiz.time_duration);
      if (this.startModal) {
        this.startModal.show();
      }
    },

    startTimer(duration) {
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
      }, 1000);
    },

    showQuestion(index) {
      this.currentQuestionIndex = index;
    },

    isAnswered(index) {
      return this.answers.has(index);
    },

    saveAndNext() {
      if (this.currentAnswer) {
        // Save the current answer
        this.answers.set(this.currentQuestionIndex, this.currentAnswer);
        
        // Move to next question
        const nextIndex = (this.currentQuestionIndex + 1) % this.currentQuiz.questions.length;
        this.currentQuestionIndex = nextIndex;
      }
    },

    async submitQuiz() {
      if (this.timerInterval) {
        clearInterval(this.timerInterval);
      }

      if (this.isQuizExpired(this.currentQuiz)) {
        alert('This quiz has expired. Your submission cannot be accepted.');
        this.startModal.hide();
        return;
      }

      // Calculate score
      let totalScore = 0;
      this.currentQuiz.questions.forEach((question, index) => {
        if (this.answers.get(index) === question.correct_answer) {
          totalScore++;
        }
      });

      try {
        const response = await fetch('/api/scores', {
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

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.message || 'Failed to submit quiz');
        }

        this.startModal.hide();
      } catch (error) {
        console.error('Error submitting quiz:', error);
        alert(error.message || 'Failed to submit quiz. Please try again.');
      }
    }
  },

  async mounted() {
    try {
      await Promise.all([
        this.fetchQuizzes(),
        this.fetchChapters()
      ]);

      // Wait for Vue to update the DOM
      this.$nextTick(() => {
        setTimeout(() => {
          this.initializeModals();
        }, 100);
      });
    } catch (error) {
      console.error('Error in mounted:', error);
    }
  },

  beforeUnmount() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  }
};

export default HomeUser;
const ScoreUser = {
  template: `
    <div class="container mt-4">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>Quiz Scores</h2>
        <button class="btn btn-primary" @click="refreshData" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-1" role="status"></span>
          Refresh
        </button>
      </div>

      <!-- Error Alert -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = null"></button>
      </div>

      <!-- Content -->
      <div v-if="loading && !error" class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
      
      <div v-else>
        <div v-if="userScores.length === 0" class="alert alert-info">
          No scores found. Take some quizzes to see your scores here!
        </div>
        <table v-else class="table table-striped table-hover">
          <thead>
            <tr>
              <th @click="sort('quiz_id')" style="cursor: pointer">
                Quiz Name
                <i v-if="sortField === 'quiz_id'" 
                   :class="sortDirection === 'asc' ? 'bi bi-arrow-up' : 'bi bi-arrow-down'"></i>
              </th>
              <th>Questions</th>
              <th @click="sort('time_stamp_of_attempt')" style="cursor: pointer">
                Date
                <i v-if="sortField === 'time_stamp_of_attempt'" 
                   :class="sortDirection === 'asc' ? 'bi bi-arrow-up' : 'bi bi-arrow-down'"></i>
              </th>
              <th @click="sort('total_scored')" style="cursor: pointer">
                Score
                <i v-if="sortField === 'total_scored'" 
                   :class="sortDirection === 'asc' ? 'bi bi-arrow-up' : 'bi bi-arrow-down'"></i>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="score in sortedScores" :key="score.id">
              <td>
                <span v-if="quizzes[score.quiz_id]">
                  {{ quizzes[score.quiz_id].name || 'Quiz #' + score.quiz_id }}
                </span>
                <span v-else class="text-muted">Loading...</span>
              </td>
              <td>{{ getQuestionCount(score.quiz_id) }}</td>
              <td>{{ formatDate(score.time_stamp_of_attempt) }}</td>
              <td>
                <span :class="getScoreClass(score)">
                  {{ score.total_scored }}/{{ getQuestionCount(score.quiz_id) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  data() {
    return {
      loading: true,
      error: null,
      scores: [],
      quizzes: {},
      sortField: 'time_stamp_of_attempt',
      sortDirection: 'desc'
    };
  },
  computed: {
    userScores() {
      if (!this.$store.state.user?.id) return [];
      return this.scores.filter(score => score.user_id === this.$store.state.user.id);
    },
    sortedScores() {
      return [...this.userScores].sort((a, b) => {
        let aVal = a[this.sortField];
        let bVal = b[this.sortField];
        
        // Handle dates
        if (this.sortField === 'time_stamp_of_attempt') {
          aVal = aVal ? new Date(aVal).getTime() : 0;
          bVal = bVal ? new Date(bVal).getTime() : 0;
        }
        
        const multiplier = this.sortDirection === 'asc' ? 1 : -1;
        return aVal > bVal ? multiplier : -multiplier;
      });
    }
  },
  methods: {
    async fetchScores() {
      try {
        const response = await fetch('/api/scores', {
          headers: {
            'Authorization': `Bearer ${this.$store.state.authToken}`
          }
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        this.scores = data;
      } catch (error) {
        this.error = 'Failed to load scores. Please try again later.';
        console.error('Error fetching scores:', error);
      }
    },
    async fetchQuizzes() {
      try {
        const response = await fetch('/api/quizzes', {
          headers: {
            'Authorization': `Bearer ${this.$store.state.authToken}`
          }
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const quizzes = await response.json();
        this.quizzes = quizzes.reduce((acc, quiz) => {
          acc[quiz.id] = quiz;
          return acc;
        }, {});
      } catch (error) {
        this.error = 'Failed to load quiz details. Please try again later.';
        console.error('Error fetching quizzes:', error);
      }
    },
    formatDate(timestamp) {
      if (!timestamp) return 'N/A';
      try {
        return new Date(timestamp).toLocaleString();
      } catch (e) {
        console.error('Date parsing error:', e);
        return 'Invalid Date';
      }
    },
    getQuestionCount(quizId) {
      const quiz = this.quizzes[quizId];
      return quiz?.questions?.length || 'N/A';
    },
    getScoreClass(score) {
      const total = this.getQuestionCount(score.quiz_id);
      if (total === 'N/A') return '';
      const percentage = (score.total_scored / total) * 100;
      if (percentage >= 75) return 'text-success';
      if (percentage >= 50) return 'text-warning';
      return 'text-danger';
    },
    sort(field) {
      if (this.sortField === field) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortField = field;
        this.sortDirection = 'desc';
      }
    },
    async refreshData() {
      this.loading = true;
      this.error = null;
      try {
        await Promise.all([
          this.fetchScores(),
          this.fetchQuizzes()
        ]);
      } finally {
        this.loading = false;
      }
    }
  },
  async mounted() {
    await this.refreshData();
  }
};

export default ScoreUser;
const ScoreUser = {
  template: `
    <div class="container mt-4">
      <div class="mb-4">
        <h2>Quiz Scores</h2>
      </div>

      <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = null"></button>
      </div>

      <div v-if="!loading || error">
        <div v-if="filteredScores.length === 0" class="alert alert-info">
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
                <span v-else>Quiz #{{ score.quiz_id }}</span>
              </td>
              <td>{{ getQuestionCount(score.quiz_id) }}</td>
              <td>{{ formatDate(score.time_stamp_of_attempt) }}</td>
              <td>{{ score.total_scored }}/{{ getQuestionCount(score.quiz_id) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  data() {
    return {
      loading: false,
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
    filteredScores() {
      const query = this.$store.state.search.query.toLowerCase();
      if (!query) return this.userScores;
      
      return this.userScores.filter(score => {
        const quiz = this.quizzes[score.quiz_id];
        if (!quiz) return false;

        if (quiz.name.toLowerCase().includes(query)) return true;
        if (score.total_scored.toString().includes(query)) return true;
        if (this.formatDate(score.time_stamp_of_attempt).toLowerCase().includes(query)) return true;
        if (quiz.chapter_id && this.chapters && this.chapters[quiz.chapter_id]) {
          if (this.chapters[quiz.chapter_id].name.toLowerCase().includes(query)) return true;
        }

        return false;
      });
    },
    sortedScores() {
      return [...this.filteredScores].sort((a, b) => {
        let aVal = a[this.sortField];
        let bVal = b[this.sortField];
        
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
            'Authentication-Token': this.$store.state.authToken
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
            'Authentication-Token': this.$store.state.authToken
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
    sort(field) {
      if (this.sortField === field) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortField = field;
        this.sortDirection = 'desc';
      }
    }
  },
  async mounted() {
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
};

export default ScoreUser;
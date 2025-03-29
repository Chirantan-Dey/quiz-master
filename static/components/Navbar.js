const Navbar = {
  template: `
    <nav class="navbar navbar-dark bg-dark h3 w-100">
      <div class="container d-flex justify-content-between">
        <div class="d-flex align-items-center">
          <router-link :to="getHomeLink" class="navbar-brand px-3 mb-0">Home</router-link>
          <span class="text-light">|</span>
          <router-link :to="getQuizLink" class="navbar-brand px-3 mb-0">{{ isAdmin ? 'Quiz' : 'Score' }}</router-link>
          <span class="text-light">|</span>
          <router-link :to="getSummaryLink" class="navbar-brand px-3 mb-0">Summary</router-link>
        </div>
        <div class="d-flex align-items-center">
          <div class="input-group mx-3" v-if="showSearch">
            <input 
              type="text" 
              class="form-control" 
              v-model="searchQuery"
              :placeholder="searchPlaceholder"
              @keyup.enter="handleSearch"
            >
            <div class="input-group-append">
              <button 
                class="btn btn-primary" 
                type="button" 
                @click="handleSearch"
              >
                Search
              </button>
              <button 
                v-if="hasSearch"
                class="btn btn-secondary" 
                type="button" 
                @click="clearSearch"
              >
                Clear
              </button>
            </div>
          </div>
          <a :href="logoutURL" class="navbar-brand px-3 mb-0">Logout</a>
        </div>
      </div>
    </nav>
  `,
  data() {
    return {
      loggedIn: false,
      logoutURL: window.location.origin + "/logout",
      searchQuery: ""
    };
  },
  computed: {
    isAdmin() {
      return this.$store.state.user && this.$store.state.user.roles.length === 1 && this.$store.state.user.roles[0].name === 'admin';
    },
    getHomeLink() {
      return this.isAdmin ? '/home-admin' : '/home-user';
    },
    getQuizLink() {
      return this.isAdmin ? '/quiz-admin' : '/score-user';
    },
    getSummaryLink() {
      return this.isAdmin ? '/summary-admin' : '/summary-user';
    },
    showSearch() {
      return !['/', '/login', '/signup'].includes(this.$route.path);
    },
    hasSearch() {
      return this.searchQuery.trim().length > 0;
    },
    searchPlaceholder() {
      const path = this.$route.path;
      const placeholders = {
        'home': 'Search subjects and chapters...',
        'quiz': 'Search quizzes and questions...',
        'score': 'Search scores...',
        'summary': 'Search results...'
      };
      
      for (const [key, value] of Object.entries(placeholders)) {
        if (path.includes(key)) {
          return value;
        }
      }
      return 'Search...';
    }
  },
  methods: {
    handleSearch() {
      if (this.searchQuery.trim()) {
        this.$store.dispatch('search', this.searchQuery.trim());
      }
    },
    clearSearch() {
      this.searchQuery = '';
      this.$store.dispatch('clearSearch');
    }
  },
  watch: {
    '$route'() {
      this.clearSearch();
    }
  }
};

export default Navbar;

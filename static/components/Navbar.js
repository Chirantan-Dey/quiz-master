const Navbar = {
  template: `
    <nav class="navbar navbar-dark bg-dark h3 w-100">
      <div class="container d-flex justify-content-between">
        <div class="d-flex align-items-center">
          <router-link :to="getHomeLink" class="navbar-brand px-3 mb-0">Home</router-link>
          <span class="text-light">|</span>
          <router-link :to="getQuizLink" class="navbar-brand px-3 mb-0">Quiz</router-link>
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
    getHomeLink() {
      return this.$store.state.user && this.$store.state.user.roles.length === 1 && this.$store.state.user.roles[0].name === 'admin' ? '/home-admin' : '/home-user';
    },
    getQuizLink() {
      return this.$store.state.user && this.$store.state.user.roles.length === 1 && this.$store.state.user.roles[0].name === 'admin' ? '/quiz-admin' : '/quiz-user';
    },
    getSummaryLink() {
      return this.$store.state.user && this.$store.state.user.roles.length === 1 && this.$store.state.user.roles[0].name === 'admin' ? '/summary-admin' : '/summary-user';
    },
    showSearch() {
      // Don't show search on login/signup pages
      return !['/', '/login', '/signup'].includes(this.$route.path);
    },
    hasSearch() {
      return this.searchQuery.trim().length > 0;
    },
    searchPlaceholder() {
      const path = this.$route.path;
      if (path.includes('home')) {
        return 'Search subjects and chapters...';
      } else if (path.includes('quiz')) {
        return 'Search quizzes...';
      } else if (path.includes('summary')) {
        return 'Search results...';
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
    // Clear search when route changes
    '$route'() {
      this.clearSearch();
    }
  }
};

export default Navbar;

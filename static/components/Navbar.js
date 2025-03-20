import { api } from '../utils/api.js';
import store from '../utils/store.js';

const Navbar = {
  template: `
<<<<<<< Updated upstream
        <nav class= "h3 w-auto d-flex justify-content-around ">
            <router-link :to="getHomeLink">Home</router-link>
            <router-link :to="getQuizLink">Quiz</router-link>
            <router-link :to="getSummaryLink">Summary</router-link>
            <a :href="logoutURL">Logout</a>
        </nav>
    `,
  data() {
      return {
        loggedIn: false,
        logoutURL: window.location.origin + "/logout",
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
      }
=======
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
                :disabled="isSearching"
              >
                {{ isSearching ? 'Searching...' : 'Search' }}
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
          <router-link to="/logout" class="navbar-brand px-3 mb-0">Logout</router-link>
        </div>
      </div>
      <div v-if="error" class="alert alert-danger alert-dismissible fade show m-0" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = null"></button>
      </div>
    </nav>
  `,
  data() {
    return {
      searchQuery: "",
      isSearching: false,
      error: null
    };
  },
  computed: {
    isAdmin() {
      return this.$store.getters.userRoles.some(role => role.name === 'admin');
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
      // Don't show search on login/signup/logout pages
      return !['/', '/login', '/register', '/logout'].includes(this.$route.path);
    },
    hasSearch() {
      return this.searchQuery.trim().length > 0;
    },
    searchPlaceholder() {
      const path = this.$route.path;
      const placeholders = {
        'home': 'Search subjects and chapters...',
        'quiz': 'Search quizzes...',
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
    async handleSearch() {
      if (!this.searchQuery.trim()) return;

      this.error = null;
      this.isSearching = true;

      try {
        await this.$store.dispatch('search', this.searchQuery.trim());
      } catch (error) {
        this.error = 'Search failed. Please try again.';
        console.error('Search error:', error);
      } finally {
        this.isSearching = false;
      }
    },
    clearSearch() {
      this.searchQuery = '';
      this.error = null;
      this.$store.dispatch('clearSearch');
>>>>>>> Stashed changes
    }
};

export default Navbar;

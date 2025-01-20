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
        <a :href="logoutURL" class="navbar-brand px-3 mb-0">Logout</a>
      </div>
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
  }
};

export default Navbar;

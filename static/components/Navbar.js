const Navbar = {
  template: `
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
        return this.$store.state.user && this.$store.state.user.role === 'admin' ? '/home-admin' : '/home-user';
      },
      getQuizLink() {
        return this.$store.state.user && this.$store.state.user.role === 'admin' ? '/quiz-admin' : '/quiz-user';
      },
      getSummaryLink() {
          return this.$store.state.user && this.$store.state.user.role === 'admin' ? '/summary-admin' : '/summary-user';
      }
    }
};

export default Navbar;

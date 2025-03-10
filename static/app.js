// import components
import router from "./utils/router.js";
import Navbar from "./components/Navbar.js";
import store from "./utils/store.js";

new Vue({
  el: "#app",
  router,
  store,
  components: { Navbar },
  computed: {
    showNavbar() {
      return !["/", "/login","/register"].includes(this.$route.path);
    },
  },
  template: `
        <div class="vw-100 vh-100 ">
        <Navbar v-if="showNavbar"/>
        <router-view class = "h-75 w-100 "></router-view>
        </div>
    `,
});

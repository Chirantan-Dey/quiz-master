import router from "./utils/router.js";
import Navbar from "./components/Navbar.js";
import store from "./utils/store.js";
import Notification from "./components/Notification.js";
import { OfflineMixin } from "./utils/offline.js";

new Vue({
  mixins: [OfflineMixin],
  el: "#app",
  router,
  store,
  components: { Navbar, Notification },
  computed: {
    showNavbar() {
      return !["/", "/login","/register"].includes(this.$route.path);
    }
  },
  template: `
    <div class="vw-100 vh-100">
      <div v-if="isOffline" class="alert alert-warning text-center mb-0" role="alert">
        You are currently offline. Some features may be limited.
      </div>
      <Navbar v-if="showNavbar"/>
      <router-view class="h-75 w-100"></router-view>
      <Notification />
    </div>
  `,
});

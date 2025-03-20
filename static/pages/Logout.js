import router from "../utils/router.js";
import { api } from "../utils/api.js";

const Logout = {
  template: `
    <div class="d-flex justify-content-center align-items-center vh-100">
      <div class="text-center">
        <h3>Logging out...</h3>
        <div v-if="error" class="alert alert-danger mt-3">
          {{ error }}
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      error: null
    };
  },
  async created() {
    try {
      // Clear all frontend auth data first
      this.$store.commit("logout");
      
      // Notify backend (don't wait for response)
      fetch("/logout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        credentials: "same-origin"
      }).catch(console.error); // Log but don't block on errors

      // Always redirect to login
      router.push("/login");
    } catch (error) {
      this.error = "Logout failed. Please try again.";
      console.error("Logout error:", error);
      
      // Redirect after short delay even if there's an error
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    }
  }
};

export default Logout;

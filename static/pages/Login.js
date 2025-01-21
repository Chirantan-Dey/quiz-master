import router from "../utils/router.js";

const Login = {
  template: `
    <div class="d-flex justify-content-center align-items-center vh-100">
      <div class="card shadow p-4 border rounded-3">
        <h3 class="card-title text-center mb-4">Login</h3>
        <form @submit.prevent="submitInfo">
          <div class="form-group mb-3">
            <input 
              v-model="email" 
              type="email" 
              class="form-control" 
              placeholder="Email" 
              required
            />
          </div>
          <div class="form-group mb-4">
            <input 
              v-model="password" 
              type="password" 
              class="form-control" 
              placeholder="Password" 
              required
            />
          </div>
          <div v-if="error" class="alert alert-danger mb-3">
            {{ error }}
          </div>
          <button 
            type="submit" 
            class="btn btn-primary w-100"
            :disabled="isLoading"
          >
            Login
          </button>
          <button type="button" class="btn btn-link w-100" @click="goToSignup">Sign Up</button>
        </form>
      </div>
    </div>
  `,
  data() {
    return {
      email: "",
      password: "",
      error: "",
      isLoading: false
    };
  },
  methods: {
    async submitInfo() {
      this.error = "";
      this.isLoading = true;
      
      try {
        const res = await fetch("/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email: this.email, password: this.password }),
          credentials: "same-origin",
        });

        const data = await res.json();

        if (res.ok) {
          this.$store.commit("setAuthToken", data.access_token);
          this.$store.commit("setUser", data.user);
          if (data.user.roles.some(role => role.name === 'admin')) {
            router.push("/home-admin");
          } else {
            router.push("/home-user");
          }
        } else {
          this.error = data.message || "Login failed. Please try again.";
        }
      } catch (error) {
        this.error = "An error occurred. Please try again.";
        console.error("Login error:", error);
      } finally {
        this.isLoading = false;
      }
    },
    goToSignup() {
      this.$router.push("/register");
    }
  },
};

export default Login;

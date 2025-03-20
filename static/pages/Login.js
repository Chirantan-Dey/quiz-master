import router from "../utils/router.js";
import { api } from "../utils/api.js";

const Login = {
  template: `
    <div class="d-flex justify-content-center align-items-center vh-100">
      <div class="card shadow p-4 border rounded-3 ">
        <h3 class="card-title text-center mb-4">Login</h3>
<<<<<<< Updated upstream
        <div class="form-group mb-3">
          <input v-model="email" type="email" class="form-control" placeholder="Email" required/>
        </div>
        <div class="form-group mb-4">
          <input v-model="password" type="password" class="form-control" placeholder="Password" required/>
        </div>
        <button class="btn btn-primary w-100" @click="submitInfo">Submit</button>
        <button class="btn btn-link w-100" @click="goToSignup">Sign Up</button>
=======
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
            {{ isLoading ? 'Logging in...' : 'Login' }}
          </button>
          <button type="button" class="btn btn-link w-100" @click="goToSignup">Sign Up</button>
        </form>
>>>>>>> Stashed changes
      </div>
    </div>
  `,
  data() {
    return {
      email: "",
      password: "",
    };
  },
  methods: {
    async submitInfo() {
<<<<<<< Updated upstream
      const origin = window.location.origin;
      const url = `${origin}/`;
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: this.email, password: this.password }),
        credentials: "same-origin", // Include credentials (cookies) with the request
      });

      if (res.ok) {
        const data = await res.json();
        console.log(data);
        console.log("User roles:", JSON.stringify(data.user.roles));
        // Handle successful login, e.g., redirect or store token
        this.$store.commit("setAuthToken", data.access_token);
        this.$store.commit("setUser", data.user);
=======
      this.error = "";
      this.isLoading = true;
      
      try {
        const data = await api.login({
          email: this.email,
          password: this.password
        });

        // Store auth data
        this.$store.commit("setAuthToken", data.access_token);
        this.$store.commit("setUser", data.user);

        // Redirect based on role
>>>>>>> Stashed changes
        if (data.user.roles.some(role => role.name === 'admin')) {
          router.push("/home-admin");
        } else {
          router.push("/home-user");
        }
<<<<<<< Updated upstream
      } else {
        const errorData = await res.json();
        console.error("Login failed:", errorData);
        // Handle login error
=======
      } catch (error) {
        this.error = error.message || "Login failed. Please try again.";
        console.error("Login error:", error);
      } finally {
        this.isLoading = false;
>>>>>>> Stashed changes
      }
    },
    goToSignup() {
      this.$router.push("/register");
    }
  },
};

export default Login;

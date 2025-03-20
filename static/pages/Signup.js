import router from "../utils/router.js";
import { api } from "../utils/api.js";

const Signup = {
  template: `
    <div class="d-flex justify-content-center align-items-center vh-100">
      <div class="card shadow p-4 border rounded-3 ">
        <h3 class="card-title text-center mb-4">Sign Up</h3>
<<<<<<< Updated upstream
        <div class="form-group mb-3">
          <input v-model="email" type="email" class="form-control" placeholder="Email" required/>
        </div>
        <div class="form-group mb-3">
          <input v-model="password" type="password" class="form-control" placeholder="Password" required/>
        </div>
        <div class="form-group mb-4">
          <input v-model="confirmPassword" type="password" class="form-control" placeholder="Confirm Password" required/>
        </div>
        <button class="btn btn-primary w-100" @click="submitInfo">Submit</button>
        <button class="btn btn-link w-100" @click="goToLogin">Login</button>
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
          <div class="form-group mb-3">
            <input 
              v-model="fullName" 
              type="text" 
              class="form-control" 
              placeholder="Full Name" 
              required
            />
          </div>
          <div class="form-group mb-3">
            <input 
              v-model="qualification" 
              type="text" 
              class="form-control" 
              placeholder="Qualification" 
              required
            />
          </div>
          <div class="form-group mb-3">
            <input 
              v-model="dob" 
              type="date" 
              class="form-control" 
              required
            />
          </div>
          <div class="form-group mb-3">
            <input 
              v-model="password" 
              type="password" 
              class="form-control" 
              placeholder="Password" 
              required
            />
          </div>
          <div class="form-group mb-4">
            <input 
              v-model="confirmPassword" 
              type="password" 
              class="form-control" 
              placeholder="Confirm Password" 
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
            {{ isLoading ? 'Signing up...' : 'Sign Up' }}
          </button>
          <button type="button" class="btn btn-link w-100" @click="goToLogin">Login</button>
        </form>
>>>>>>> Stashed changes
      </div>
    </div>
  `,
  data() {
    return {
      email: "",
      password: "",
      confirmPassword: "",
    };
  },
  methods: {
    async submitInfo() {
<<<<<<< Updated upstream
      const origin = window.location.origin;
      const url = `${origin}/register`;
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: this.email, password: this.password, role: 'stud' }),
        credentials: "same-origin", // Include credentials (cookies) with the request
      });

      if (res.ok) {
        const data = await res.json();
        console.log(data);
        console.log("User roles:", JSON.stringify(data.user.roles));
        // Handle successful login, e.g., redirect or store token
        this.$store.commit("setAuthToken", data.access_token);
        this.$store.commit("setUser", data.user);
        if (data.user.roles.some(role => role.name === 'admin')) {
          router.push("/home-admin");
        } else {
          router.push("/home-user");
        }
      } else {
        const errorData = await res.json();
        console.error("Login failed:", errorData);
        // Handle login error
=======
      this.error = "";
      
      if (this.password !== this.confirmPassword) {
        this.error = "Passwords do not match";
        return;
      }

      this.isLoading = true;
      
      try {
        const data = await api.register({ 
          email: this.email,
          full_name: this.fullName,
          qualification: this.qualification,
          dob: this.dob,
          password: this.password,
          role: 'user'
        });

        // Store auth data if registration includes auto-login
        if (data.access_token) {
          this.$store.commit("setAuthToken", data.access_token);
          this.$store.commit("setUser", data.user);

          // Redirect based on role
          if (data.user.roles.some(role => role.name === 'admin')) {
            router.push("/home-admin");
          } else {
            router.push("/home-user");
          }
        } else {
          // If registration doesn't include auto-login, redirect to login page
          this.$router.push("/login");
        }
      } catch (error) {
        this.error = error.message || "Registration failed. Please try again.";
        console.error("Registration error:", error);
      } finally {
        this.isLoading = false;
>>>>>>> Stashed changes
      }
    },
    goToLogin() {
      this.$router.push("/login");
    }
  },
};

export default Signup;

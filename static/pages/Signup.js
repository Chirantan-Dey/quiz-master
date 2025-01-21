import router from "../utils/router.js";

const Signup = {
  template: `
    <div class="d-flex justify-content-center align-items-center vh-100">
      <div class="card shadow p-4 border rounded-3">
        <h3 class="card-title text-center mb-4">Sign Up</h3>
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
            Sign Up
          </button>
          <button type="button" class="btn btn-link w-100" @click="goToLogin">Login</button>
        </form>
      </div>
    </div>
  `,
  data() {
    return {
      email: "",
      fullName: "",
      qualification: "",
      dob: "",
      password: "",
      confirmPassword: "",
      error: "",
      isLoading: false
    };
  },
  methods: {
    async submitInfo() {
      this.error = "";
      
      if (this.password !== this.confirmPassword) {
        this.error = "Passwords do not match";
        return;
      }

      this.isLoading = true;
      
      try {
        const res = await fetch("/register", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ 
            email: this.email,
            full_name: this.fullName,
            qualification: this.qualification,
            dob: this.dob,
            password: this.password,
            role: 'user'
          }),
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
          this.error = data.message || "Registration failed. Please try again.";
        }
      } catch (error) {
        this.error = "An error occurred. Please try again.";
        console.error("Registration error:", error);
      } finally {
        this.isLoading = false;
      }
    },
    goToLogin() {
      this.$router.push("/login");
    }
  },
};

export default Signup;

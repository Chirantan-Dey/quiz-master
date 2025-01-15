import router from "../utils/router.js";

const Signup = {
  template: `
    <div class="d-flex justify-content-center align-items-center vh-100">
      <div class="card shadow p-4 border rounded-3 ">
        <h3 class="card-title text-center mb-4">Sign Up</h3>
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
        if (data.user.roles.includes('admin')) {
          router.push("/home-admin");
        } else {
          router.push("/home-user");
        }
      } else {
        const errorData = await res.json();
        console.error("Login failed:", errorData);
        // Handle login error
      }
    },
    goToLogin() {
      this.$router.push("/login");
    }
  },
};

export default Signup;

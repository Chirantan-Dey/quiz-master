import router from "../utils/router.js";

const Logout = {
  template: `
    <div> 
        <h1>Logging out...</h1>
    </div>
    `,
  created() {
    this.$store.commit("logout");
    router.push("/login");
  }
};

export default Logout;

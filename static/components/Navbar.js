const Navbar = {
  template: `
        <nav class= "h3 w-auto d-flex justify-content-around ">
            <nav class="h3 w-auto d-flex justify-content-around">
            <router-link to='/'>Home</router-link>
            <router-link to='/quiz'>Quiz</router-link>
            <router-link to='/summary'>Summary</router-link>
            <a :href="logoutURL">Logout</a>
        
        </nav>
    `,
  data() {
    return {
      loggedIn: false,
      logoutURL: window.location.origin + "/logout",
    };
  },
};

export default Navbar;

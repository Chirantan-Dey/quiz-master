const store = new Vuex.Store({
  state: {
    authToken: localStorage.getItem("authToken") || "",
    test: "to test vuex working",
    user: JSON.parse(localStorage.getItem("user")) || null,
    search: {
      query: ""
    }
  },
  mutations: {
    setAuthToken(state, token) {
      state.authToken = token;
      localStorage.setItem("authToken", token);
    },
    setUser(state, user) {
      state.user = { ...user, roles: user.roles || [] };
      localStorage.setItem("user", JSON.stringify(state.user));
    },
    logout(state) {
      state.authToken = "";
      localStorage.removeItem("authToken");
      localStorage.removeItem("user");
      state.user = null;
    },
    setSearchQuery(state, query) {
      state.search.query = query;
    }
  },
  actions: {
    search({ commit }, query) {
      commit('setSearchQuery', query);
    },
    clearSearch({ commit }) {
      commit('setSearchQuery', '');
    }
  },
  getters: {
    isLoggedIn: (state) => !!state.authToken,
    userRoles: (state) => state.user?.roles || [],
    searchQuery: (state) => state.search.query
  },
});

export default store;

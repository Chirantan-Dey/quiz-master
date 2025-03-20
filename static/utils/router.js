import Login from "../pages/Login.js";
import HomeAdmin from "../pages/HomeAdmin.js";
import HomeUser from "../pages/HomeUser.js";
import QuizAdmin from "../pages/QuizAdmin.js";
import QuizUser from "../pages/QuizUser.js";
import Signup from "../pages/Signup.js";
import Logout from "../pages/Logout.js";
import SummaryAdmin from "../pages/SummaryAdmin.js";
import SummaryUser from "../pages/SummaryUser.js";
<<<<<<< Updated upstream
=======
import ScoreUser from "../pages/ScoreUser.js";
import store from "./store.js";

// Route groups
const publicRoutes = ['/', '/login', '/register'];
const adminRoutes = ['/home-admin', '/quiz-admin', '/summary-admin'];
const userRoutes = ['/home-user', '/summary-user', '/score-user'];
>>>>>>> Stashed changes

const routes = [
  {
    path: "/",
    component: Login,
  },
  {
    path: "/login",
    component: Login,
  },
  {
    path: "/home-admin",
    component: HomeAdmin,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: "/home-user",
    component: HomeUser,
    meta: { requiresAuth: true }
  },
  {
    path: "/quiz-admin",
    component: QuizAdmin,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: "/quiz-user",
    component: QuizUser,
  },
  {
    path: "/register",
    component: Signup,
  },
  {
    path: "/logout",
    component: Logout,
    meta: { requiresAuth: true }
  },
  {
    path: "/summary-admin",
    component: SummaryAdmin,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: "/summary-user",
    component: SummaryUser,
    meta: { requiresAuth: true }
  },
<<<<<<< Updated upstream
=======
  {
    path: "/score-user",
    component: ScoreUser,
    meta: { requiresAuth: true }
  },
>>>>>>> Stashed changes
];

const router = new VueRouter({
  routes,
});

// Navigation guard
router.beforeEach((to, from, next) => {
  const isLoggedIn = store.getters.isLoggedIn;
  const isAdmin = store.getters.userRoles.some(role => role.name === 'admin');
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin);

  // Handle public routes
  if (publicRoutes.includes(to.path)) {
    if (isLoggedIn) {
      // Redirect logged-in users away from auth pages
      return next(isAdmin ? '/home-admin' : '/home-user');
    }
    return next();
  }

  // Handle protected routes
  if (requiresAuth) {
    if (!isLoggedIn) {
      // Redirect to login if not authenticated
      return next('/login');
    }

    if (requiresAdmin && !isAdmin) {
      // Redirect non-admin users trying to access admin routes
      return next('/home-user');
    }

    if (!requiresAdmin && isAdmin && userRoutes.includes(to.path)) {
      // Redirect admin users trying to access user routes
      return next('/home-admin');
    }
  }

  next();
});

export default router;

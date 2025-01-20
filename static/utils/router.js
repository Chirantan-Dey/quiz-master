import Login from "../pages/Login.js";
import HomeAdmin from "../pages/HomeAdmin.js";
import HomeUser from "../pages/HomeUser.js";
import QuizAdmin from "../pages/QuizAdmin.js";
import Signup from "../pages/Signup.js";
import Logout from "../pages/Logout.js";
import SummaryAdmin from "../pages/SummaryAdmin.js";
import SummaryUser from "../pages/SummaryUser.js";
import ScoreUser from "../pages/ScoreUser.js";

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
  },
  {
    path: "/home-user",
    component: HomeUser,
  },
  {
    path: "/quiz-admin",
    component: QuizAdmin,
  },
  {
    path: "/register",
    component: Signup,
  },
  {
    path: "/logout",
    component: Logout,
  },
  {
    path: "/summary-admin",
    component: SummaryAdmin,
  },
  {
    path: "/summary-user",
    component: SummaryUser,
  },
  {
    path: "/score-user",
    component: ScoreUser,
  },
];

const router = new VueRouter({
  routes,
});

export default router;

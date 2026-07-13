window.AppTemplate = `
  <div v-cloak>
    <nav class="navbar navbar-expand-lg sticky-top border-bottom shadow-sm" :class="roleNavClass">
      <div class="container-fluid px-3 px-lg-4">
        <a class="navbar-brand fw-bold" href="#" @click.prevent="go('home')"
          >Placement Portal</a
        >
        <span v-if="user && user.role === 'admin'" class="ms-4 fw-semibold">Admin Dashboard</span>
        <span v-else-if="user && user.role === 'company'" class="ms-4 fw-semibold">Company Dashboard</span>
        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#mainNav"
        >
          <span class="navbar-toggler-icon"></span>
        </button>
        <div id="mainNav" class="collapse navbar-collapse">
          <div class="navbar-nav ms-auto align-items-lg-center gap-lg-2">
            <template v-if="user">
              <button
                class="btn btn-link nav-link"
                :class="[navItemClass('dashboard'), { active: page === 'dashboard' }]"
                @mouseenter="hoveredNav = 'dashboard'"
                @mouseleave="hoveredNav = ''"
                @click="go('dashboard')"
              >
                Home
              </button>
              <button
                v-if="user && user.role === 'admin'"
                class="btn btn-link nav-link"
                :class="[navItemClass('admin-companies'), { active: page === 'admin-companies' }]"
                @mouseenter="hoveredNav = 'admin-companies'"
                @mouseleave="hoveredNav = ''"
                @click="go('admin-companies')"
              >
                Companies
              </button>
              <button
                v-if="user && user.role === 'admin'"
                class="btn btn-link nav-link"
                :class="[navItemClass('admin-students'), { active: page === 'admin-students' }]"
                @mouseenter="hoveredNav = 'admin-students'"
                @mouseleave="hoveredNav = ''"
                @click="go('admin-students')"
              >
                Students
              </button>
              <button
                v-if="user && user.role === 'admin'"
                class="btn btn-link nav-link"
                :class="[navItemClass('admin-drives'), { active: page === 'admin-drives' }]"
                @mouseenter="hoveredNav = 'admin-drives'"
                @mouseleave="hoveredNav = ''"
                @click="go('admin-drives')"
              >
                Drives
              </button>
              <button
                v-if="user && user.role === 'admin'"
                class="btn btn-link nav-link"
                :class="[navItemClass('admin-applications'), { active: page === 'admin-applications' }]"
                @mouseenter="hoveredNav = 'admin-applications'"
                @mouseleave="hoveredNav = ''"
                @click="go('admin-applications')"
              >
                Applications
              </button>
              <button
                v-if="user && user.role === 'company'"
                class="btn btn-link nav-link"
                :class="[navItemClass('company-drives'), { active: page === 'company-drives' }]"
                @mouseenter="hoveredNav = 'company-drives'"
                @mouseleave="hoveredNav = ''"
                @click="go('company-drives')"
              >
                Drives
              </button>
              <button
                v-if="user && user.role === 'company'"
                class="btn btn-link nav-link"
                :class="[navItemClass('company-applications'), { active: page === 'company-applications' }]"
                @mouseenter="hoveredNav = 'company-applications'"
                @mouseleave="hoveredNav = ''"
                @click="go('company-applications')"
              >
                Applicants
              </button>
              <button
                v-if="user && user.role === 'student'"
                class="btn btn-link nav-link"
                :class="[navItemClass('student-drives'), { active: page === 'student-drives' }]"
                @mouseenter="hoveredNav = 'student-drives'"
                @mouseleave="hoveredNav = ''"
                @click="go('student-drives')"
              >
                Find Jobs
              </button>
              <button
                v-if="user && user.role === 'student'"
                class="btn btn-link nav-link"
                :class="[navItemClass('student-applications'), { active: page === 'student-applications' }]"
                @mouseenter="hoveredNav = 'student-applications'"
                @mouseleave="hoveredNav = ''"
                @click="go('student-applications')"
              >
                My Applications
              </button>
              <button
                v-if="user && user.role !== 'admin'"
                class="btn btn-link nav-link"
                :class="[navItemClass('profile'), { active: page === 'profile' }]"
                @mouseenter="hoveredNav = 'profile'"
                @mouseleave="hoveredNav = ''"
                @click="go('profile')"
              >
                Profile
              </button>
              <button
                v-if="user && user.role !== 'company'"
                class="btn btn-outline-secondary btn-sm"
                type="button"
                title="Open MailHog"
                @click="openMailhog"
              >
                Inbox
              </button>
              <button
                class="btn btn-outline-danger btn-sm ms-lg-2"
                @click="logout"
              >
                Logout
              </button>
            </template>
            <template v-else>
              <button
                class="btn btn-outline-secondary btn-sm"
                @click="go('login')"
              >
                Login
              </button>
              <button class="btn btn-secondary btn-sm" @click="go('register')">
                Register
              </button>
            </template>
          </div>
        </div>
      </div>
    </nav>

    <main class="container-xxl px-3 px-lg-4 py-4 py-lg-5 mt-4 mb-4 rounded-4 shadow-sm" :class="roleShellClass">
      <div
        v-if="alert.message"
        class="d-inline-block"
        role="status"
        aria-live="polite"
      >
        <div
          class="alert alert-dismissible shadow-sm py-2 px-3 mb-4"
          :class="'alert-' + alert.type"
        >
          <div class="pe-4">{{ alert.message }}</div>
          <div class="progress mt-2" style="height: 3px;">
            <div
              class="progress-bar"
              :class="'bg-' + alert.type"
              role="progressbar"
              :style="{ width: alert.progress + '%' }"
            ></div>
          </div>
          <button
            class="btn-close"
            @click="dismissAlert"
            aria-label="Close"
          ></button>
        </div>
      </div>
      <div
        v-if="loading"
        class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center bg-white bg-opacity-75 z-3"
      >
        <div class="spinner-border text-primary" aria-label="Loading"></div>
      </div>

    ${window.HomeView}
    ${window.AnalyticsView}
    ${window.LoginView}
    ${window.RegisterView}
    ${window.DashboardView}
    ${window.AdminCompaniesView}
    ${window.AdminStudentsView}
    ${window.AdminDrivesView}
    ${window.AdminApplicationsView}
    ${window.CompanyDrivesView}
    ${window.CompanyApplicationsView}
    ${window.StudentDrivesView}
    ${window.StudentApplicationsView}
    ${window.ProfileView}
    </main>
  </div>
`;

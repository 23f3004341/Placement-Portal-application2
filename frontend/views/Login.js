window.LoginView = `
      <section v-else-if="page === 'login'" class="row justify-content-center align-items-center g-4">
        <div class="col-lg-5 d-none d-lg-block">
          <span class="badge rounded-pill text-bg-primary mb-3">Welcome back</span>
          <h1 class="display-6 fw-bold">Your placement journey continues here.</h1>
          <p class="lead text-secondary">Access opportunities, applications, interviews, and placement updates from one dashboard.</p>
        </div>
        <div class="col-md-7 col-lg-5">
          <form class="card shadow-sm border-0" @submit.prevent="login">
            <div class="card-body p-4">
              <h1 class="h3 mb-1">Sign in</h1>
              <p class="text-secondary mb-4">Choose your role and enter your account details.</p>
              <label class="form-label">Role</label
              ><select
                class="form-select mb-3"
                v-model="loginForm.role"
                required
              >
                <option value="student">Student</option>
                <option value="company">Company</option>
                <option value="admin">Admin</option></select
              ><label class="form-label">Email</label
              ><input
                class="form-control mb-3"
                type="email"
                v-model.trim="loginForm.email"
                required
              /><label class="form-label">Password</label
              ><input
                class="form-control mb-3"
                type="password"
                minlength="6"
                v-model="loginForm.password"
                required
              /><button class="btn btn-primary btn-lg w-100">Sign in</button>
            </div>
          </form>
        </div>
      </section>
`;

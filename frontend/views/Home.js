window.HomeView = `
      <section v-if="page === 'home'">
        <div class="card border-0 shadow-sm bg-success-subtle mb-4">
          <div class="card-body p-4 p-lg-5">
            <div class="row align-items-center g-4">
              <div class="col-lg-10">
                <span class="badge rounded-pill text-bg-light text-success-emphasis border mb-3">
                  Northbridge University Placement Cell
                </span>
                <h1 class="display-5 fw-bold mb-3">Northbridge University</h1>
                <p class="lead text-secondary mb-4">
                  A calm, organized space for students, companies, and the placement cell
                  to manage campus hiring.
                </p>
                <div class="d-flex flex-wrap gap-2">
                  <button class="btn btn-success btn-lg px-4" @click="go('login')">Login</button>
                  <button class="btn btn-outline-success btn-lg px-4" @click="go('register')">Create account</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="row g-3">
          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body p-4">
                <h2 class="h5">Student access</h2>
                <p class="text-secondary mb-0">
                  Apply for approved roles and keep track of your application history.
                </p>
              </div>
            </div>
          </div>
          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body p-4">
                <h2 class="h5">Company access</h2>
                <p class="text-secondary mb-0">
                  Submit job positions and manage applicants after approval.
                </p>
              </div>
            </div>
          </div>
          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body p-4">
                <h2 class="h5">Admin access</h2>
                <p class="text-secondary mb-0">
                  Review records, approvals, reminders, and placement summaries.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
`;

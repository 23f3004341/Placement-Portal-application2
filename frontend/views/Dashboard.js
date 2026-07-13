window.DashboardView = `
      <section v-else-if="page === 'dashboard'">
        <div
          class="card border-0 shadow-sm mb-4"
          :class="{
            'bg-primary-subtle': user && user.role === 'student',
            'bg-warning-subtle': user && user.role === 'company',
            'bg-info-subtle': user && user.role === 'admin'
          }"
        >
          <div class="card-body p-4 p-lg-5">
            <div class="d-flex flex-wrap justify-content-between align-items-center gap-3">
              <div>
                <div class="small fw-semibold text-uppercase mb-1" :class="themeTextClass">Overview</div>
                <h1 class="display-6 fw-bold mb-2">{{ roleTitle }} Dashboard</h1>
                <p class="lead text-secondary mb-0" v-if="user && user.role === 'student'">
                  Your applications, interviews, exports, and placement records.
                </p>
                <p class="lead text-secondary mb-0" v-else-if="user && user.role === 'company'">
                  Your drives, applicants, interviews, and final results.
                </p>
                <p class="lead text-secondary mb-0" v-else>
                  A clean overview of campus placement activity.
                </p>
              </div>
              <div class="text-end">
                <div class="small text-secondary">Signed in as</div>
                <div class="h5 mb-0">{{ user?.name }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="row g-3 mb-4">
          <div
            v-for="(value, key) in dashboard.metrics"
            :key="key"
            class="col-6 col-lg-4 col-xl-2"
          >
            <div class="card border-0 shadow-sm h-100 border-start border-4" :class="themeBorderClass">
              <div class="card-body">
                <div class="small text-secondary text-uppercase text-capitalize">
                  {{ key.replaceAll("_", " ") }}
                </div>
                <div class="display-6 fw-bold">{{ value }}</div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="user && user.role === 'student'" class="row g-4">
          <div class="col-lg-7">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h2 class="h5">Welcome, {{ dashboard.student?.user.name }}</h2>
                <p class="text-secondary">
                  Start with Find Jobs to discover eligible roles by company or position.
                </p>
                <div v-if="dashboard.recent_applications?.length" class="table-responsive mt-4">
                  <table class="table table-sm align-middle mb-0">
                    <thead>
                      <tr>
                        <th>Company</th>
                        <th>Position</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in dashboard.recent_applications">
                        <td>{{ item.drive.company }}</td>
                        <td>{{ item.drive.title }}</td>
                        <td>
                          <span
                            v-if="item.feedback === 'Already placed at a different role'"
                            class="badge text-bg-secondary"
                          >Already placed at a different role</span
                          ><status-badge v-else :value="item.status"></status-badge>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
          <div class="col-lg-5">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h2 class="h5">Reports and exports</h2>
                <export-panel :value="dashboard.latest_export" :button-class="themeOutlineButtonClass" @start="startExport"></export-panel>
                <div class="d-grid gap-2 mt-3">
                  <a class="btn" :class="themeOutlineButtonClass" href="/api/student/report?format=html" download>Download HTML report</a>
                  <a class="btn" :class="themeOutlineButtonClass" href="/api/student/report?format=pdf" download>Download PDF report</a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="user && user.role === 'company'" class="row g-4">
          <div class="col-lg-7">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h2 class="h5">{{ dashboard.company?.name }}</h2>
                <p class="text-secondary">
                  Keep your drives updated, review applicants, schedule interviews, and record final decisions.
                </p>
                <div class="row g-3 mt-2">
                  <div class="col-sm-6">
                    <div class="p-3 rounded bg-warning-subtle border">
                      <div class="small text-secondary">Applicants</div>
                      <div class="fw-semibold">Review and update statuses</div>
                    </div>
                  </div>
                  <div class="col-sm-6">
                    <div class="p-3 rounded bg-light border">
                      <div class="small text-secondary">Drives</div>
                      <div class="fw-semibold">Post or edit open roles</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-lg-5">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h2 class="h5">Quick actions</h2>
                <div class="d-grid gap-2">
                  <button class="btn" :class="themeButtonClass" @click="go('company-drives')">Manage job positions</button>
                  <button class="btn" :class="themeOutlineButtonClass" @click="go('company-applications')">Review applicants</button>
                  <button class="btn btn-outline-secondary" @click="go('profile')">Update company profile</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="user && user.role === 'admin'" class="row g-4">
          <div class="col-lg-8">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h2 class="h5 mb-1">Placement summary</h2>
                <p class="text-secondary mb-3">
                  Applications, drives, companies, and major application outcomes.
                </p>
                <img
                  class="img-fluid rounded border bg-white"
                  :src="'/api/admin/dashboard/summary-chart.png?v=' + dashboardChartVersion"
                  alt="Admin placement summary chart"
                />
              </div>
            </div>
          </div>
          <div class="col-lg-4">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h2 class="h5 mb-3">Admin shortcuts</h2>
                <div class="d-grid gap-2">
                  <button class="btn" :class="themeButtonClass" @click="go('admin-companies')">Companies</button>
                  <button class="btn" :class="themeOutlineButtonClass" @click="go('admin-drives')">Drives</button>
                  <button class="btn" :class="themeOutlineButtonClass" @click="go('admin-applications')">Applications</button>
                  <button class="btn btn-outline-secondary" @click="go('admin-students')">Students</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
`;

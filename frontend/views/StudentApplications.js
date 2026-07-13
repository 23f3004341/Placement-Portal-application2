window.StudentApplicationsView = `
      <section v-else-if="page === 'student-applications'">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h1 class="h3 mb-0">Applications & Placement History</h1>
          <button class="btn" :class="themeOutlineButtonClass" @click="startExport">
            Export CSV
          </button>
        </div>
        <div class="row g-3">
          <div v-if="!applications.length" class="col-12"><div class="card border-0 shadow-sm"><div class="card-body text-center text-secondary py-5"><h2 class="h5 text-body">No applications yet</h2><p class="mb-3">Explore approved positions and submit your first application.</p><button class="btn" :class="themeButtonClass" @click="go('student-drives')">Find jobs</button></div></div></div>
          <div v-for="a in applications" :key="a.id" class="col-12">
            <div class="card border-0 shadow-sm">
              <div class="card-body">
                <div class="row g-3">
                  <div class="col-lg-3">
                    <h2 class="h5">{{ a.drive.title }}</h2>
                    <div>{{ a.drive.company }}</div>
                    <div>Applied {{ formatDate(a.applied_at) }}</div>
                  </div>
                  <div class="col-lg-3">
                    <span
                      v-if="a.feedback === 'Already placed at a different role'"
                      class="badge text-bg-secondary"
                    >
                      Already placed at a different role</span
                    ><status-badge v-else :value="a.status"></status-badge>
                    <p class="mt-2 mb-0">
                      <strong>Feedback:</strong> {{ a.feedback || "-" }}
                    </p>
                    <button
                      v-if="a.status === 'applied'"
                      class="btn btn-outline-danger btn-sm mt-2"
                      @click="withdrawApplication(a)"
                    >
                      Withdraw
                    </button>
                  </div>
                  <div class="col-lg-3">
                    <h3 class="h6">Interviews</h3>
                    <div v-if="a.interviews.length">
                      <div
                        v-if="['placed', 'rejected'].includes(a.status)"
                        class="alert p-3 mb-0"
                        :class="a.status === 'placed' ? 'alert-success' : 'alert-danger'"
                      >
                        <div class="fw-semibold mb-2">Results Out</div>
                        <span
                          class="badge fs-6"
                          :class="a.status === 'placed' ? 'text-bg-success' : 'text-bg-danger'"
                        >
                          {{ a.status === 'placed' ? 'Placed' : 'Rejected' }}
                        </span>
                      </div>
                      <div v-else class="alert alert-info p-3 mb-0">
                        <div class="fw-semibold mb-2">Interview scheduled</div>
                        <div>
                          <span class="fw-semibold">Time:</span>
                          {{ formatDate(a.interviews[0].scheduled_at) }}
                        </div>
                        <div>
                          <span class="fw-semibold">Location:</span>
                          {{ a.interviews[0].location_or_link || "Not specified" }}
                        </div>
                        <div class="mt-3">
                          <span class="badge fs-6 text-bg-warning">Result pending</span>
                        </div>
                      </div>
                    </div>
                    <span v-if="!a.interviews.length" class="text-secondary"
                      >None scheduled</span
                    >
                  </div>
                  <div class="col-lg-3">
                    <h3 class="h6">Placement</h3>
                    <template v-if="a.placement"
                      ><div class="mb-2">
                        <span class="fw-semibold">Package:</span>
                        {{ moneyLabel(a.placement.package, a.placement.package_unit || a.drive.salary_unit) }}
                      </div>
                      <a
                        class="btn btn-success btn-sm mt-2"
                        :href="a.placement.offer_letter_url"
                        >Download letter</a
                      ></template
                    ><span v-else class="text-secondary">Not available</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
`;

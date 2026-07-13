window.AdminDrivesView = `
      <section v-else-if="page === 'admin-drives'">
        <list-header
          title="Placement Drives"
          placeholder="Search company, position, or skill"
          v-model="search"
          :button-class="themeButtonClass"
          :eyebrow-class="themeTextClass"
          @search="loadAdminDrives"
        ></list-header
        ><div
          v-if="selectedAdminDrive"
          class="card border-0 shadow-sm mb-4"
        >
          <div class="card-body p-4">
            <div
              class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4"
            >
              <div>
                <p class="fw-semibold text-uppercase small mb-1" :class="themeTextClass">
                  Drive approval review
                </p>
                <h2 class="h4 mb-1">{{ selectedAdminDrive.title }}</h2>
                <div class="d-flex flex-wrap gap-2">
                  <span class="badge text-bg-light border">
                    {{ selectedAdminDrive.company }}
                  </span>
                  <status-badge :value="selectedAdminDrive.status"></status-badge>
                  <status-badge
                    :value="selectedAdminDrive.active ? 'active' : 'inactive'"
                  ></status-badge>
                </div>
              </div>
              <button
                class="btn btn-outline-secondary btn-sm"
                @click="selectedAdminDrive = null"
              >
                Back to list
              </button>
            </div>

            <div class="row g-4">
              <div class="col-lg-6">
                <h3 class="h6 text-secondary text-uppercase">Job details</h3>
                <dl class="row mb-0">
                  <dt class="col-sm-4">Company</dt>
                  <dd class="col-sm-8">{{ selectedAdminDrive.company }}</dd>
                  <dt class="col-sm-4">Type</dt>
                  <dd class="col-sm-8">{{ selectedAdminDrive.job_type || "-" }}</dd>
                  <dt class="col-sm-4">Deadline</dt>
                  <dd class="col-sm-8">{{ selectedAdminDrive.deadline || "-" }}</dd>
                  <dt class="col-sm-4">Location</dt>
                  <dd class="col-sm-8">{{ selectedAdminDrive.location || "-" }}</dd>
                  <dt class="col-sm-4">Package</dt>
                  <dd class="col-sm-8">
                    {{ moneyLabel(selectedAdminDrive.salary, selectedAdminDrive.salary_unit) }}
                  </dd>
                  <dt class="col-sm-4">Openings</dt>
                  <dd class="col-sm-8">{{ selectedAdminDrive.openings || "-" }}</dd>
                </dl>
              </div>
              <div class="col-lg-6">
                <h3 class="h6 text-secondary text-uppercase">Eligibility</h3>
                <dl class="row mb-0">
                  <dt class="col-sm-4">Minimum CGPA</dt>
                  <dd class="col-sm-8">
                    {{
                      selectedAdminDrive.min_cgpa !== null &&
                      selectedAdminDrive.min_cgpa !== undefined
                        ? selectedAdminDrive.min_cgpa
                        : "Not specified"
                    }}
                  </dd>
                  <dt class="col-sm-4">Degrees</dt>
                  <dd class="col-sm-8">
                    {{ selectedAdminDrive.eligible_degrees || "All eligible degrees" }}
                  </dd>
                  <dt class="col-sm-4">Branches</dt>
                  <dd class="col-sm-8">
                    {{ selectedAdminDrive.eligible_branches || "All eligible branches" }}
                  </dd>
                  <dt class="col-sm-4">Years</dt>
                  <dd class="col-sm-8">
                    {{ selectedAdminDrive.eligible_years || "All eligible years" }}
                  </dd>
                  <dt class="col-sm-4">Skills</dt>
                  <dd class="col-sm-8">
                    {{ selectedAdminDrive.skills_required || "-" }}
                  </dd>
                  <dt class="col-sm-4">Experience</dt>
                  <dd class="col-sm-8">
                    {{ selectedAdminDrive.experience_required || "-" }}
                  </dd>
                </dl>
              </div>
              <div class="col-lg-6">
                <h3 class="h6 text-secondary text-uppercase">Description</h3>
                <p class="mb-0 text-break">
                  {{ selectedAdminDrive.description || "-" }}
                </p>
              </div>
            </div>

            <div class="d-flex flex-wrap gap-2 mt-4 pt-3 border-top">
              <button
                v-if="selectedAdminDrive.status !== 'approved'"
                class="btn btn-success"
                @click="adminDriveAction(selectedAdminDrive, 'approve')"
              >
                Approve drive
              </button>
              <button
                v-if="selectedAdminDrive.status === 'pending'"
                class="btn btn-outline-danger"
                @click="adminDriveAction(selectedAdminDrive, 'reject')"
              >
                Reject drive
              </button>
              <button
                v-if="selectedAdminDrive.status === 'approved'"
                class="btn btn-outline-danger"
                @click="adminDriveAction(selectedAdminDrive, 'close')"
              >
                Close drive
              </button>
            </div>
          </div>
        </div
        ><drive-table
          :drives="drives"
          admin
          :action-class="themeOutlineButtonClass"
          @view="viewAdminDrive"
          @action="adminDriveAction"
        ></drive-table>
      </section>
`;

window.CompanyDrivesView = `
      <section v-else-if="page === 'company-drives'">
        <div
          class="d-flex flex-wrap justify-content-between align-items-center mb-3"
        >
          <h1 class="h3 mb-0">Job Positions</h1>
          <button
            class="btn"
            :class="themeButtonClass"
            @click="showDriveForm = !showDriveForm"
          >
            {{ showDriveForm ? "Close form" : "Post new job" }}
          </button>
        </div>
        <form
          v-if="showDriveForm"
          class="card border-0 shadow-sm mb-4"
          @submit.prevent="saveDrive"
        >
          <div class="card-body">
            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label"
                  >Title <span class="text-danger">*</span></label
                ><input
                  class="form-control"
                  v-model.trim="driveForm.title"
                  required
                />
              </div>
              <div class="col-md-3">
                <label class="form-label"
                  >Type <span class="text-danger">*</span></label
                ><select class="form-select" v-model="driveForm.job_type" required>
                  <option value="full-time">Full-time</option>
                  <option value="internship">Internship</option>
                  <option value="contract">Contract</option>
                </select>
              </div>
              <div class="col-md-3">
                <label class="form-label"
                  >Deadline <span class="text-danger">*</span></label
                ><input
                  class="form-control"
                  type="date"
                  :min="today"
                  v-model="driveForm.deadline"
                  required
                />
              </div>
              <div class="col-md-4">
                <label class="form-label"
                  >Location <span class="text-danger">*</span></label
                ><input
                  class="form-control"
                  v-model.trim="driveForm.location"
                  required
                />
              </div>
              <div class="col-md-2">
                <label class="form-label"
                  >Salary <span class="text-danger">*</span></label
                ><input
                  class="form-control"
                  type="number"
                  min="0"
                  step="0.01"
                  v-model="driveForm.salary"
                  required
                />
              </div>
              <div class="col-md-2">
                <label class="form-label"
                  >Openings <span class="text-danger">*</span></label
                ><input
                  class="form-control"
                  type="number"
                  min="1"
                  v-model="driveForm.openings"
                  required
                />
              </div>
              <div class="col-md-2">
                <label class="form-label"
                  >Minimum CGPA <span class="text-danger">*</span></label
                ><input
                  class="form-control"
                  type="number"
                  min="0"
                  max="10"
                  step="0.01"
                  v-model="driveForm.min_cgpa"
                  required
                />
              </div>
              <div class="col-md-2">
                <label class="form-label"
                  >Unit <span class="text-danger">*</span></label
                ><select class="form-select" v-model="driveForm.salary_unit" required>
                  <option value="lpa">LPA</option>
                  <option value="k_month">K/month</option>
                </select>
              </div>
              <div class="col-md-4">
                <label class="form-label"
                  >Eligible degrees <span class="text-danger">*</span></label
                ><select
                  class="form-select"
                  multiple
                  size="7"
                  v-model="driveForm.eligible_degrees_list"
                  required
                >
                  <option
                    v-for="degree in degreeOptions"
                    :key="degree"
                    :value="degree"
                  >
                    {{ degree }}
                  </option></select
                ><small class="text-secondary"
                  >Hold Cmd/Ctrl to select more than one.</small
                >
              </div>
              <div class="col-md-4">
                <label class="form-label"
                  >Eligible branches <span class="text-danger">*</span></label
                ><select
                  class="form-select"
                  multiple
                  size="7"
                  v-model="driveForm.eligible_branches_list"
                  required
                >
                  <option
                    v-for="branch in branchOptions"
                    :key="branch"
                    :value="branch"
                  >
                    {{ branch }}
                  </option></select
                ><small class="text-secondary">Hold Cmd/Ctrl to select more than one.</small>
              </div>
              <div class="col-md-4">
                <label class="form-label"
                  >Eligible graduation years <span class="text-danger">*</span></label
                ><input
                  class="form-control"
                  v-model.trim="driveForm.eligible_years"
                  placeholder="2026, 2027"
                  required
                /><small class="text-secondary">Comma-separated years.</small>
              </div>
              <div class="col-md-6">
                <label class="form-label">Required skills</label
                ><input
                  class="form-control"
                  v-model.trim="driveForm.skills_required"
                  placeholder="Python, SQL, Vue"
                />
              </div>
              <div class="col-md-6">
                <label class="form-label">Experience required</label
                ><input
                  class="form-control"
                  v-model.trim="driveForm.experience_required"
                  placeholder="0-2 years"
                />
              </div>
              <div class="col-12">
                <label class="form-label"
                  >Job description <span class="text-danger">*</span></label
                ><textarea
                  class="form-control"
                  v-model.trim="driveForm.description"
                  required
                ></textarea>
              </div>
              <div class="col-12">
                <button class="btn" :class="themeButtonClass">
                  {{
                    driveForm.id ? "Update and resubmit" : "Submit for approval"
                  }}
                </button>
              </div>
            </div>
          </div>
        </form>
        <drive-table
          v-if="!showDriveForm"
          :drives="drives"
          company
          :action-class="themeOutlineButtonClass"
          @edit="editDrive"
          @action="companyDriveAction"
        ></drive-table>
      </section>
`;

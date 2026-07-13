window.StudentDrivesView = `
      <section v-else-if="page === 'student-drives'">
        <list-header
          title="Approved Job Positions"
          placeholder="Search company or position"
          v-model="search"
          :button-class="themeButtonClass"
          :eyebrow-class="themeTextClass"
          @search="loadStudentDrives"
        ></list-header>
        <div class="form-check form-switch mb-3">
          <input
            id="eligibleOnly"
            class="form-check-input"
            type="checkbox"
            v-model="eligibleOnly"
            @change="loadStudentDrives"
          /><label class="form-check-label" for="eligibleOnly"
            >Show only jobs I am eligible for</label
          >
        </div>
        <div class="row g-3">
          <div v-if="!drives.length" class="col-12"><div class="card border-0 shadow-sm"><div class="card-body text-center text-secondary py-5"><h2 class="h5 text-body">No matching jobs</h2><p class="mb-0">Try changing your search or eligibility filter.</p></div></div></div>
          <div v-for="d in drives" :key="d.id" class="col-12 col-xl-6">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <div class="d-flex flex-wrap justify-content-between align-items-start gap-2">
                  <div class="me-3">
                    <h2 class="h5 mb-1">{{ d.title }}</h2>
                    <div class="text-secondary">
                      {{ d.company }} · {{ d.location || "Location TBA" }}
                    </div>
                  </div>
                  <span
                    class="badge rounded-pill px-3 py-2"
                    :class="d.eligible ? 'text-bg-success' : 'text-bg-light text-secondary border'"
                    >{{ d.eligible ? "Eligible" : "Not Eligible" }}</span
                  >
                </div>
                <p class="mt-3 mb-2">{{ d.description }}</p>
                <div>
                  <strong>Experience:</strong>
                  {{ d.experience_required || "-" }}
                </div>
                <div><strong>Deadline:</strong> {{ d.deadline }}</div>
                <div
                  v-if="!d.eligible"
                  class="alert alert-warning py-2 px-3 mt-3 mb-0"
                >
                  <span class="fw-semibold">Eligibility gap:</span>
                  {{ d.eligibility_reasons.map(titleCase).join(", ") }}
                </div>
                <button
                  class="btn mt-3"
                  :class="themeButtonClass"
                  :disabled="!d.eligible || !!d.application_status"
                  @click="applyDrive(d)"
                >
                  {{
                    d.application_status
                      ? "Status: " + titleCase(d.application_status)
                      : "Apply"
                  }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
`;

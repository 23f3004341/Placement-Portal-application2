window.CompanyApplicationsView = `
      <section v-else-if="page === 'company-applications'">
        <h1 class="h3 mb-3">Applicants</h1>
        <div class="table-responsive card border-0 shadow-sm rounded-4 overflow-hidden">
          <table class="table table-hover align-middle mb-0">
            <thead><tr><th>Student</th><th>Position & status</th><th>Decision & feedback</th><th>Interview</th></tr></thead>
            <tbody>
              <tr v-if="!applications.length"><td colspan="4" class="text-center text-secondary py-5"><h2 class="h5 text-body">No applicants yet</h2><p class="mb-0">Applications will appear here when students apply to your positions.</p></td></tr>
              <tr v-for="a in applications" :key="a.id">
                  <td>
                    <h2 class="h5">{{ a.student.user.name }}</h2>
                    <div>Student ID: {{ a.student.roll_number }}</div>
                    <div>
                      {{ a.student.course }} · {{ a.student.cgpa ?? "-" }} CGPA
                    </div>
                    <a
                      v-if="a.student.resume_url"
                      :href="a.student.resume_url"
                      target="_blank"
                      >View resume</a
                    >
                  </td>
                  <td>
                    <strong>{{ a.drive.title }}</strong
                    ><br /><span
                      v-if="a.already_placed_elsewhere"
                      class="badge text-bg-secondary"
                    >
                      Already placed at a different role</span
                    ><status-badge
                      v-else
                      :value="a.status"
                    ></status-badge>
                    <p class="small mt-2 mb-0">
                      Feedback: {{ a.feedback || "-" }}
                    </p>
                  </td>
                  <td>
                    <div
                      v-if="a.already_placed_elsewhere"
                      class="alert alert-secondary py-2 px-3 mb-0"
                    >
                      Already placed at a different role.
                    </div>
                    <template v-else>
                    <label class="form-label">Status and feedback</label
                    ><select
                      class="form-select form-select-sm mb-2"
                      v-model="a.nextStatus"
                    >
                      <option
                        v-if="a.interviews.length && a.status === 'interview'"
                        value="interview"
                        disabled
                      >
                        Interview scheduled
                      </option>
                      <option v-if="!a.interviews.length" value="shortlisted">
                        Shortlisted
                      </option>
                      <option value="rejected">Rejected</option>
                      <option value="placed">Placed</option></select
                    ><textarea
                      class="form-control form-control-sm mb-2"
                      v-model="a.nextFeedback"
                      placeholder="Feedback to student"
                    ></textarea
                    ><button
                      class="btn btn-sm"
                      :class="themeButtonClass"
                      :disabled="a.nextStatus === 'interview'"
                      @click="updateApplication(a)"
                    >
                      Update
                    </button>
                    </template>
                  </td>
                  <td>
                  <div v-if="!a.already_placed_elsewhere && (a.interviews.length || (!a.student_placed && a.status === 'shortlisted' && !(a.placement && a.placement.status === 'placed')))">
                    <template v-if="!a.interviews.length">
                      <label class="form-label">Schedule interview</label
                      ><input
                        class="form-control form-control-sm mb-2"
                        type="datetime-local"
                        v-model="a.interviewAt"
                      /><input
                        class="form-control form-control-sm mb-2"
                        v-model="a.interviewLocation"
                        placeholder="Link or location"
                      /><button
                        class="btn btn-outline-secondary btn-sm"
                        @click="scheduleInterview(a)"
                      >
                        Schedule
                      </button>
                    </template>
                    <div
                      v-else-if="['placed', 'rejected'].includes(a.status)"
                      class="alert alert-success p-3 mb-0"
                    >
                      <div class="fw-semibold mb-2">Results Out</div>
                      <div>
                        Final status:
                        <span class="badge fs-6 ms-1" :class="a.status === 'placed' ? 'text-bg-success' : 'text-bg-danger'">
                          {{ a.status === 'placed' ? 'Placed' : 'Rejected' }}
                        </span>
                      </div>
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
                  </div><span v-else class="text-secondary">—</span>
                  </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
`;
